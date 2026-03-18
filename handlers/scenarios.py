from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from services.user_service import (
    get_all_scenarios, get_user, create_conversation,
    get_existing_conversation, get_last_assistant_message,
)
from keyboards.menus import scenarios_kb, chat_reply_kb
from handlers.chat import ChatState

router = Router()


@router.callback_query(lambda c: c.data == "menu:scenarios")
async def show_scenarios(callback: CallbackQuery) -> None:
    tg_id = callback.from_user.id
    user = await get_user(tg_id)
    scenarios = await get_all_scenarios()

    await callback.message.edit_text(
        "💫 <b>Сценарии</b>\n\nВыбери персонажа, с которым хочешь поговорить.\n🔒 — доступно только с Premium.",
        reply_markup=scenarios_kb(scenarios, is_premium=user["is_premium"]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("scenario:start:"))
async def start_scenario(callback: CallbackQuery, state: FSMContext) -> None:
    scenario_id = int(callback.data.split(":")[2])
    tg_id = callback.from_user.id

    user = await get_user(tg_id)
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

    if not user["is_premium"] and user["balance"] <= 0:
        await callback.answer(
            "У тебя закончились сообщения 😔\nПополни баланс в Магазине.",
            show_alert=True,
        )
        return

    # If this scenario has a story mode — show choice
    if scenario["premium_gate_at"]:
        existing = await get_existing_conversation(tg_id, scenario_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 История" + (" (продолжить)" if existing else " (начать)"),
                    callback_data=f"scenario:mode:story:{scenario_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💬 Диалог",
                    callback_data=f"scenario:mode:chat:{scenario_id}",
                ),
            ],
        ])
        await callback.message.edit_text(
            f"{scenario['emoji']} <b>{scenario['name']}</b>\n\n"
            f"{scenario['description']}\n\n"
            "Выбери режим:",
            reply_markup=kb,
            parse_mode="HTML",
        )
        await callback.answer()
        return

    await _launch_chat(callback, state, scenario, tg_id, story_mode=False)


@router.callback_query(lambda c: c.data.startswith("scenario:mode:"))
async def start_scenario_mode(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    mode = parts[2]       # "story" or "chat"
    scenario_id = int(parts[3])
    tg_id = callback.from_user.id

    scenarios = await get_all_scenarios()
    scenario = next((s for s in scenarios if s["id"] == scenario_id), None)
    if not scenario:
        await callback.answer("Сценарий не найден.", show_alert=True)
        return

    await _launch_chat(callback, state, scenario, tg_id, story_mode=(mode == "story"))


async def _launch_chat(callback: CallbackQuery, state: FSMContext, scenario, tg_id: int, story_mode: bool) -> None:
    existing = await get_existing_conversation(tg_id, scenario["id"]) if story_mode else None

    if existing:
        conv_id = existing["id"]
        msg_count = existing["message_count"]
    else:
        conv_id = await create_conversation(tg_id, scenario["id"])
        msg_count = 0

    gate = scenario["premium_gate_at"] if story_mode else None

    await state.set_state(ChatState.in_chat)
    await state.update_data(
        conversation_id=conv_id,
        scenario_name=scenario["name"],
        scenario_system_prompt=scenario["system_prompt"],
        premium_gate_at=gate,
        msg_count=msg_count,
    )

    STORY_INTROS = {
        "Настикс": (
            "Небольшое кафе в центре города. Воскресный день, почти все места заняты. "
            "Ты берёшь кофе и оглядываешься — свободный стул есть только за столиком у окна. "
            "Напротив сидит девушка с книгой и наушниками. Явно не хочет компании. "
            "Ты всё равно садишься."
        ),
        "Вика": (
            "Арбат, солнечный полдень. Ты идёшь мимо художников и уличных музыкантов. "
            "У витрины стоит красивая блондинка — смотрит в телефон с явно раздражённым видом. "
            "Ты решаешь пройти мимо. Но в этот момент она поднимает взгляд — прямо на тебя — "
            "и делает шаг навстречу."
        ),
    }

    if existing and story_mode:
        last_msg = await get_last_assistant_message(conv_id)
        intro = (
            f"{scenario['emoji']} <b>Продолжаем с {scenario['name']}</b>\n\n"
            f"Сообщение {msg_count} из истории\n\n"
            f"<i>Последнее сообщение:</i>\n{last_msg}" if last_msg else
            f"{scenario['emoji']} <b>Продолжаем с {scenario['name']}</b>"
        )
        await callback.message.answer(intro, parse_mode="HTML", reply_markup=chat_reply_kb())
    else:
        header = (
            f"{scenario['emoji']} <b>{'История' if story_mode else 'Диалог'} с {scenario['name']}</b>\n\n"
            f"{scenario['description']}"
        )
        await callback.message.answer(header, parse_mode="HTML", reply_markup=chat_reply_kb())

        scene_intro = STORY_INTROS.get(scenario["name"]) if story_mode else None
        if scene_intro:
            await callback.message.answer(f"<i>{scene_intro}</i>", parse_mode="HTML")
        else:
            await callback.message.answer(f"Напиши что-нибудь — {scenario['name']} ждёт тебя...")
        await callback.answer()
        return

    await callback.answer()
    await callback.answer()
