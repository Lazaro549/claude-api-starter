"""
examples/02_streaming.py
Stream a response token-by-token using the stream() context manager.
"""

from src.utils.client import get_client, get_model

client = get_client()

print("Streaming response:\n")

with client.messages.stream(
    model=get_model(),
    max_tokens=512,
    messages=[{"role": "user", "content": "Write a haiku about Python programming."}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

print("\n\n[stream complete]")
final = stream.get_final_message()
print(f"Total tokens: input={final.usage.input_tokens} output={final.usage.output_tokens}")
