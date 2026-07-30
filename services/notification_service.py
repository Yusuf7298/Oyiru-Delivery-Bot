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


async def _send_order_media(
    bot: Bot,
    chat_id,
    caption: str,
    telegram_file_id: str = None,
    file_path: str = None,
    file_type: str = None,
    **kwargs
):
    if not chat_id:
        return
    try:
        cid = int(str(chat_id).strip())
        if cid == 0:
            return

        is_photo = (file_type == "photo")

        # 1. Try sending via telegram_file_id
        if telegram_file_id:
            try:
                if is_photo:
                    await bot.send_photo(chat_id=cid, photo=telegram_file_id, caption=caption, **kwargs)
                    return
                else:
                    await bot.send_document(chat_id=cid, document=telegram_file_id, caption=caption, **kwargs)
                    return
            except Exception as exc_tfid:
                logging.warning(f"send_photo/document with telegram_file_id to {cid} failed: {exc_tfid}. Trying local file_path.")

        # 2. Try sending via local file_path
        if file_path:
            full_path = os.path.join(os.getcwd(), file_path) if not os.path.isabs(file_path) else file_path
            if os.path.exists(full_path):
                from aiogram.types import FSInputFile
                file_input = FSInputFile(full_path)
                try:
                    if is_photo:
                        await bot.send_photo(chat_id=cid, photo=file_input, caption=caption, **kwargs)
                        return
                    else:
                        await bot.send_document(chat_id=cid, document=file_input, caption=caption, **kwargs)
                        return
                except Exception as exc_fp:
                    logging.warning(f"send_photo/document with FSInputFile to {cid} failed: {exc_fp}. Fallback to text.")

        # 3. Fallback to text message
        await bot.send_message(chat_id=cid, text=caption, **kwargs)
    except Exception as e:
        logging.error(f"Notification to {chat_id} failed: {e}")


async def _send(bot: Bot, chat_id, text: str, **kwargs):
    if not chat_id:
        return
    try:
        cid = int(str(chat_id).strip())
        if cid == 0:
            return
        await bot.send_message(chat_id=cid, text=text, **kwargs)
    except Exception as e:
        logging.error(f"Notification to {chat_id} failed: {e}")


async def _broadcast(bot: Bot, targets: set, text: str, **kwargs):
    seen = set()
    for t in targets:
        key = str(t).strip()
        if key and key != "0" and key not in seen:
            seen.add(key)
            await _send(bot, key, text, **kwargs)


async def _broadcast_order(
    bot: Bot,
    targets: set,
    text: str,
    telegram_file_id: str = None,
    file_path: str = None,
    file_type: str = None,
    **kwargs
):
    seen = set()
    for t in targets:
        key = str(t).strip()
        if key and key != "0" and key not in seen:
            seen.add(key)
            if telegram_file_id or file_path:
                await _send_order_media(
                    bot,
                    key,
                    caption=text,
                    telegram_file_id=telegram_file_id,
                    file_path=file_path,
                    file_type=file_type,
                    **kwargs
                )
            else:
                await _send(bot, key, text, **kwargs)

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
_STATUS_MSG = {
    OrderStatus.APPROVED:         "✅ Your order has been *approved* and is being prepared.",
    OrderStatus.PREPARING:        "👨‍🍳 Your order is now being *prepared*.",
    OrderStatus.PACKED:           "📦 Your order has been *packed* and is ready.",
    OrderStatus.OUT_FOR_DELIVERY: "🚛 Your order is *out for delivery*! The driver is on the way.",
    OrderStatus.DELIVERED:        "🎉 Your order has been *delivered*! Thank you for choosing Oyiru.",
    OrderStatus.CANCELLED:        "❌ Your order has been *cancelled*.",
}

async def notify_customer_status_update(bot: Bot, order, customer_telegram_id: int):
    status_msg = _STATUS_MSG.get(order.status, f"Your order status: {order.status.value}")
    driver_line = f"\n🚗 Driver: {order.driver_name}" if order.driver_name else ""

    text = (
        f"🔔 Order Update\n\n"
        f"🆔 Order: `{order.order_number}`\n"
        f"🏨 Hotel: {order.hotel.name if order.hotel else '—'}\n"
        f"📌 Status: {order.status.value}{driver_line}\n"
        f"⏰ Time: {_now()}\n\n"
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
