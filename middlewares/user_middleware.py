from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from services.user_service import get_or_create_user


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, Update):
            tg_user = None
            if event.message:
                tg_user = event.message.from_user
            elif event.callback_query:
                tg_user = event.callback_query.from_user

            if tg_user:
                # Check for referral in start payload
                ref_code = None
                if event.message and event.message.text and event.message.text.startswith("/start "):
                    ref_code = event.message.text.split(" ", 1)[1].strip() or None

                user = await get_or_create_user(
                    tg_id=tg_user.id,
                    username=tg_user.username,
                    ref_code_used=ref_code,
                )
                data["db_user"] = user

        return await handler(event, data)
