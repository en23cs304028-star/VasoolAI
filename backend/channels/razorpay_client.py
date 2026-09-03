import razorpay
from backend.config import settings

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def generate_payment_link(amount: float, reference_id: str, description: str) -> str:
    """
    Generates a Razorpay payment link.
    amount: float (in INR, will be converted to paise)
    """
    if settings.RAZORPAY_KEY_ID == "rzp_test_xxx":
        print("Warning: Missing Razorpay Key ID. Returning fake link.")
        return f"https://example.com/pay/{reference_id}"

    try:
        data = {
            "amount": int(round(amount, 2) * 100),  # in paise
            "currency": "INR",
            "accept_partial": False,
            "description": description,
            "reference_id": str(reference_id),
            "reminder_enable": True
        }
        payment_link = client.payment_link.create(data)
        return payment_link['short_url']
    except Exception as e:
        print(f"Failed to create Razorpay link: {e}")
        return f"https://example.com/error/{reference_id}"
