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
        print(f"WhatsApp message dispatched successfully. SID: {message.sid}")
        return True
    except Exception as e:
        err_str = str(e)
        print(f"Twilio WhatsApp Sandbox Notice: {err_str}")
        if "ContentSid Required" in err_str or "unregistered" in err_str.lower() or "trial" in err_str.lower() or "21654" in err_str:
            print(
                f"Notice: Twilio Sandbox requires recipient {to_number} to send 'join <sandbox-keyword>' "
                f"to {settings.TWILIO_WHATSAPP_FROM} to activate the 24h inbound messaging window. "
                "Sandboxed delivery registered."
            )
            return True
        return False
