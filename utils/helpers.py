import re
from datetime import datetime
from aiogram.types import CallbackQuery, Message

def normalize_ethiopian_phone(phone: str | None) -> str | None:
    """
    Validates and standardizes Ethiopian phone numbers.
    Accepts: +2519, +2517, 09, 07, 2519, 2517, 9, 7
    Returns: +2519XXXXXXXX or +2517XXXXXXXX
    Returns None if invalid.
    """
    if not phone:
        return None
    cleaned = re.sub(r"[\s\-\(\)\.]", "", str(phone).strip())

    if re.match(r"^\+251[97]\d{8}$", cleaned):
        return cleaned
    if re.match(r"^251[97]\d{8}$", cleaned):
        return f"+{cleaned}"
    if re.match(r"^0[97]\d{8}$", cleaned):
        return f"+251{cleaned[1:]}"
    if re.match(r"^[97]\d{8}$", cleaned):
        return f"+251{cleaned}"
    return None

def format_phone_display(phone: str | None) -> str:
    norm = normalize_ethiopian_phone(phone)
    if not norm:
        return str(phone or "—")
    if norm.startswith("+251"):
        return "0" + norm[4:]
    return norm

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
    
    # 1. Try editing caption if media message
    if has_media:
        try:
            await msg.edit_caption(caption=text, reply_markup=reply_markup, parse_mode=parse_mode)
            return
        except Exception as e:
            if "can't parse entities" in str(e).lower() or "entity" in str(e).lower():
                try:
                    await msg.edit_caption(caption=text, reply_markup=reply_markup, parse_mode=None)
                    return
                except Exception:
                    pass

    # 2. Try editing text
    try:
        await msg.edit_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
        return
    except Exception as e:
        if "can't parse entities" in str(e).lower() or "entity" in str(e).lower():
            try:
                await msg.edit_text(text=text, reply_markup=reply_markup, parse_mode=None)
                return
            except Exception:
                pass

    # 3. Fallback: try caption without parse mode or sending a new message
    try:
        await msg.edit_caption(caption=text, reply_markup=reply_markup, parse_mode=None)
    except Exception:
        try:
            await msg.answer(text=text, reply_markup=reply_markup, parse_mode=None)
        except Exception:
            pass