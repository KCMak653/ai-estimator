import os
from typing import Any, Dict, Optional
from urllib.parse import quote

import resend

# When send_quote returns pixel_lead=True, the storefront should run Meta Pixel, e.g. fbq('track', META_PIXEL_LEAD_EVENT).
META_PIXEL_LEAD_EVENT = "Lead"
INTERNAL_QUOTE_COPY_EMAIL_ENV = "INTERNAL_QUOTE_COPY_EMAIL"

_EMAIL_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_template.html")
_EMAIL_TEMPLATE_INSTALLATION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_template_installation.html")
UNSUBSCRIBE_PAGE_URL = "https://direct-windows-quote.myshopify.com/pages/unsubscribe"


def _load_template(installation_required: bool = False) -> str:
    path = _EMAIL_TEMPLATE_INSTALLATION_PATH if installation_required else _EMAIL_TEMPLATE_PATH
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def quote_to_email_html(
    quote_html: str,
    user_email: str,
    quote_id: Optional[str] = None,
    installation_required: bool = False,
) -> str:
    """Wrap quote HTML body in the email template (header + body + footer). Body is inserted as-is."""
    unsubscribe_url = f"{UNSUBSCRIBE_PAGE_URL}?contact[email]={quote(user_email, safe='')}"
    template = _load_template(installation_required)
    return (
        template.replace("{{body}}", quote_html)
        .replace("{{unsubscribe_url}}", unsubscribe_url)
        .replace("{{quote_id}}", str(quote_id or ""))
    )


class QuoteEmailer:
    def __init__(self, email_address: str):
        self.email_address = email_address
        self.internal_copy_email = (os.getenv(INTERNAL_QUOTE_COPY_EMAIL_ENV) or "").strip()
        resend.api_key = os.getenv("RESEND_API_KEY")
        if not resend.api_key:
            print("[QuoteEmailer] WARNING: RESEND_API_KEY not set; emails will not send.")

    def send_quote(
        self,
        quote: str,
        quote_id: Optional[str] = None,
        debug: bool = False,
        installation_required: bool = False,
    ) -> Dict[str, Any]:
        """
        Send quote email. quote: HTML body (inserted into template as-is).
        quote_id: optional unique ref. If debug=True, write HTML to a file (no send).
        installation_required: use installation CTA template.

        Returns a dict. If pixel_lead is True, Resend delivered the email; the /chat client may fire fbq('track', Lead).
        """
        body = quote_to_email_html(
            quote,
            self.email_address,
            quote_id=quote_id,
            installation_required=installation_required,
        )
        subject = f"Your Quote {quote_id}" if quote_id else "Your Generated Quote"
        if debug:
            out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "quotes")
            os.makedirs(out_dir, exist_ok=True)
            path = os.path.join(out_dir, f"quote_email_{quote_id or 'debug'}.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)
            print(f"[QuoteEmailer] Debug: wrote HTML to {path} (no email sent)")
            return {
                "sent": False,
                "debug_saved": True,
                "path": path,
                "quote_id": quote_id,
                "pixel_lead": False,
                "meta_pixel_event": META_PIXEL_LEAD_EVENT,
            }
        if not resend.api_key:
            raise ValueError("Email service is not configured. Please try again later.")
        try:
            payload = {
                "from": "Direct Windows <hello@quote.directwindows.ca>",
                "to": self.email_address,
                "subject": subject,
                "html": body,
                "headers": {
                    "List-Unsubscribe": f"<https://direct-windows-quote.myshopify.com/pages/unsubscribe?contact[email]={self.email_address}>",
                    "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"
                }
            }
            # Optional internal duplicate of every quote email (set via env var).
            if self.internal_copy_email and self.internal_copy_email.lower() != self.email_address.lower():
                payload["bcc"] = [self.internal_copy_email]
            resend.Emails.send(payload)
            print(f"[QuoteEmailer] Email sent to {self.email_address} (ref: {quote_id})")
            return {
                "sent": True,
                "quote_id": quote_id,
                "pixel_lead": True,
                "meta_pixel_event": META_PIXEL_LEAD_EVENT,
                "internal_copy_email": self.internal_copy_email or None,
            }
        except Exception as e:
            print(f"[QuoteEmailer] Failed to send email: {e}")
            raise


if __name__ == "__main__":
    # Debug: write sample quote HTML to file
    sample_quote = """<p style="margin: 0 0 16px 0; font-size: 14px;"><strong>Window 1</strong></p>
<p style="margin: 4px 0;">Type: Casement</p>
<p style="margin: 4px 0;">Dimensions: 23"W x 45"H</p>
<p style="margin: 4px 0;">Quantity: 1</p>
<p style="margin: 4px 0;">Price: $250 - $295</p>
<p style="margin: 16px 0 0;"><strong>Total: $250 - $295 plus tax</strong></p>"""
    emailer = QuoteEmailer("dmagal@gmail.com")
    emailer.send_quote(sample_quote, debug=False)

    # resend.api_key = os.getenv("RESEND_API_KEY")
    # domain = resend.Domains.create({
    #     "name": "quote.directwindows.ca",
    # })
    # print(domain)
    # print(f"Domain ID: {domain['id']}")
    # print("Add these records to Namecheap:")
    # for record in domain['records']:
    #     print(f"Type: {record['type']} | Host: {record['name']} | Value: {record['value']}")
