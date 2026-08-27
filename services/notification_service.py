import datetime
import logging
import os
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.models.order import OrderStatus
try:
    from config.settings import ( # type: ignore
        ADMIN_ID,
        ORDERS_GROUP_ID,
        STORE_MANAGERS_GROUP_ID,
        INVENTORY_GROUP_ID,
        SALES_MANAGERS_GROUP_ID,
        QUALITY_CONTROL_GROUP_ID,
        OPERATIONS_GROUP_ID,
    )
except Exception:
    ADMIN_ID                 = os.getenv("ADMIN_ID", "8223004316")
    ORDERS_GROUP_ID          = os.getenv("ORDERS_GROUP_ID",          ADMIN_ID)
    STORE_MANAGERS_GROUP_ID  = os.getenv("STORE_MANAGERS_GROUP_ID",  ADMIN_ID)
    INVENTORY_GROUP_ID       = os.getenv("INVENTORY_GROUP_ID",       ADMIN_ID)
    SALES_MANAGERS_GROUP_ID  = os.getenv("SALES_MANAGERS_GROUP_ID",  ADMIN_ID)
    QUALITY_CONTROL_GROUP_ID = os.getenv("QUALITY_CONTROL_GROUP_ID", ADMIN_ID)
    OPERATIONS_GROUP_ID      = os.getenv("OPERATIONS_GROUP_ID",      ADMIN_ID)

def _now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
def _products_block(order) -> str:
    if getattr(order, "file_path", None):
        fname = getattr(order, "original_filename", None) or "uploaded file"
        ftype = (getattr(order, "file_type", None) or "document").title()
        return f"📎 {ftype}: `{fname}`"
    try:
        items = getattr(order, "items", []) or []
        lines = [
            f"  • {item.product.name} — {item.quantity} {item.product.unit}"
            for item in items
            if getattr(item, "product", None)
        ]
        return "\n".join(lines) if lines else "—"
    except Exception:
        return "—"


def _order_detail_block(order, customer=None) -> str:
    """Full order detail block used in group notifications."""
    try:
        hotel = order.hotel.name if getattr(order, "hotel", None) else "—"
    except Exception:
        hotel = "—"

    try:
        if customer:
            cust = customer.full_name
        elif getattr(order, "customer", None):
            cust = order.customer.full_name
        else:
            cust = "—"
    except Exception:
        cust = "—"

    status_val = order.status.value if hasattr(order.status, "value") else str(order.status)
    driver   = f"\n🚗 Driver: {order.driver_name}" if getattr(order, "driver_name", None) else ""
    note     = f"\n📝 Note: {order.note}" if getattr(order, "note", None) else ""
    return (
        f"🆔 Order: `{order.order_number}`\n"
        f"🏨 Hotel: {hotel}\n"
        f"👤 Customer: {cust}\n"
        f"📌 Status: {status_val}{driver}{note}\n"
        f"⏰ Time: {_now()}\n\n"
        f"🛒 Products / File:\n{_products_block(order)}"
    )


import re

def _extract_chat_ids(targets) -> list[int]:
    if targets is None:
        return []
    if isinstance(targets, (int, float)):
        return [int(targets)] if int(targets) != 0 else []

    result = []
    items = targets if isinstance(targets, (list, tuple, set)) else [targets]
    for item in items:
        if item is None:
            continue
        if isinstance(item, (int, float)):
            val = int(item)
            if val != 0 and val not in result:
                result.append(val)
            continue
        str_val = str(item).strip()
        if not str_val or str_val == "0":
            continue
        for part in re.split(r"[,;\s]+", str_val):
            part = part.strip()
            if not part or part == "0":
                continue
            try:
                val = int(part)
                if val != 0 and val not in result:
                    result.append(val)
            except ValueError:
                pass
    return result


async def _send_order_media(
    bot: Bot,
    chat_id: int,
    caption: str,
    telegram_file_id: str = None,
    file_path: str = None,
    file_type: str = None,
    **kwargs
):
    cid = int(chat_id)
    if cid == 0:
        return
    try:
        # Ensure caption fits Telegram's 1024 character limit for media
        safe_caption = caption
        overflow_text = None
        if len(caption) > 1020:
            safe_caption = caption[:1015] + "..."
            overflow_text = "..." + caption[1015:]

        # Detect photo file type
        ext = ""
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
        is_photo = (file_type == "photo" or ext in [".jpg", ".jpeg", ".png", ".webp"])

        # 1. Try sending via telegram_file_id
        if telegram_file_id:
            try:
                if is_photo:
                    await bot.send_photo(chat_id=cid, photo=telegram_file_id, caption=safe_caption, **kwargs)
                else:
                    await bot.send_document(chat_id=cid, document=telegram_file_id, caption=safe_caption, **kwargs)
                if overflow_text:
                    await bot.send_message(chat_id=cid, text=overflow_text, **kwargs)
                return
            except Exception as exc_tfid:
                logging.debug(f"send_photo/document with telegram_file_id to {cid} failed: {exc_tfid}. Trying local file_path.")

        # 2. Try sending via local file_path
        if file_path:
            candidate_paths = [
                os.path.join(os.getcwd(), file_path) if not os.path.isabs(file_path) else file_path,
                os.path.join(os.getcwd(), "uploads", os.path.basename(file_path)),
                file_path,
            ]
            valid_path = next((p for p in candidate_paths if os.path.exists(p)), None)
            if valid_path:
                from aiogram.types import FSInputFile
                file_input = FSInputFile(valid_path)
                try:
                    if is_photo:
                        await bot.send_photo(chat_id=cid, photo=file_input, caption=safe_caption, **kwargs)
                    else:
                        await bot.send_document(chat_id=cid, document=file_input, caption=safe_caption, **kwargs)
                    if overflow_text:
                        await bot.send_message(chat_id=cid, text=overflow_text, **kwargs)
                    return
                except Exception as exc_fp:
                    logging.debug(f"send_photo/document with FSInputFile to {cid} failed: {exc_fp}. Fallback to text.")

        # 3. Fallback to text message if media could not be sent
        await bot.send_message(chat_id=cid, text=caption, **kwargs)
    except Exception as e:
        err_msg = str(e)
        if "chat not found" in err_msg.lower():
            logging.info(f"Notification skipped for chat {cid} (bot not in chat or channel not created yet).")
        elif "blocked by the user" in err_msg.lower():
            logging.info(f"Notification skipped: User {cid} has blocked the bot.")
        else:
            logging.warning(f"Notification to {cid} failed: {e}")


async def _send(bot: Bot, chat_id: int, text: str, **kwargs):
    cid = int(chat_id)
    if cid == 0:
        return
    try:
        await bot.send_message(chat_id=cid, text=text, **kwargs)
    except Exception as e:
        err_msg = str(e)
        if "chat not found" in err_msg.lower():
            logging.info(f"Notification skipped for chat {cid} (bot not in chat or channel not created yet).")
        elif "blocked by the user" in err_msg.lower():
            logging.info(f"Notification skipped: User {cid} has blocked the bot.")
        else:
            logging.warning(f"Notification to {cid} failed: {e}")


async def _broadcast(bot: Bot, targets, text: str, **kwargs):
    ids = _extract_chat_ids(targets)
    for cid in ids:
        await _send(bot, cid, text, **kwargs)


async def _broadcast_order(
    bot: Bot,
    targets,
    text: str,
    telegram_file_id: str = None,
    file_path: str = None,
    file_type: str = None,
    **kwargs
):
    ids = _extract_chat_ids(targets)
    for cid in ids:
        if telegram_file_id or file_path:
            await _send_order_media(
                bot,
                cid,
                caption=text,
                telegram_file_id=telegram_file_id,
                file_path=file_path,
                file_type=file_type,
                **kwargs
            )
        else:
            await _send(bot, cid, text, **kwargs)

async def notify_new_order(bot: Bot, order, customer):
    text = (
        "🆕 New Order Submitted\n\n"
        + _order_detail_block(order, customer)
    )
    targets = {
        ADMIN_ID,
        ORDERS_GROUP_ID,
        STORE_MANAGERS_GROUP_ID,
        INVENTORY_GROUP_ID,
    }
    await _broadcast_order(
        bot,
        targets,
        text,
        telegram_file_id=getattr(order, "telegram_file_id", None),
        file_path=getattr(order, "file_path", None),
        file_type=getattr(order, "file_type", None),
        parse_mode="Markdown",
    )

notify_admin_new_order = notify_new_order
async def notify_driver_assigned(bot: Bot, order, driver_telegram_id: int, driver_name: str):
    caption = (
        f"📦 New Delivery Assigned\n\n"
        f"🆔 Order: `{order.order_number}`\n"
        f"🏨 Hotel: {order.hotel.name if getattr(order, 'hotel', None) else '—'}\n"
        f"📍 Address: {order.hotel.address if getattr(order, 'hotel', None) else '—'}\n"
        f"🚗 Driver: {driver_name}\n"
        f"⏰ Time: {_now()}\n\n"
        f"🛒 Order:\n{_products_block(order)}"
    )
    await _send_order_media(
        bot,
        driver_telegram_id,
        caption=caption,
        telegram_file_id=getattr(order, "telegram_file_id", None),
        file_path=getattr(order, "file_path", None),
        file_type=getattr(order, "file_type", None),
        parse_mode="Markdown",
    )
from utils.i18n import t

_STATUS_KEY = {
    OrderStatus.APPROVED:         "status_approved",
    OrderStatus.PREPARING:        "status_preparing",
    OrderStatus.PACKED:           "status_packed",
    OrderStatus.OUT_FOR_DELIVERY: "status_out_for_delivery",
    OrderStatus.DELIVERED:        "status_delivered",
    OrderStatus.CANCELLED:        "status_cancelled",
}

async def notify_customer_status_update(bot: Bot, order, customer_telegram_id: int):
    lang = "en"
    if getattr(order, "customer", None) and getattr(order.customer, "language", None):
        lang = order.customer.language

    status_key = _STATUS_KEY.get(order.status)
    if status_key:
        status_msg = t(status_key, lang)
    else:
        status_msg = f"Your order status: {order.status.value}"

    driver_line = f"\n🚗 Driver: {order.driver_name}" if order.driver_name else ""

    # When out for delivery, add the delivery partner's contact details if available
    driver_contact = ""
    if order.status == OrderStatus.OUT_FOR_DELIVERY:
        dp = getattr(order, "delivery_partner", None)
        if dp:
            driver_contact += f"\n👤 Driver: {dp.full_name}"
            if getattr(dp, "phone", None):
                driver_contact += f"\n📞 Phone: {dp.phone}"
        elif order.driver_name:
            driver_contact = f"\n👤 Driver: {order.driver_name}"

    text = (
        f"🔔 Order Update\n\n"
        f"🆔 Order: `{order.order_number}`\n"
        f"🏨 Hotel: {order.hotel.name if order.hotel else '—'}\n"
        f"📌 Status: {order.status.value}{driver_line}\n"
        f"⏰ Time: {_now()}\n"
        f"{driver_contact}\n"
        f"{status_msg}"
    )

    reply_markup = None
    if order.status == OrderStatus.DELIVERED:
        text += "\n\n⭐ Please rate your delivery experience:"
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="⭐ 1", callback_data=f"rate_order:{order.id}:1"),
                InlineKeyboardButton(text="⭐ 2", callback_data=f"rate_order:{order.id}:2"),
                InlineKeyboardButton(text="⭐ 3", callback_data=f"rate_order:{order.id}:3"),
                InlineKeyboardButton(text="⭐ 4", callback_data=f"rate_order:{order.id}:4"),
                InlineKeyboardButton(text="⭐ 5", callback_data=f"rate_order:{order.id}:5"),
            ]]
        )
        group_text = (
            "✅ Order Delivered\n\n"
            + _order_detail_block(order)
        )
        targets = {ORDERS_GROUP_ID, STORE_MANAGERS_GROUP_ID, SALES_MANAGERS_GROUP_ID}
        await _broadcast_order(
            bot,
            targets,
            group_text,
            telegram_file_id=getattr(order, "telegram_file_id", None),
            file_path=getattr(order, "file_path", None),
            file_type=getattr(order, "file_type", None),
            parse_mode="Markdown",
        )

    await _send(bot, customer_telegram_id, text, parse_mode="Markdown", reply_markup=reply_markup)

async def notify_customer_rejected(bot: Bot, order, customer_telegram_id: int, reason: str):
    text = (
        f"❌ Order Rejected\n\n"
        f"🆔 Order: `{order.order_number}`\n"
        f"🏨 Hotel: {order.hotel.name if order.hotel else '—'}\n"
        f"📌 Status: {order.status.value}\n"
        f"⏰ Time: {_now()}\n\n"
        f"📋 Reason: {reason}"
    )
    await _send(bot, customer_telegram_id, text, parse_mode="Markdown")

async def notify_sales_managers(bot: Bot, order, action: str):
    text = (
        f"📊 Sales Monitor — {action}\n\n"
        + _order_detail_block(order)
    )
    await _broadcast_order(
        bot,
        {SALES_MANAGERS_GROUP_ID, ADMIN_ID},
        text,
        telegram_file_id=getattr(order, "telegram_file_id", None),
        file_path=getattr(order, "file_path", None),
        file_type=getattr(order, "file_type", None),
        parse_mode="Markdown",
    )

async def notify_operations(bot: Bot, order, rating: int, feedback: str = None): # type: ignore
    stars = "⭐" * rating + "☆" * (5 - rating)
    driver_line = f"\n🚗 Driver: {order.driver_name}" if order.driver_name else ""
    text = (
        f"📋 Customer Feedback Report\n\n"
        f"🆔 Order: `{order.order_number}`\n"
        f"🏨 Hotel: {order.hotel.name if order.hotel else '—'}\n"
        f"👤 Customer: {order.customer.full_name if order.customer else '—'}"
        f"{driver_line}\n"
        f"⏰ Time: {_now()}\n\n"
        f"⭐ Rating: {stars}  ({rating}/5)\n"
    )
    if feedback:
        text += f"💬 Feedback: {feedback}\n"

    await _broadcast(bot, {QUALITY_CONTROL_GROUP_ID, OPERATIONS_GROUP_ID}, text, parse_mode="Markdown")


async def notify_returned_products(bot: Bot, order, description: str, photo_file_id: str = None): # type: ignore
    driver_line = f"\n🚗 Driver: {order.driver_name}" if order.driver_name else ""
    text = (
        f"🔄 Returned Products Report\n\n"
        f"🆔 Order: `{order.order_number}`\n"
        f"🏨 Hotel: {order.hotel.name if order.hotel else '—'}\n"
        f"👤 Customer: {order.customer.full_name if order.customer else '—'}"
        f"{driver_line}\n"
        f"⏰ Time: {_now()}\n\n"
        f"📦 Returned Items:\n{description}"
    )

    targets = {QUALITY_CONTROL_GROUP_ID, ADMIN_ID}
    for target in targets:
        key = str(target).strip()
        if not key or key == "0":
            continue
        if photo_file_id:
            try:
                await bot.send_photo(
                    chat_id=int(key),
                    photo=photo_file_id,
                    caption=text,
                    parse_mode="Markdown",
                )
            except Exception as e:
                logging.error(f"QC photo to {key} failed: {e}")
                await _send(bot, key, text, parse_mode="Markdown")
        else:
            await _send(bot, key, text, parse_mode="Markdown")

async def notify_quality_control(bot: Bot, order, rating: int = None, feedback: str = None, returned_items: str = None): # type: ignore
    text = (
        f"🔒 Quality Control Report\n\n"
        f"🆔 Order: `{order.order_number}`\n"
        f"🏨 Hotel: {order.hotel.name if order.hotel else '—'}\n"
        f"👤 Customer: {order.customer.full_name if order.customer else '—'}\n"
        f"⏰ Time: {_now()}\n\n"
    )
    if rating is not None:
        text += f"⭐ Rating: {'⭐' * rating}  ({rating}/5)\n"
    if feedback:
        text += f"💬 Feedback: {feedback}\n"
    if returned_items:
        text += f"🔄 Returned Items:\n{returned_items}\n"

    await _send(bot, QUALITY_CONTROL_GROUP_ID, text, parse_mode="Markdown")
