"""Telegram bot entry point for the Budget Planner."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from telegram.config import BOT_TOKEN
from telegram.backend import backend
from telegram.handlers import (
    dashboard,
    help,
    transactions,
    transfers,
    wallets,
    recurring,
    sorting,
    filters,
    percentages,
    common,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers (order matters — common/cancel should be last)
    dp.include_router(dashboard.router)
    dp.include_router(help.router)
    dp.include_router(transactions.router)
    dp.include_router(transfers.router)
    dp.include_router(wallets.router)
    dp.include_router(recurring.router)
    dp.include_router(sorting.router)
    dp.include_router(filters.router)
    dp.include_router(percentages.router)
    dp.include_router(common.router)

    return dp


async def main():
    if not BOT_TOKEN:
        logger.error(
            "TELEGRAM_BOT_TOKEN is not set. "
            "Add it to your .env file or environment variables."
        )
        return

    bot = Bot(token=BOT_TOKEN)
    dp = create_dispatcher()

    logger.info("Starting Budget Planner Telegram bot...")
    try:
        await dp.start_polling(bot)
    finally:
        await backend.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
