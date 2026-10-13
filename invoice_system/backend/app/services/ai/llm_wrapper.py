"""
LLM wrapper with a provider-agnostic interface.

Configure the provider and API key in .env:

    LLM_PROVIDER=claude    # or "openai"
    LLM_API_KEY=sk-...

Supported providers
-------------------
* claude  – Anthropic Claude API  (requires: pip install anthropic)
* openai  – OpenAI Chat API       (requires: pip install openai)
"""

import logging
from app.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions about invoice documents. "
    "Use ONLY the information present in the document provided. "
    "If the answer cannot be found in the document, say so clearly and concisely."
)


def answer_question_about_document(document_text: str, question: str) -> str:
    """
    Ask a natural-language question about a document's content.

    Args:
        document_text: Structured + raw text representation of the invoice.
        question:      Free-text question from the user.

    Returns:
        The LLM's answer as a plain string.

    Raises:
        ValueError:   Unknown LLM_PROVIDER value.
        RuntimeError: Required package not installed or API call failed.
    """
    provider = settings.llm_provider.lower()
    logger.info("LLM request → provider=%r, question=%r", provider, question[:80])

    if provider == "claude":
        return _ask_claude(document_text, question)
    if provider == "openai":
        return _ask_openai(document_text, question)

    raise ValueError(
        f"Unknown LLM_PROVIDER={provider!r}. Set LLM_PROVIDER=claude or openai in .env"
    )


# ── Providers ─────────────────────────────────────────────────────────────────

def _build_user_message(document_text: str, question: str) -> str:
    return (
        f"DOCUMENT:\n{document_text}\n\n"
        f"QUESTION: {question}"
    )


def _ask_claude(document_text: str, question: str) -> str:
    """Call Anthropic Claude Messages API."""
    try:
        import anthropic
    except ImportError:
        raise RuntimeError(
            "The 'anthropic' package is not installed. "
            "Run: pip install anthropic"
        )

    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY is not set in .env (required for Claude).")

    client = anthropic.Anthropic(api_key=settings.llm_api_key)
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": _build_user_message(document_text, question)}
        ],
    )
    return message.content[0].text


def _ask_openai(document_text: str, question: str) -> str:
    """Call OpenAI Chat Completions API."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError(
            "The 'openai' package is not installed. "
            "Run: pip install openai"
        )

    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY is not set in .env (required for OpenAI).")

    client = OpenAI(api_key=settings.llm_api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_message(document_text, question)},
        ],
    )
    return response.choices[0].message.content
