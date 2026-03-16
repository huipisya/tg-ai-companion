import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.groq_client import chat_completion, chat_completion_story
from services.user_service import (
    deduct_message, save_message, get_conversation_history,
    increment_conversation_message_count, get_user,
)
from keyboards.menus import chat_kb, chat_suggestions_kb, main_menu_kb

router = Router()
logger = logging.getLogger(__name__)


class ChatState(StatesGroup):
    in_chat = State()


@router.message(ChatState.in_chat, F.text == "🏠 Главное меню")
async def chat_main_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    from handlers.start import WELCOME_TEXT
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.callback_query(lambda c: c.data.startswith("chat:suggest:"))
async def handle_suggestion(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    suggestion_index = int(parts[3])

    data = await state.get_data()
    suggestions = data.get("suggestions", [])

    if suggestion_index >= len(suggestions):
        await callback.answer()
        return

    text = suggestions[suggestion_index]
    await callback.message.edit_text(
        callback.message.text + f"\n\n<i>Ты: {text}</i>",
        reply_markup=None,
        parse_mode="HTML",
    )
    await callback.answer()
    await _process_chat(callback.message, state, text, tg_id=callback.from_user.id)


@router.message(ChatState.in_chat, F.text)
async def handle_chat_message(message: Message, state: FSMContext) -> None:
    await _process_chat(message, state, message.text)


async def _process_chat(message: Message, state: FSMContext, text: str, tg_id: int | None = None) -> None:
    tg_id = tg_id or message.from_user.id
    data = await state.get_data()

    conversation_id = data["conversation_id"]
    system_prompt = data["scenario_system_prompt"]
    premium_gate_at = data.get("premium_gate_at")
    msg_count = data.get("msg_count", 0) + 1

    # Check premium gate before spending balance
    if premium_gate_at and msg_count >= premium_gate_at:
        user = await get_user(tg_id)
        if not user or not user["is_premium"]:
            await message.answer(
                "🔒 Дальше — только для Premium\n\n"
                "Это место, куда попадают только свои. "
                "Оформи подписку в Магазине, чтобы продолжить историю.",
                reply_markup=main_menu_kb(),
            )
            await state.clear()
            return

    has_balance = await deduct_message(tg_id)
    if not has_balance:
        await message.answer(
            "У тебя закончились сообщения 😔\n"
            "Пополни баланс в Магазине, чтобы продолжить.",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        return

    await save_message(conversation_id, "user", text)
    await increment_conversation_message_count(conversation_id)

    history = await get_conversation_history(conversation_id, limit=20)
    history = history[:-1] if history else []

    thinking = await message.answer("...")

    try:
        if premium_gate_at:
            narrative, reply, suggestions = await chat_completion_story(
                system_prompt=system_prompt,
                history=history,
                user_message=text,
            )
        else:
            narrative = None
            suggestions = []
            reply = await chat_completion(
                system_prompt=system_prompt,
                history=history,
                user_message=text,
            )
    except Exception as e:
        logger.exception("chat_completion failed for user %s: %s", tg_id, e)
        await thinking.delete()
        await message.answer("Что-то пошло не так. Попробуй ещё раз.")
        return

    await save_message(conversation_id, "assistant", reply)
    await thinking.delete()

    if narrative:
        await message.answer(f"<i>{narrative}</i>", parse_mode="HTML")

    if suggestions:
        await state.update_data(msg_count=msg_count, suggestions=suggestions)
        await message.answer(reply, reply_markup=chat_suggestions_kb(conversation_id, suggestions))
    else:
        await state.update_data(msg_count=msg_count)
        await message.answer(reply, reply_markup=chat_kb(conversation_id))


@router.callback_query(lambda c: c.data.startswith("chat:end:"))
async def end_chat(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Диалог завершён 👋\n\nВозвращайся, когда захочешь поговорить.",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()
