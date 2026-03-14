from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from keyboards.menus import main_menu_kb, chat_reply_kb

router = Router()

WELCOME_TEXT = (
    "Привет... 🌙\n\n"
    "Здесь ты можешь познакомиться с удивительными девушками и погрузиться "
    "в увлекательные диалоги без границ.\n\n"
    "Каждая из них — особенная личность с характером, историей и секретами.\n\n"
    "Всё начинается в «Сценариях». Выбери свою историю 👇"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("👋", reply_markup=chat_reply_kb())
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.message(F.text == "🏠 Главное меню")
async def main_menu_reply_btn(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.callback_query(lambda c: c.data == "menu:main")
async def back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_kb())
    await callback.answer()
