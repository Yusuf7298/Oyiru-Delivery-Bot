from __future__ import annotations
from datetime import datetime
from aiogram.types import CallbackQuery, Message

def generate_order_number(order_id: int) -> str:
    date = datetime.now().strftime("%Y%m%d")
    return f"OYR-{date}-{order_id:04d}"

async def safe_edit_text_or_caption(
    callback_or_msg: CallbackQuery | Message,
    text: str,
    reply_markup=None,
    parse_mode="Markdown",
):
    msg = callback_or_msg.message if isinstance(callback_or_msg, CallbackQuery) else callback_or_msg
    if not msg:
        return

    has_media = bool(getattr(msg, "photo", None) or getattr(msg, "document", None))
    if has_media:
        try:
            await msg.edit_caption(caption=text, reply_markup=reply_markup, parse_mode=parse_mode)
            return
        except Exception:
            pass

    try:
        await msg.edit_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        try:
            await msg.edit_caption(caption=text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception:
            await msg.answer(text=text, reply_markup=reply_markup, parse_mode=parse_mode)