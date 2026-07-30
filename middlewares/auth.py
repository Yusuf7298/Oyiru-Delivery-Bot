import traceback
import os
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from loguru import logger

_ERROR_TEXT = (
    "⚠️ An unexpected error occurred. Our team has been notified.\n"
    "Please try again in a moment."
)

_DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"


class ErrorHandlingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Unhandled exception:\n{tb}")

            # Send user-facing error without exposing internals
            try:
                if _DEV_MODE:
                    err_msg = f"⚠️ *Error (dev mode)*\n```\n{type(e).__name__}: {e}\n```"
                else:
                    err_msg = _ERROR_TEXT

                if isinstance(event, Message):
                    await event.answer(err_msg, parse_mode="Markdown" if _DEV_MODE else None)
                elif isinstance(event, CallbackQuery):
                    await event.answer(f"Error: {type(e).__name__}: {e}"[:200], show_alert=True)
            except Exception:
                pass  # Don't let error-notification itself crash anything

            return None  # Swallow the exception — bot keeps running
