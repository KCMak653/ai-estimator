import logging
import resend

import os

class QuoteEmailer:


    
    def __init__(self, email_address: str):
        self.email_address = email_address
        resend.api_key = os.getenv("RESEND_API_KEY")

    def send_quote(self, quote: str):
        try:
            resend.Emails.send({
                "from": "Quotes <onboarding@resend.dev>", # Use your verified domain here
                "to": 'k.makulowich@gmail.com',
                "subject": "Your Generated Quote",
                "html": f"<p>Here is your quote: <strong>{quote}</strong></p>"
            })
            print("Success!")
        except Exception as e:
            print(f"Failed: {e}")


if __name__ == "__main__":
    quote_emailer = QuoteEmailer("k.makulowich@gmail.com")
    quote_emailer.send_quote("Hello, world!")