"""
examples/01_basic_message.py
The simplest possible Claude API call.
"""

from src.utils.client import get_client, get_model
from src.utils.tokens import print_usage

client = get_client()

response = client.messages.create(
    model=get_model(),
    max_tokens=512,
    messages=[
        {"role": "user", "content": "Explain the difference between a list and a tuple in Python in two sentences."}
    ],
)

print(response.content[0].text)
print()
print_usage(response)
