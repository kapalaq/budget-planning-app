"""Telegram bot entry point for the Budget Planner."""

import asyncio
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import TelegramObject

from telegram.config import BOT_TOKEN
from telegram.backend import _current_token, backend
from telegram.handlers import (
    auth,
    dashboard,
    help,
    transactions,
    transfers,
    wallets,
    recurring,
    sorting,
    filters,
    percentages,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Authenticate Telegram users with the backend before each handler."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user:
            token = await backend.ensure_auth(user.id)
            if token:
                _current_token.set(token)
        return await handler(event, data)


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    # Auth middleware runs before every handler
    dp.update.middleware(AuthMiddleware())

    # Register routers (order matters — auth first, common/cancel last)
    dp.include_router(auth.router)
    dp.include_router(dashboard.router)
    dp.include_router(help.router)
    dp.include_router(transactions.router)
    dp.include_router(transfers.router)
    dp.include_router(wallets.router)
    dp.include_router(recurring.router)
    dp.include_router(sorting.router)
    dp.include_router(filters.router)
    dp.include_router(percentages.router)

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
