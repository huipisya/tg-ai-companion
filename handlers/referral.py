from aiogram import Router
from aiogram.types import CallbackQuery
from services.user_service import get_referral_stats
from keyboards.menus import back_to_menu_kb

router = Router()

REFERRAL_TEXT_TEMPLATE = (
    "🎁 <b>Реферальная программа</b>\n\n"
    "Приглашай друзей и получай бонусные сообщения за каждую их покупку.\n\n"
    "Твоя ссылка:\n<code>{ref_link}</code>\n\n"
    "👥 Приглашено: <b>{invited}</b>\n"
    "🎉 Заработано сообщений: <b>{earned}</b>\n\n"
    "<b>Сколько я получу?</b>\n\n"
    "💎 <b>Premium-подписки (50%):</b>\n"
    "— 1 неделя: 75 сообщений\n"
    "— 2 недели: 150 сообщений\n"
    "— 1 месяц: 300 сообщений\n"
    "— 3 месяца: 900 сообщений\n\n"
    "✉️ <b>Пакеты сообщений (50%):</b>\n"
    "— 30+30: 30 сообщений\n"
    "— 100+100: 100 сообщений\n"
    "— 300+300: 300 сообщений\n"
    "— 800+800: 800 сообщений\n"
    "— 2000+2000: 2000 сообщений\n"
    "— 5000+5000: 5000 сообщений\n\n"
    "<i>Бонусы зачисляются сразу и не сгорают.</i>"
)


@router.callback_query(lambda c: c.data == "menu:referral")
async def show_referral(callback: CallbackQuery) -> None:
    tg_id = callback.from_user.id
    stats = await get_referral_stats(tg_id)

    bot_username = (await callback.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={stats['ref_code']}"

    text = REFERRAL_TEXT_TEMPLATE.format(
        ref_link=ref_link,
        invited=stats.get("invited", 0),
        earned=stats.get("earned", 0),
    )

    await callback.message.edit_text(text, reply_markup=back_to_menu_kb(), parse_mode="HTML")
    await callback.answer()
