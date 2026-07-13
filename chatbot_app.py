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