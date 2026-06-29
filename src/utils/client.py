"""
src/utils/client.py
Anthropic client factory — reads config from environment variables.
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")


def get_client() -> Anthropic:
    """Return a configured Anthropic client."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Copy .env.example to .env and add your key."
        )
    return Anthropic(api_key=api_key)


def get_model() -> str:
    """Return the model name to use across examples."""
    return DEFAULT_MODEL
