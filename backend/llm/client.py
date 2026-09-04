import os
from openai import OpenAI
from backend.config import settings
from backend.llm.prompts import SYSTEM_PROMPT

client = OpenAI(
    base_url="https://openrouter.ai/api/v1" if settings.NVIDIA_API_KEY.startswith("sk-or") else "https://integrate.api.nvidia.com/v1",
    api_key=settings.NVIDIA_API_KEY,
    timeout=60.0,
)

def extract_final_message(raw_text: str) -> str:
    content = raw_text.strip()
    
    # Check for [DRAFT]...[/DRAFT] blocks
    if "[DRAFT]" in content:
        parts = content.split("[DRAFT]")[-1]
        if "[/DRAFT]" in parts:
            parts = parts.split("[/DRAFT]")[0]
        content = parts.strip()

    if "</think>" in content:
        content = content.split("</think>")[-1].strip()
    if "[Output]" in content:
        content = content.split("[Output]")[-1].strip()
    if "*Body:*" in content:
        content = content.split("*Body:*")[-1].strip()
    
    # If model outputted a thinking process preamble
    if "thinking process" in content.lower() or content.startswith("1. ") or "analyze user" in content.lower():
        markers = [
            "\nDear ", "\n\nDear ",
            "\nSubject:", "\n\nSubject:",
            "\nTo:", "\n\nTo:",
            "\nHi ", "\n\nHi ",
            "\nHello ", "\n\nHello ",
            '\n"Dear ', '\n\n"Dear ',
            "\nPayment Reminder", "\n\nPayment Reminder",
            "\nSTATUTORY NOTICE", "\n\nSTATUTORY NOTICE",
            "\nFIRM REMINDER", "\n\nFIRM REMINDER"
        ]
        best_idx = -1
        for m in markers:
            idx = content.find(m)
            if idx != -1:
                if best_idx == -1 or idx < best_idx:
                    best_idx = idx
        
        if best_idx != -1:
            content = content[best_idx:].strip()
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1].strip()
        else:
            # Sift out thinking bullet points
            paragraphs = content.split("\n\n")
            cleaned_paras = [p for p in paragraphs if not any(k in p.lower() for k in ["thinking", "analyze", "deconstruct", "constraints", "tone:", "facts provided:"])]
            if cleaned_paras:
                content = "\n\n".join(cleaned_paras).strip()

    if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
        content = content[1:-1].strip()

    # If after extraction it still contains thinking process or is too short, reject so fallback is used
    if "thinking process" in content.lower() or "analyze user" in content.lower() or len(content.split()) < 10:
        return ""

    return content.strip()

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
    
    instruction = f"\nDraft the message for the tier '{tier}' using the facts above. Enclose your final draft strictly between [DRAFT] and [/DRAFT] tags."
    
    for attempt in range(2):
        try:
            completion = client.chat.completions.create(
                model=settings.NVIDIA_DRAFT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an automated payment reminder drafting engine for Indian MSMEs. You must produce the final draft message inside [DRAFT] and [/DRAFT] tags. Output no extra conversational filler."},
                    {"role": "user", "content": prompt + instruction}
                ],
                temperature=0.2,
                max_tokens=1024,
            )
            raw_content = completion.choices[0].message.content or ""
            clean_msg = extract_final_message(raw_content)
            if clean_msg:
                return clean_msg
        except Exception as e:
            print(f"NVIDIA drafting attempt {attempt + 1} failed: {e}")

    # Deterministic fallback if API has inference connection error
    buyer = facts.get('buyer_name', 'Valued Customer')
    inv_num = facts.get('invoice_number', '')
    amt = facts.get('principal_amount', '')
    days = facts.get('days_overdue', '')
    link = facts.get('payment_link', '')
    interest = facts.get('interest_amount')
    
    if tier == "statutory_notice":
        int_text = f"Accrued statutory interest under Section 16 amounts to ₹{interest}." if interest else ""
        return (
            f"Dear {buyer},\n\n"
            f"This is a formal statutory notice pursuant to Sections 15 and 16 of the Micro, Small and Medium Enterprises Development Act, 2006 (MSMED Act). "
            f"Invoice {inv_num} for the principal amount of ₹{amt} is now overdue by {days} days. "
            f"{int_text} Please discharge this liability immediately using the following payment link: {link}"
        )
    elif tier == "firm_reminder":
        return (
            f"Dear {buyer},\n\n"
            f"This is a firm reminder that invoice {inv_num} for the principal amount of ₹{amt} is now {days} days overdue. "
            f"Please arrange payment at your earliest convenience via the following link: {link}"
        )
    else:
        return (
            f"Dear {buyer},\n\n"
            f"This is a friendly reminder that invoice {inv_num} for ₹{amt} is now due. "
            f"You can easily make the payment using this link: {link}"
        )

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
