from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from services.user_service import get_all_scenarios, get_user, create_conversation
from keyboards.menus import scenarios_kb
from handlers.chat import ChatState

router = Router()


@router.callback_query(lambda c: c.data == "menu:scenarios")
async def show_scenarios(callback: CallbackQuery) -> None:
    tg_id = callback.from_user.id
    user = await get_user(tg_id)
    scenarios = await get_all_scenarios()

    text = (
        "💫 <b>Сценарии</b>\n\n"
        "Выбери персонажа, с которым хочешь поговорить.\n"
        "🔒 — доступно только с Premium."
    )

    await callback.message.edit_text(
        text,
        reply_markup=scenarios_kb(scenarios, is_premium=user["is_premium"]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("scenario:start:"))
async def start_scenario(callback: CallbackQuery, state: FSMContext) -> None:
    scenario_id = int(callback.data.split(":")[2])
    tg_id = callback.from_user.id

    user = await get_user(tg_id)

    # Check premium lock
    scenarios = await get_all_scenarios()
    scenario = next((s for s in scenarios if s["id"] == scenario_id), None)

    if not scenario:
        await callback.answer("Сценарий не найден.", show_alert=True)
        return

    if scenario["is_premium"] and not user["is_premium"]:
        await callback.answer(
            "🔒 Этот сценарий доступен только Premium-пользователям.\nЗайди в Магазин, чтобы улучшить статус.",
            show_alert=True,
        )
        return

    if user["balance"] <= 0:
        await callback.answer(
            "У тебя закончились сообщения 😔\nПополни баланс в Магазине.",
            show_alert=True,
        )
        return

    conv_id = await create_conversation(tg_id, scenario_id)
    await state.set_state(ChatState.in_chat)
    await state.update_data(
        conversation_id=conv_id,
        scenario_name=scenario["name"],
        scenario_system_prompt=scenario["system_prompt"],
    )

    await callback.message.edit_text(
        f"{scenario['emoji']} <b>Диалог с {scenario['name']}</b>\n\n"
        f"{scenario['description']}\n\n"
        f"Напиши что-нибудь — {scenario['name']} ждёт тебя...",
        parse_mode="HTML",
    )
    await callback.answer()
