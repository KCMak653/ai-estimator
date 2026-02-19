import html
import os

import resend

_EMAIL_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_template.html")


def string_to_html(s: str) -> str:
    """Take a string and return HTML that displays it (preserves indentation and line breaks)."""
    escaped = html.escape(s)
    return f'<pre style="margin: 0; white-space: pre-wrap; font-family: inherit; font-size: 14px; line-height: 1.5;">{escaped}</pre>'


def _load_template() -> str:
    with open(_EMAIL_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def quote_to_email_html(quote: str) -> str:
    """Wrap quote string in the email template (header + body + footer)."""
    body = string_to_html(quote)
    template = _load_template()
    return template.replace("{{body}}", body)


class QuoteEmailer:
    def __init__(self, email_address: str):
        self.email_address = email_address
        resend.api_key = os.getenv("RESEND_API_KEY")

    def send_quote(self, quote: str, debug: bool = False):
        """Send quote email. quote: formatted string from format_quote(total, breakdown). If debug=True, write HTML to a file instead of sending."""
        body = quote_to_email_html(quote)
        if debug:
            out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "quotes")
            os.makedirs(out_dir, exist_ok=True)
            path = os.path.join(out_dir, "quote_email.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)
            print(f"Debug: wrote HTML to {path}")
            return
        try:
            resend.Emails.send({
                "from": "Quotes <onboarding@resend.dev>",
                "to": self.email_address,
                "subject": "Your Generated Quote",
                "html": body,
            })
            print("Success!")
        except Exception as e:
            print(f"Failed: {e}")


if __name__ == "__main__":
    # Debug: write sample quote HTML to file
    sample_quote = """Window 1
  Type: Casement
  Dimensions: 23"W x 45"H
  Interior: White
  Exterior: White
  Quantity: 1
  Total Price: $250 - $295

Total: $250 - $295
"""
    emailer = QuoteEmailer("test@example.com")
    emailer.send_quote(sample_quote, debug=True)

    # resend.api_key = os.getenv("RESEND_ADMIN_API_KEY")
    # domain = resend.Domains.create({
    #     "name": "quote.directwindows.ca",
    # })
    # print(domain)
    # print(f"Domain ID: {domain['id']}")
    # print("Add these records to Namecheap:")
    # for record in domain['records']:
    #     print(f"Type: {record['type']} | Host: {record['name']} | Value: {record['value']}")