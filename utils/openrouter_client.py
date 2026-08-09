"""
utils/openrouter_client.py
Thin wrapper around the OpenRouter API (https://openrouter.ai) so the rest
of the app never touches HTTP requests directly. Swap models here.

OpenRouter uses an OpenAI-compatible /chat/completions endpoint, so we
just use plain HTTP requests (no special SDK needed).
"""

import os
import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Default model to use. Change this to any model id listed on
# https://openrouter.ai/models (e.g. "openai/gpt-4o-mini",
# "google/gemini-2.5-flash", "anthropic/claude-3.5-haiku", etc.)
# NOTE: "google/gemini-2.0-flash-001" was retired by Google on 1 June 2026 —
# don't switch back to it, OpenRouter will return a 404 "No endpoints found".
DEFAULT_MODEL = "google/gemini-2.5-flash"


def _get_api_key():
    """Check env var first (local dev), then Streamlit secrets (Streamlit Cloud)."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key:
        return api_key
    try:
        import streamlit as st
        return st.secrets.get("OPENROUTER_API_KEY")
    except Exception:
        return None


def generate(prompt, model_name=DEFAULT_MODEL, temperature=0.4, max_tokens=2000):
    """Send a single prompt to OpenRouter and return the text response."""
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Locally: copy .env.example to .env "
            "and paste your OpenRouter key. On Streamlit Cloud: add it under "
            "App settings -> Secrets."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # Optional but recommended by OpenRouter for analytics/rankings.
        "HTTP-Referer": "https://eduhelp-ai.local",
        "X-Title": "EduHelp AI",
    }

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        # Keep this well under your OpenRouter credit-based token budget.
        # Raise it later once you've added credits at
        # https://openrouter.ai/settings/credits if responses get cut off.
        "max_tokens": max_tokens,
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(
            f"OpenRouter API error {response.status_code}: {response.text}"
        )

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected OpenRouter response format: {data}") from e
