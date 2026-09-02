from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.settings_repository import SettingsRepository
from keyboards.support import support_keyboard
from utils.i18n import t

router = Router()

SUPPORT_BTNS = ["📞 Contact Support", "📞 ድጋፍ ያግኙ", "📞 Deeggarsa Qunnamaa"]

@router.message(F.text.in_(SUPPORT_BTNS))
async def show_contact_support(message: Message, session: AsyncSession, lang: str = "en") -> None:
    repo = SettingsRepository(session)
    support = await repo.get_support_contact()

    text = (
        f"{t('support_title', lang)}\n\n"
        f"{t('support_phone_label', lang)}: `{support['phone']}`\n"
        f"{t('support_email_label', lang)}: `{support['email']}`\n"
        f"{t('support_telegram_label', lang)}: [@{support['telegram_username']}]({support['telegram_link']})\n\n"
        f"👨‍💻 Developed by [Yusuf Mohammed](https://yusuf-mohammed.vercel.app/)"
    )

    await message.answer(
        text,
        reply_markup=support_keyboard(support, lang=lang),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

