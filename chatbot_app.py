from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from chatbot.chatbot import agent_app
import html
import re
import uuid
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import os

import resend


def get_real_ip(request: Request):
    # Railway passes the real user IP in this header
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()  # Get the first IP in the list
    return request.client.host


limiter = Limiter(key_func=get_real_ip)
app = FastAPI(title="Windows Chatbot Backend")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["https://direct-windows-quote.myshopify.com", "https://window-chatbot-production.up.railway.app"], 
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_AUTH_KEY = os.getenv("CHAT_CUSTOM_HEADER_KEY")

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

@app.post("/chat")
@limiter.limit("5/minute; 100/day")
async def chat_endpoint(request: Request, chat_request: ChatRequest):

    auth = request.headers.get("Authorization")
    client_key = (auth.split(maxsplit=1)[1].strip() if auth and auth.startswith("Bearer ") else None) or None
    expected = (API_AUTH_KEY or "").strip() or None
    if client_key != expected:
        return PlainTextResponse("Invalid API key", status_code=403)  

    thread_id = chat_request.thread_id or str(uuid.uuid4())
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run the graph
    input_message = {"messages": [("user", chat_request.message)]}
    result = agent_app.invoke(input_message, config=config)
    
    # Get the last message from the assistant
    assistant_msg = result["messages"][-1].content

    return {
        "response": assistant_msg,
        "thread_id": thread_id,
    }

class CallbackRequest(BaseModel):
    phone: str
    name: Optional[str] = None
    thread_id: Optional[str] = None
    page: Optional[str] = None


@app.post("/callback-request")
@limiter.limit("3/minute; 10/day")
async def callback_request(request: Request, cb: CallbackRequest):
    """'Talk to a human' button: email the business a callback request.
    Alert goes to LEAD_BCC_EMAIL (same var as estimate BCCs), else david@."""
    auth = request.headers.get("Authorization")
    client_key = (auth.split(maxsplit=1)[1].strip() if auth and auth.startswith("Bearer ") else None) or None
    expected = (API_AUTH_KEY or "").strip() or None
    if client_key != expected:
        return PlainTextResponse("Invalid API key", status_code=403)

    digits = re.sub(r"\D", "", cb.phone or "")
    if not (10 <= len(digits) <= 15):
        return PlainTextResponse("Please provide a valid phone number.", status_code=400)

    resend.api_key = (os.getenv("RESEND_API_KEY") or "").strip() or None
    if not resend.api_key:
        return PlainTextResponse("Callback service is not configured.", status_code=503)

    name = html.escape((cb.name or "").strip()[:100])
    phone = html.escape((cb.phone or "").strip()[:40])
    page = html.escape((cb.page or "").strip()[:200])
    thread = html.escape((cb.thread_id or "").strip()[:60])

    body = f'<p style="font-size:16px;margin:0 0 12px;"><strong>Phone:</strong> <a href="tel:{digits}">{phone}</a></p>'
    if name:
        body += f'<p style="margin:0 0 12px;"><strong>Name:</strong> {name}</p>'
    if page:
        body += f'<p style="margin:0 0 12px;"><strong>Page:</strong> {page}</p>'
    if thread:
        body += f'<p style="margin:0 0 12px;color:#667085;">Chat thread: {thread}</p>'
    body += '<p style="margin:16px 0 0;color:#667085;">Sent by the "talk to a human" button on estimate.directwindows.ca.</p>'

    subject = f"\U0001F4DE Callback request — {phone}" + (f" ({name})" if name else "")
    try:
        resend.Emails.send({
            "from": "Direct Windows <hello@quote.directwindows.ca>",
            "to": (os.getenv("LEAD_BCC_EMAIL") or "david@directwindows.ca").strip(),
            "subject": subject,
            "html": body,
        })
    except Exception as e:
        print(f"[callback-request] Failed to send alert email: {e}")
        return PlainTextResponse("Could not send your request. Please call us directly.", status_code=502)

    return {"ok": True}


class EstimateRequest(BaseModel):
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    postal: Optional[str] = None
    home_type: Optional[str] = None
    page: Optional[str] = None
    selections: dict


@app.post("/estimate-request")
@limiter.limit("3/minute; 10/day")
async def estimate_request(request: Request, er: EstimateRequest):
    """Step-form estimator (estimate.directwindows.ca/quote/): price the form
    selections through the engine, email the customer the written estimate
    (PDF attached, business BCC'd), and alert the business with the contact
    details. Selections use the same mapping as the site's client-side price
    table (see form_estimate.py), so the email matches the on-screen range."""
    auth = request.headers.get("Authorization")
    client_key = (auth.split(maxsplit=1)[1].strip() if auth and auth.startswith("Bearer ") else None) or None
    expected = (API_AUTH_KEY or "").strip() or None
    if client_key != expected:
        return PlainTextResponse("Invalid API key", status_code=403)

    email = (er.email or "").strip()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return PlainTextResponse("Please provide a valid email address.", status_code=400)

    from form_estimate import build_form_estimate
    try:
        display_dict, pdf_config, quote_html = build_form_estimate(er.selections or {})
    except (ValueError, KeyError, TypeError) as e:
        print(f"[estimate-request] Bad selections: {e}")
        return PlainTextResponse("Invalid selections.", status_code=400)

    from quote_emailer.quote_emailer import QuoteEmailer
    from quote_emailer.pdf_estimate import render_estimate_pdf

    quote_id = uuid.uuid4().hex[:8].upper()
    pdf_bytes = None
    try:
        pdf_bytes = render_estimate_pdf(display_dict=display_dict, config=pdf_config,
                                        quote_id=quote_id, email=email)
    except Exception as e:
        print(f"[estimate-request] PDF render failed (sending without): {e}")

    try:
        QuoteEmailer(email).send_quote(quote_html, quote_id=quote_id,
                                       installation_required=True,
                                       pdf_attachment=pdf_bytes)
    except Exception as e:
        print(f"[estimate-request] Estimate email failed: {e}")
        return PlainTextResponse("Could not send your estimate. Please try the chat or call us.",
                                 status_code=502)

    # Business alert with contact details the estimate BCC doesn't carry.
    try:
        name = html.escape((er.name or "").strip()[:100])
        phone = html.escape((er.phone or "").strip()[:40])
        postal = html.escape((er.postal or "").strip()[:12])
        home_type = html.escape((er.home_type or "").strip()[:30])
        sel = html.escape(str(er.selections)[:500])
        total_min = display_dict.get("total_min_adjusted", 0)
        total_max = display_dict.get("total_max_adjusted", 0)
        body = f'<p style="font-size:16px;margin:0 0 12px;"><strong>Email:</strong> {html.escape(email)}</p>'
        if name:
            body += f'<p style="margin:0 0 12px;"><strong>Name:</strong> {name}</p>'
        if phone:
            digits = re.sub(r"\D", "", phone)
            body += f'<p style="margin:0 0 12px;"><strong>Phone:</strong> <a href="tel:{digits}">{phone}</a></p>'
        body += f'<p style="margin:0 0 12px;"><strong>Range shown:</strong> ${total_min:,} - ${total_max:,} (quote {quote_id})</p>'
        if postal or home_type:
            body += f'<p style="margin:0 0 12px;"><strong>Home:</strong> {home_type} {postal}</p>'
        body += f'<p style="margin:0 0 12px;color:#667085;">Selections: {sel}</p>'
        body += '<p style="margin:16px 0 0;color:#667085;">Sent by the step-form estimator on estimate.directwindows.ca.</p>'
        resend.api_key = (os.getenv("RESEND_API_KEY") or "").strip() or None
        resend.Emails.send({
            "from": "Direct Windows <hello@quote.directwindows.ca>",
            "to": (os.getenv("LEAD_BCC_EMAIL") or "david@directwindows.ca").strip(),
            "subject": f"\U0001F4CB Form estimate lead — {email}" + (f" ({name})" if name else ""),
            "html": body,
        })
    except Exception as e:
        print(f"[estimate-request] Lead alert email failed (estimate already sent): {e}")

    return {"ok": True, "quote_id": quote_id,
            "total_min": display_dict.get("total_min_adjusted", 0),
            "total_max": display_dict.get("total_max_adjusted", 0)}


@app.get("/health/pdf")
@limiter.limit("5/minute")
async def pdf_health(request: Request):
    """Diagnostic: can this container render the estimate PDF? Auth required.
    Reports node availability, bundle presence, and a minimal render attempt."""
    auth = request.headers.get("Authorization")
    client_key = (auth.split(maxsplit=1)[1].strip() if auth and auth.startswith("Bearer ") else None) or None
    expected = (API_AUTH_KEY or "").strip() or None
    if client_key != expected:
        return PlainTextResponse("Invalid API key", status_code=403)

    import shutil, subprocess
    from quote_emailer import pdf_estimate

    node = shutil.which("node")
    node_version = None
    if node:
        try:
            node_version = subprocess.run([node, "--version"], capture_output=True, timeout=10).stdout.decode().strip()
        except Exception as e:
            node_version = f"error: {type(e).__name__}"
    script_exists = os.path.exists(pdf_estimate._RENDER_SCRIPT)

    sample_dd = {"multi_unit": False, "any_quant_gt_1": False, "installation_req": False,
                 "total_min_adjusted": 100, "total_max_adjusted": 120,
                 "breakdown": {"window_1": {"type": "Casement", "width": 30, "height": 30,
                     "interior": "White", "exterior": "White", "quantity": 1,
                     "unit_price_min_adjusted": 100, "unit_price_max_adjusted": 120,
                     "price_min_adjusted": 100, "price_max_adjusted": 120}}}
    sample_cfg = {"installation_required": False, "window_1": {"quantity": 1,
        "config": {"width": 30, "height": 30, "units": {"unit_1": {"unit_type": "casement", "window_area_frac": 1}}}}}
    render_err = None
    render_bytes = 0
    try:
        proc = subprocess.run([node or "node", pdf_estimate._RENDER_SCRIPT],
            input=__import__("json").dumps({"quote_id": "HEALTH", "email": "health@check",
                "date": "check", "display_dict": sample_dd, "config": sample_cfg}).encode(),
            capture_output=True, timeout=30)
        if proc.returncode == 0 and proc.stdout.startswith(b"%PDF"):
            render_bytes = len(proc.stdout)
        else:
            render_err = f"rc={proc.returncode} stderr={proc.stderr.decode('utf-8','replace')[:600]}"
    except Exception as e:
        render_err = f"{type(e).__name__}: {e}"

    return {"node": node, "node_version": node_version,
            "script_exists": script_exists, "script_path": pdf_estimate._RENDER_SCRIPT,
            "render_ok": render_bytes > 0, "render_bytes": render_bytes, "render_error": render_err}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)