from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👤 Профиль", callback_data="menu:profile"))
    builder.row(InlineKeyboardButton(text="💫 Сценарии", callback_data="menu:scenarios"))
    builder.row(InlineKeyboardButton(text="💎 Магазин", callback_data="menu:shop"))
    builder.row(InlineKeyboardButton(text="🎁 Мои рефералы", callback_data="menu:referral"))
    return builder.as_markup()


def back_to_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="↩️ Назад в меню", callback_data="menu:main"))
    return builder.as_markup()


def profile_kb(is_premium: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not is_premium:
        builder.row(InlineKeyboardButton(text="💎 Улучшить до Premium", callback_data="menu:shop"))
    builder.row(InlineKeyboardButton(text="↩️ Назад в меню", callback_data="menu:main"))
    return builder.as_markup()


def scenarios_kb(scenarios: list, is_premium: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in scenarios:
        label = f"{s['emoji']} {s['name']}"
        if s["is_premium"] and not is_premium:
            label += " 🔒"
        builder.row(InlineKeyboardButton(
            text=label,
            callback_data=f"scenario:start:{s['id']}",
        ))
    builder.row(InlineKeyboardButton(text="↩️ Назад в меню", callback_data="menu:main"))
    return builder.as_markup()


def shop_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⭐ Купить Premium", callback_data="shop:premium"))
    builder.row(InlineKeyboardButton(text="✉️ Купить сообщения", callback_data="shop:messages"))
    builder.row(InlineKeyboardButton(text="↩️ Назад в меню", callback_data="menu:main"))
    return builder.as_markup()


def premium_tiers_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    tiers = [
        ("1 неделя — 75 ⭐", "premium:1w:75"),
        ("2 недели — 130 ⭐", "premium:2w:130"),
        ("1 месяц — 250 ⭐", "premium:1m:250"),
        ("3 месяца — 650 ⭐", "premium:3m:650"),
    ]
    for label, data in tiers:
        builder.row(InlineKeyboardButton(text=label, callback_data=f"buy:{data}"))
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data="menu:shop"))
    return builder.as_markup()


def message_packs_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    packs = [
        ("30+30 сообщений — 25 ⭐", "pack:30:25"),
        ("100+100 — 75 ⭐", "pack:100:75"),
        ("300+300 — 200 ⭐", "pack:300:200"),
        ("800+800 — 500 ⭐", "pack:800:500"),
        ("2000+2000 — 1100 ⭐", "pack:2000:1100"),
        ("5000+5000 — 2500 ⭐", "pack:5000:2500"),
    ]
    for label, data in packs:
        builder.row(InlineKeyboardButton(text=label, callback_data=f"buy:{data}"))
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data="menu:shop"))
    return builder.as_markup()


def chat_kb(conversation_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🚪 Завершить диалог", callback_data=f"chat:end:{conversation_id}"))
    return builder.as_markup()


def chat_suggestions_kb(conversation_id: int, suggestions: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, text in enumerate(suggestions[:3]):
        builder.row(InlineKeyboardButton(text=text, callback_data=f"chat:suggest:{conversation_id}:{i}"))
    builder.row(InlineKeyboardButton(text="🚪 Завершить диалог", callback_data=f"chat:end:{conversation_id}"))
    return builder.as_markup()


def chat_reply_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏠 Главное меню")]],
        resize_keyboard=True,
    )


def remove_reply_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
