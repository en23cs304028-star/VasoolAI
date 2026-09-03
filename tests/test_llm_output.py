import re
import pytest
from backend.llm.client import draft_message
from backend.config import settings
from unittest.mock import patch

def test_no_hallucinated_numbers():
    facts_list = [
        {"buyer_name": "Acme Corp", "invoice_number": "INV-100", "principal_amount": 50000.0, "days_overdue": 10, "interest_amount": None, "payment_link": "http://pay/1"},
        {"buyer_name": "Globex", "invoice_number": "INV-101", "principal_amount": 12345.67, "days_overdue": 20, "interest_amount": None, "payment_link": "http://pay/2"},
        {"buyer_name": "Initech", "invoice_number": "INV-102", "principal_amount": 999.99, "days_overdue": 40, "interest_amount": 12.34, "payment_link": "http://pay/3"},
    ]
    for i in range(4, 11):
        facts_list.append({
            "buyer_name": f"Buyer {i}", "invoice_number": f"INV-10{i}", "principal_amount": 1000.0 * i, "days_overdue": i * 5, "interest_amount": round(float(i * 2.5), 2) if i > 6 else None, "payment_link": f"http://pay/{i}"
        })
        
    is_dummy_key = settings.NVIDIA_API_KEY == "nvapi-xxx"
    
    class MockMessage:
        def __init__(self, content):
            self.content = content
            
    class MockChoice:
        def __init__(self, message):
            self.message = message
            
    class MockCompletion:
        def __init__(self, choices):
            self.choices = choices
            
    if is_dummy_key:
        with patch('openai.resources.chat.completions.Completions.create') as mock_gen:
            for facts in facts_list:
                tier = "statutory_notice" if facts['days_overdue'] >= 31 else "nudge"
                interest_str = str(facts['interest_amount']) if facts['interest_amount'] is not None else "N/A"
                msmed_str = "Sections 15 and 16 of MSMED Act" if tier == "statutory_notice" else ""
                mock_text = f"Dear {facts['buyer_name']}, {msmed_str} Invoice {facts['invoice_number']} for Rs. {facts['principal_amount']} is {facts['days_overdue']} days late. Interest: {interest_str}. Pay at {facts['payment_link']}."
                mock_gen.return_value = MockCompletion([MockChoice(MockMessage(mock_text))])
                
                message = draft_message(tier, facts)
                _verify_no_hallucinations(tier, facts, message)
    else:
        import openai
        try:
            for facts in facts_list:
                tier = "statutory_notice" if facts['days_overdue'] >= 31 else "nudge"
                message = draft_message(tier, facts)
                _verify_no_hallucinations(tier, facts, message)
        except (openai.APITimeoutError, openai.APIConnectionError) as e:
            pytest.skip(f"Live NVIDIA API endpoint timed out or unavailable: {e}")

def _verify_no_hallucinations(tier, facts, message):
    import re
    raw_numbers = re.findall(r'\b\d+(?:\.\d+)?\b', message.replace(',', ''))
    
    allowed_floats = set()
    for k, v in facts.items():
        if v is not None:
            if isinstance(v, (int, float)):
                allowed_floats.add(float(v))
            elif isinstance(v, str):
                for n in re.findall(r'\b\d+(?:\.\d+)?\b', v.replace(',', '')):
                    allowed_floats.add(float(n))
                    
    if tier == "statutory_notice":
        allowed_floats.update([15.0, 16.0, 2006.0, 2020.0])
        
    for num_str in raw_numbers:
        num_float = float(num_str)
        assert num_float in allowed_floats, f"Invented number {num_float} found! Allowed: {allowed_floats}. Msg: {message}"
