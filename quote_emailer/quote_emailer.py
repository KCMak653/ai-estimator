import os
from typing import Optional
from urllib.parse import quote

import resend

_EMAIL_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_template.html")
_EMAIL_TEMPLATE_INSTALLATION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_template_installation.html")
# Unsubscribe is mailto-based: the old Shopify unsubscribe page is dead, and
# CASL requires a working mechanism. Templates link mailto directly.
UNSUBSCRIBE_PAGE_URL = "mailto:info@directwindows.ca?subject=Unsubscribe"


def _load_template(installation_required: bool = False) -> str:
    path = _EMAIL_TEMPLATE_INSTALLATION_PATH if installation_required else _EMAIL_TEMPLATE_PATH
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def quote_to_email_html(quote_html: str, user_email: str, installation_required: bool = False) -> str:
    """Wrap quote HTML body in the email template (header + body + footer). Body is inserted as-is."""
    unsubscribe_url = f"{UNSUBSCRIBE_PAGE_URL}?contact[email]={quote(user_email, safe='')}"
    template = _load_template(installation_required)
    return template.replace("{{body}}", quote_html).replace("{{unsubscribe_url}}", unsubscribe_url)


class QuoteEmailer:
    def __init__(self, email_address: str):
        self.email_address = email_address
        resend.api_key = (os.getenv("RESEND_API_KEY") or "").strip() or None
        if not resend.api_key:
            print("[QuoteEmailer] WARNING: RESEND_API_KEY not set; emails will not send.")

    def send_quote(self, quote: str, quote_id: Optional[str] = None, debug: bool = False, installation_required: bool = False, pdf_attachment: Optional[bytes] = None):
        """Send quote email. quote: HTML body (inserted into template as-is). quote_id: optional unique ref. If debug=True, write HTML to a file. installation_required: use installation CTA template. pdf_attachment: optional estimate PDF bytes to attach."""
        body = quote_to_email_html(quote, self.email_address, installation_required=installation_required)
        subject = f"Your Direct Windows estimate ({quote_id})" if quote_id else "Your Direct Windows estimate"
        if debug:
            out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "quotes")
            os.makedirs(out_dir, exist_ok=True)
            path = os.path.join(out_dir, f"quote_email_{quote_id or 'debug'}.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)
            print(f"[QuoteEmailer] Debug: wrote HTML to {path} (no email sent)")
            return
        if not resend.api_key:
            raise ValueError("Email service is not configured. Please try again later.")
        try:
            params = {
                "from": "Direct Windows <hello@quote.directwindows.ca>",
                "to": self.email_address,
                # Business copy of every estimate — lead visibility without a CRM.
                "bcc": (os.getenv("LEAD_BCC_EMAIL") or "david@directwindows.ca").strip(),
                "subject": subject,
                "html": body,
                "headers": {
                    "List-Unsubscribe": "<mailto:info@directwindows.ca?subject=Unsubscribe>"
                }
            }
            if pdf_attachment:
                import base64
                filename = f"Direct-Windows-Estimate-{quote_id}.pdf" if quote_id else "Direct-Windows-Estimate.pdf"
                params["attachments"] = [{
                    "filename": filename,
                    "content": base64.b64encode(pdf_attachment).decode("ascii"),
                }]
            resend.Emails.send(params)
            print(f"[QuoteEmailer] Email sent to {self.email_address} (ref: {quote_id})")
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