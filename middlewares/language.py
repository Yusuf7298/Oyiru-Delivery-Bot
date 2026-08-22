from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser
from database.repositories.user_repository import UserRepository
from utils.i18n import t

class LanguageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        session = data.get("session")
        event_user: TelegramUser = data.get("event_from_user")
        
        user = data.get("user")
        lang = "en"

        if not user and session is not None and event_user is not None:
            try:
                user = await UserRepository(session).get_by_telegram_id(event_user.id)
                if user:
                    data["user"] = user
            except Exception:
                pass

        if user and getattr(user, "language", None):
            lang = user.language
        elif event_user and event_user.language_code:
            code = event_user.language_code[:2].lower()
            if code in ["en", "am", "om"]:
                lang = code

        data["lang"] = lang
        data["t"] = lambda key, **kwargs: t(key, lang=lang, **kwargs)
        return await handler(event, data)
