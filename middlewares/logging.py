import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from loguru import logger

class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        start = time.monotonic()
        user_id  = None
        username = None
        detail   = ""

        if isinstance(event, Message):
            if event.from_user:
                user_id  = event.from_user.id
                username = event.from_user.username or event.from_user.full_name
            text = (event.text or event.caption or f"[{event.content_type}]")
            detail = text[:80]
        elif isinstance(event, CallbackQuery):
            if event.from_user:
                user_id  = event.from_user.id
                username = event.from_user.username or event.from_user.full_name
            detail = (event.data or "")[:80]

        log_prefix = f"user={user_id} ({username}) | {detail!r}"

        try:
            result = await handler(event, data)
            elapsed = (time.monotonic() - start) * 1000
            logger.debug(f"✅ {log_prefix} | {elapsed:.1f}ms")
            return result
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.error(
                f"❌ {log_prefix} | {elapsed:.1f}ms | {type(exc).__name__}: {exc}"
            )
            raise
