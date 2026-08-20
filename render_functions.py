import resend
from flask import current_app

def send_reset_email(to, html):
    api_key = current_app.config.get("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not configured")

    if not to:
        raise ValueError("Recipient email is required")

    if not html or not html.strip():
        raise ValueError("Email HTML body cannot be empty")

    resend.api_key = api_key
    print(f"DEBUG html: {repr(html)}")
    params = {
        "from": "Devlogs+ <auth@email.devlogs.plus>",
        "to": [to],
        "subject": "Reset your Password",
        "html": html,
        "reply_to": "Devlogs+ <contact@devlogs.plus"
    }

    return resend.Emails.send(params)