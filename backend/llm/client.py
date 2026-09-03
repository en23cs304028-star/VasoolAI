import os
from openai import OpenAI
from backend.config import settings
from backend.llm.prompts import SYSTEM_PROMPT

client = OpenAI(
    base_url="https://openrouter.ai/api/v1" if settings.NVIDIA_API_KEY.startswith("sk-or") else "https://integrate.api.nvidia.com/v1",
    api_key=settings.NVIDIA_API_KEY,
    timeout=30.0,
)

def draft_message(tier: str, facts: dict) -> str:
    interest_amount = facts.get('interest_amount')
    if interest_amount is None:
        interest_amount_str = "N/A"
    else:
        interest_amount_str = str(interest_amount)
        
    prompt = SYSTEM_PROMPT.format(
        buyer_name=facts.get('buyer_name', ''),
        invoice_number=facts.get('invoice_number', ''),
        principal_amount=facts.get('principal_amount', ''),
        days_overdue=facts.get('days_overdue', ''),
        interest_amount=interest_amount_str,
        payment_link=facts.get('payment_link', '')
    )
    
    instruction = f"\nDraft the message for the tier '{tier}' using the facts above."
    
    completion = client.chat.completions.create(
        model=settings.NVIDIA_DRAFT_MODEL,
        messages=[{"role": "user", "content": prompt + instruction}],
        temperature=0.4,
        max_tokens=4096,
    )
    raw_content = completion.choices[0].message.content or ""
    if "</think>" in raw_content:
        raw_content = raw_content.split("</think>")[-1]
    if "[Output]" in raw_content:
        raw_content = raw_content.split("[Output]")[-1]
    return raw_content.strip()

def extract_structured(prompt: str) -> str:
    """Used by the ledger/invoice parsing path. Different model from
    draft_message — Mistral Nemotron handles structured/JSON output more
    reliably than Lightning, which doesn't enforce response_format."""
    completion = client.chat.completions.create(
        model=settings.NVIDIA_EXTRACT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1024,
    )
    return completion.choices[0].message.content
