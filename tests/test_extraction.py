import pytest
from backend.llm.client import extract_structured
from backend.config import settings
from unittest.mock import patch

def test_extract_structured_minimal():
    class MockMessage:
        def __init__(self, content):
            self.content = content
            
    class MockChoice:
        def __init__(self, message):
            self.message = message
            
    class MockCompletion:
        def __init__(self, choices):
            self.choices = choices
            
    prompt = "Extract details: Invoice #123, Acme Corp, 500.0"
    expected_output = '{"invoice_number": "123", "buyer_name": "Acme Corp", "amount": 500.0}'
    
    with patch('openai.resources.chat.completions.Completions.create') as mock_gen:
        mock_gen.return_value = MockCompletion([MockChoice(MockMessage(expected_output))])
        result = extract_structured(prompt)
        assert result == expected_output
