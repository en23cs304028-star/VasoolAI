import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config import settings

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Sends an email using Mailtrap SMTP.
    """
    if settings.SMTP_USER == "xxx" or settings.SMTP_PASS == "xxx":
        print(f"Warning: Mailtrap credentials missing. Skipping email to {to_email}.")
        return True
        
    msg = MIMEMultipart()
    msg['From'] = "system@vasoolai.in"
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
