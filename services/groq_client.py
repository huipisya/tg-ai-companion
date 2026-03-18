import json
import logging
import re

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


async def chat_completion_story(
    system_prompt: str,
    history: list[dict],
    user_message: str,
    max_tokens: int = 700,
) -> tuple[str | None, str, list[str]]:
    """
    Story mode: returns (narrative, reply, suggestions).
    narrative — atmospheric narrator text (or None).
    reply — character message.
    suggestions — 2-3 short inline reply options (or []).
    """
    story_system = (
        system_prompt
        + '\n\nВАЖНО: Отвечай строго в формате JSON без markdown-блоков:\n'
        '{"narrative": "...", "reply": "...", "suggestions": ["...", "..."]}\n'
        'narrative — атмосферное описание от нарратора (от второго лица, настоящее время, 1-3 предложения). '
        'Используй только когда происходит смена места или важный момент. В остальных случаях — пустая строка "".\n'
        'reply — твой ответ как персонажа.\n'
        'suggestions — массив из 2-3 коротких вариантов ответа от лица пользователя (не более 5 слов каждый). '
        'Добавляй РЕДКО — только в ключевые моменты истории когда нужен явный выбор: согласиться идти куда-то, '
        'отреагировать на признание, принять решение. НЕ добавляй на обычные вопросы в разговоре — '
        'пользователь сам напишет. В большинстве сообщений — пустой массив [].'
    )
    messages = [{"role": "system", "content": story_system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    raw = ""
    try:
        response = await get_client().chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.85,
        )
        raw = response.choices[0].message.content.strip()
        # strip markdown code blocks
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        # try to extract JSON object if there's garbage around it
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            raw = match.group(0)
        data = json.loads(raw)
        narrative = data.get("narrative", "").strip() or None
        reply = data.get("reply", "").strip()
        suggestions = data.get("suggestions", [])
        if not isinstance(suggestions, list):
            suggestions = []
        return narrative, reply, suggestions
    except json.JSONDecodeError:
        logger.warning("Groq story JSON parse failed, using raw response as reply: %s", raw[:100])
        return None, raw or "...", []
    except Exception as e:
        logger.exception("Groq story API error: %s", e)
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
