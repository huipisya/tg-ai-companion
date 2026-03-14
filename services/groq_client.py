import logging

from groq import AsyncGroq
from config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)
_client: AsyncGroq | None = None


def get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=GROQ_API_KEY)
    return _client


async def chat_completion(
    system_prompt: str,
    history: list[dict],
    user_message: str,
    max_tokens: int = 500,
) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    logger.info("Sending request to Groq: model=%s, messages=%d", GROQ_MODEL, len(messages))
    try:
        response = await get_client().chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.85,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.exception("Groq API error: %s", e)
        raise
