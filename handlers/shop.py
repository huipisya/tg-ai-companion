from aiogram import Router
from aiogram.types import CallbackQuery, LabeledPrice, PreCheckoutQuery, Message
from keyboards.menus import shop_kb, premium_tiers_kb, message_packs_kb, back_to_menu_kb
from services.user_service import record_purchase

router = Router()

SHOP_TEXT = (
    "💎 <b>Магазин</b>\n\n"
    "Расширь свои возможности:\n\n"
    "⭐ <b>Premium-подписка</b> — эксклюзивные персонажи и еженедельное пополнение сообщений.\n\n"
    "✉️ <b>Пакеты сообщений</b> — если нужно ещё, мы поможем."
)

PREMIUM_TIER_MESSAGES = {
    "1w": 150,
    "2w": 300,
    "1m": 600,
    "3m": 1800,
}


@router.callback_query(lambda c: c.data == "menu:shop")
async def show_shop(callback: CallbackQuery) -> None:
    await callback.message.edit_text(SHOP_TEXT, reply_markup=shop_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(lambda c: c.data == "shop:premium")
async def show_premium_tiers(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "⭐ <b>Premium-подписка</b>\n\nВыбери срок подписки:",
        reply_markup=premium_tiers_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "shop:messages")
async def show_message_packs(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "✉️ <b>Пакеты сообщений</b>\n\nКоличество удваивается — бонус сразу на счёт:",
        reply_markup=message_packs_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("buy:"))
async def initiate_purchase(callback: CallbackQuery) -> None:
    # data format: buy:premium:1w:75 or buy:pack:100:75
    parts = callback.data.split(":")
    kind = parts[1]  # "premium" or "pack"
    amount_str = parts[2]
    stars = int(parts[3])

    if kind == "premium":
        title = f"Premium {amount_str}"
        description = f"Premium-подписка на {amount_str} + {PREMIUM_TIER_MESSAGES.get(amount_str, 0)} сообщений"
    else:
        amount = int(amount_str)
        title = f"Пакет {amount}+{amount} сообщений"
        description = f"{amount * 2} сообщений на твой баланс"

    await callback.message.answer_invoice(
        title=title,
        description=description,
        payload=callback.data,
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=stars)],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(lambda m: m.successful_payment is not None)
async def successful_payment(message: Message) -> None:
    payload = message.successful_payment.invoice_payload
    parts = payload.split(":")
    kind = parts[1]
    stars = int(parts[3])
    tg_id = message.from_user.id

    if kind == "premium":
        tier = parts[2]
        messages_added = PREMIUM_TIER_MESSAGES.get(tier, 0)
        await record_purchase(tg_id, f"premium_{tier}", messages_added, stars)
        await message.answer(
            f"⭐ Premium активирован!\n+{messages_added} сообщений добавлено на баланс.",
            reply_markup=back_to_menu_kb(),
        )
    else:
        amount = int(parts[2])
        messages_added = amount * 2
        await record_purchase(tg_id, f"pack_{amount}", messages_added, stars)
        await message.answer(
            f"✉️ Готово! +{messages_added} сообщений добавлено на баланс.",
            reply_markup=back_to_menu_kb(),
        )
