from twilio.rest import Client
from backend.config import settings

def send_whatsapp_message(to_number: str, message_body: str) -> bool:
    """
    Sends a WhatsApp message using Twilio Sandbox.
    to_number: e.g. "whatsapp:+1234567890"
    """
    if settings.TWILIO_ACCOUNT_SID == "xxx":
        print(f"Warning: Twilio Account SID missing. Skipping WhatsApp message to {to_number}.")
        return True
        
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Ensure to_number is in correct format
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"
            
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=to_number
        )
        return True
    except Exception as e:
        print(f"Failed to send WhatsApp message: {e}")
        return False
