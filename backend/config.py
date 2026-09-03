import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    NVIDIA_API_KEY: str = "nvapi-xxx"
    NVIDIA_DRAFT_MODEL: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    NVIDIA_EXTRACT_MODEL: str = "mistralai/mistral-nemotron"
    RAZORPAY_KEY_ID: str = "rzp_test_xxx"
    RAZORPAY_KEY_SECRET: str = "xxx"
    TWILIO_ACCOUNT_SID: str = "xxx"
    TWILIO_AUTH_TOKEN: str = "xxx"
    TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"
    TEST_WHATSAPP_NUMBER: str | None = None
    SMTP_HOST: str = "sandbox.smtp.mailtrap.io"
    SMTP_PORT: int = 2525
    SMTP_USER: str = "xxx"
    SMTP_PASS: str = "xxx"
    RBI_BANK_RATE: float = 0.055
    DATABASE_URL: str = "sqlite:///./sandbox.db"

    class Config:
        env_file = ".env"

settings = Settings()
