from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.groq_client import chat_completion
from services.user_service import (
    deduct_message, save_message, get_conversation_history
)
from keyboards.menus import chat_kb, main_menu_kb

router = Router()


class ChatState(StatesGroup):
    in_chat = State()


@router.message(ChatState.in_chat, F.text)
async def handle_chat_message(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    data = await state.get_data()

    conversation_id = data["conversation_id"]
    system_prompt = data["scenario_system_prompt"]
    scenario_name = data["scenario_name"]

    has_balance = await deduct_message(tg_id)
    if not has_balance:
        await message.answer(
            "У тебя закончились сообщения 😔\n"
            "Пополни баланс в Магазине, чтобы продолжить.",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        return

    await save_message(conversation_id, "user", message.text)

    history = await get_conversation_history(conversation_id, limit=20)
    # Remove last message since we pass it separately
    history = history[:-1] if history else []

    thinking = await message.answer("...")

    try:
        reply = await chat_completion(
            system_prompt=system_prompt,
            history=history,
            user_message=message.text,
        )
    except Exception:
        await thinking.delete()
        await message.answer("Что-то пошло не так. Попробуй ещё раз.")
        return

    await save_message(conversation_id, "assistant", reply)
    await thinking.delete()
    await message.answer(reply, reply_markup=chat_kb(conversation_id))


@router.callback_query(lambda c: c.data.startswith("chat:end:"))
async def end_chat(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Диалог завершён 👋\n\nВозвращайся, когда захочешь поговорить.",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()
