import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, PORT
from database.db import run_migrations, close_pool
from middlewares.user_middleware import UserMiddleware
from handlers import start, profile, scenarios, chat, shop, referral

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    await run_migrations()
    await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")
    logger.info("Bot started, webhook set.")


async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook()
    await close_pool()
    logger.info("Bot stopped.")


def build_app() -> web.Application:
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.update.middleware(UserMiddleware())

    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(scenarios.router)
    dp.include_router(chat.router)
    dp.include_router(shop.router)
    dp.include_router(referral.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    return app


if __name__ == "__main__":
    app = build_app()
    web.run_app(app, host=WEBAPP_HOST, port=PORT)
