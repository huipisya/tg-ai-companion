import json
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


async def generate_suggestions(
    character_name: str,
    history: list[dict],
    last_reply: str,
) -> list[str]:
    """Generate 3 short reply suggestions from the user's perspective."""
    prompt = (
        f"Ты помогаешь пользователю общаться с персонажем по имени {character_name}. "
        f"Придумай ровно 3 коротких варианта ответа от лица пользователя (не персонажа) — "
        f"разные по тону: один серьёзный, один игривый, один интригующий. "
        f"Каждый вариант — не более 6 слов. "
        f"Верни только JSON-массив строк, без пояснений. Пример: [\"текст1\", \"текст2\", \"текст3\"]"
    )
    messages = [
        {"role": "system", "content": prompt},
        *history[-6:],
        {"role": "assistant", "content": last_reply},
        {"role": "user", "content": "Предложи 3 варианта ответа пользователя."},
    ]
    try:
        response = await get_client().chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=100,
            temperature=0.9,
        )
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception:
        return []
