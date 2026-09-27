"""LLM abstraction — Groq when configured, graceful fallback otherwise."""

from __future__ import annotations

from app.config import GROQ_API_KEY, GROQ_MODEL

FALLBACK_MESSAGE = (
    "AI assistance is temporarily unavailable because GROQ_API_KEY is not configured. "
    "Add your key to backend/.env to enable source-grounded responses."
)


def is_llm_available() -> bool:
    return bool(GROQ_API_KEY and GROQ_API_KEY.strip())


def generate_response(
    user_message: str,
    *,
    system_prompt: str,
    context: str = "",
    max_tokens: int = 1024,
) -> dict:
    """
    Generate an LLM response via Groq.
    Returns dict with keys: text, mode ('groq' | 'fallback'), model (optional).
    Never raises due to missing API key.
    """
    if not is_llm_available():
        return {
            "text": FALLBACK_MESSAGE,
            "mode": "fallback",
            "model": None,
        }

    try:
        from groq import Groq

        client = Groq(api_key=GROQ_API_KEY)
        messages = [{"role": "system", "content": system_prompt}]
        if context.strip():
            messages.append(
                {
                    "role": "user",
                    "content": f"Reference knowledge (use only this — do not invent facts):\n\n{context}",
                }
            )
        messages.append({"role": "user", "content": user_message})

        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,
            reasoning_effort="low",
        )
        text = completion.choices[0].message.content or ""
        return {"text": text.strip(), "mode": "groq", "model": GROQ_MODEL}
    except Exception as exc:
        return {
            "text": f"AI service encountered an error: {exc}. Please try again later.",
            "mode": "fallback",
            "model": GROQ_MODEL,
        }
