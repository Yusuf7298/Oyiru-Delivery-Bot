import time
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from loguru import logger

MAX_CALLS: int   = 3    # max requests
PERIOD:    float = 1.0  # per second


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, max_calls: int = MAX_CALLS, period: float = PERIOD) -> None:
        self.max_calls = max_calls
        self.period    = period
        # {user_id: [timestamps]}
        self._timestamps: dict[int, list[float]] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id

        if user_id is None:
            return await handler(event, data)

        now  = time.monotonic()
        hist = self._timestamps[user_id]

        # Drop timestamps older than period
        self._timestamps[user_id] = [t for t in hist if now - t < self.period]

        if len(self._timestamps[user_id]) >= self.max_calls:
            logger.warning(f"Throttled user {user_id}")
            if isinstance(event, Message):
                await event.answer("⏳ Too many requests. Please slow down.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⏳ Too many requests.", show_alert=False)
            return None

        self._timestamps[user_id].append(now)
        return await handler(event, data)
