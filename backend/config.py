import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = "xxx"
    GEMINI_MODEL: str = "gemini-3.7-flash"
    RAZORPAY_KEY_ID: str = "rzp_test_xxx"
    RAZORPAY_KEY_SECRET: str = "xxx"
    TWILIO_ACCOUNT_SID: str = "xxx"
    TWILIO_AUTH_TOKEN: str = "xxx"
    TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"
    SMTP_HOST: str = "sandbox.smtp.mailtrap.io"
    SMTP_PORT: int = 2525
    SMTP_USER: str = "xxx"
    SMTP_PASS: str = "xxx"
    RBI_BANK_RATE: float = 0.055
    DATABASE_URL: str = "sqlite:///./sandbox.db"

    class Config:
        env_file = ".env"

settings = Settings()
