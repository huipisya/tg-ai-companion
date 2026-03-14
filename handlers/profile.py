from aiogram import Router
from aiogram.types import CallbackQuery
from services.user_service import get_user_stats
from keyboards.menus import profile_kb

router = Router()


@router.callback_query(lambda c: c.data == "menu:profile")
async def show_profile(callback: CallbackQuery) -> None:
    tg_id = callback.from_user.id
    stats = await get_user_stats(tg_id)

    status = "Premium ⭐" if stats.get("is_premium") else "Обычный 🌿"

    text = (
        f"👤 <b>Твой профиль</b>\n\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Баланс сообщений:</b> {stats.get('balance', 0)}\n\n"
        f"📊 <b>Твоя активность:</b>\n"
        f"— Создано диалогов: {stats.get('total_dialogs', 0)}\n"
        f"— Отправлено сообщений: {stats.get('messages_sent', 0)}\n"
    )

    if not stats.get("is_premium"):
        text += "\n✨ <b>Premium</b> — безлимитное общение и эксклюзивные персонажи!"

    await callback.message.edit_text(
        text,
        reply_markup=profile_kb(is_premium=stats.get("is_premium", False)),
        parse_mode="HTML",
    )
    await callback.answer()
