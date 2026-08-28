import datetime
import logging
import os
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.models.order import OrderStatus
try:
    from config.settings import ( # type: ignore
        ADMIN_ID,
        SUPER_ADMIN_IDS,
        ORDERS_GROUP_ID,
        STORE_MANAGERS_GROUP_ID,
        INVENTORY_GROUP_ID,
        SALES_MANAGERS_GROUP_ID,
        QUALITY_CONTROL_GROUP_ID,
        OPERATIONS_GROUP_ID,
    )
except Exception:
    ADMIN_ID                 = os.getenv("ADMIN_ID", "8223004316")
    SUPER_ADMIN_IDS          = {str(ADMIN_ID).strip(), "7269164159"}
    ORDERS_GROUP_ID          = os.getenv("ORDERS_GROUP_ID",          ADMIN_ID)
    STORE_MANAGERS_GROUP_ID  = os.getenv("STORE_MANAGERS_GROUP_ID",  ADMIN_ID)
    INVENTORY_GROUP_ID       = os.getenv("INVENTORY_GROUP_ID",       ADMIN_ID)
    SALES_MANAGERS_GROUP_ID  = os.getenv("SALES_MANAGERS_GROUP_ID",  ADMIN_ID)
    QUALITY_CONTROL_GROUP_ID = os.getenv("QUALITY_CONTROL_GROUP_ID", ADMIN_ID)
    OPERATIONS_GROUP_ID      = os.getenv("OPERATIONS_GROUP_ID",      ADMIN_ID)

def _now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

def _products_block(order) -> str:
    if getattr(order, "file_path", None) or getattr(order, "telegram_file_id", None):
        fname = getattr(order, "original_filename", None) or "uploaded file"
        ftype = (getattr(order, "file_type", None) or "document").title()
        return f"📎 {ftype}: `{fname}`"
    try:
        items = getattr(order, "items", []) or []
        lines = []
        for item in items:
            pname = (item.product.name if getattr(item, "product", None) else getattr(item, "product_name", None)) or "Item"
            punit = (getattr(item.product, "unit", None) if getattr(item, "product", None) else getattr(item, "unit", "KG")) or "KG"
            qty = getattr(item, "quantity", 0)
            lines.append(f"  • {pname} — {qty} {punit}")
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

    status_obj = getattr(order, "status", None)
    status_val = status_obj.value if hasattr(status_obj, "value") else str(status_obj or "Submitted")
    dp = getattr(order, "delivery_partner", None)
    dname = getattr(order, "driver_name", None) or (dp.full_name if dp else None)
    dphone = (dp.phone if dp and getattr(dp, "phone", None) else None)
    driver_str = f"\n🚗 Driver: {dname}" if dname else ""
    if dphone:
        driver_str += f"\n📞 Driver Phone: `{dphone}`"
    note = f"\n📝 Note: {order.note}" if getattr(order, "note", None) else ""
    return (
        f"🆔 Order: `{order.order_number}`\n"
        f"🏨 Hotel: {hotel}\n"
        f"👤 Customer: {cust}\n"
        f"📌 Status: {status_val}{driver_str}{note}\n"
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
    chat_id,
    caption: str,
    telegram_file_id: str = None,
    file_path: str = None,
    file_type: str = None,
    **kwargs
):
    ids = _extract_chat_ids(chat_id)
    if not ids:
        return

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

    for cid in ids:
        try:
            # 1. Try sending via telegram_file_id
            if telegram_file_id:
                try:
                    if is_photo:
                        await bot.send_photo(chat_id=cid, photo=telegram_file_id, caption=safe_caption, **kwargs)
                    else:
                        await bot.send_document(chat_id=cid, document=telegram_file_id, caption=safe_caption, **kwargs)
                    if overflow_text:
                        await bot.send_message(chat_id=cid, text=overflow_text, **kwargs)
                    continue
                except Exception as exc_tfid:
                    err_s = str(exc_tfid).lower()
                    if "can't parse entities" in err_s or "entity" in err_s:
                        # Retry without parse_mode
                        kw_no_parse = dict(kwargs)
                        kw_no_parse.pop("parse_mode", None)
                        if is_photo:
                            await bot.send_photo(chat_id=cid, photo=telegram_file_id, caption=safe_caption, **kw_no_parse)
                        else:
                            await bot.send_document(chat_id=cid, document=telegram_file_id, caption=safe_caption, **kw_no_parse)
                        continue
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
                        continue
                    except Exception as exc_fp:
                        err_s = str(exc_fp).lower()
                        if "can't parse entities" in err_s or "entity" in err_s:
                            kw_no_parse = dict(kwargs)
                            kw_no_parse.pop("parse_mode", None)
                            if is_photo:
                                await bot.send_photo(chat_id=cid, photo=file_input, caption=safe_caption, **kw_no_parse)
                            else:
                                await bot.send_document(chat_id=cid, document=file_input, caption=safe_caption, **kw_no_parse)
                            continue
                        logging.debug(f"send_photo/document with FSInputFile to {cid} failed: {exc_fp}. Fallback to text.")

            # 3. Fallback to text message if media could not be sent
            try:
                await bot.send_message(chat_id=cid, text=caption, **kwargs)
            except Exception as e_txt:
                err_s = str(e_txt).lower()
                if "can't parse entities" in err_s or "entity" in err_s:
                    kw_no_parse = dict(kwargs)
                    kw_no_parse.pop("parse_mode", None)
                    await bot.send_message(chat_id=cid, text=caption, **kw_no_parse)
                else:
                    raise
        except Exception as e:
            err_msg = str(e)
            if "chat not found" in err_msg.lower():
                logging.info(f"Notification skipped for chat {cid} (bot not in chat or channel not created yet).")
            elif "blocked by the user" in err_msg.lower():
                logging.info(f"Notification skipped: User {cid} has blocked the bot.")
            else:
                logging.warning(f"Notification to {cid} failed: {e}")


async def _send(bot: Bot, chat_id, text: str, **kwargs):
    ids = _extract_chat_ids(chat_id)
    if not ids:
        return
    for cid in ids:
        try:
            await bot.send_message(chat_id=cid, text=text, **kwargs)
        except Exception as e:
            err_msg = str(e)
            if "can't parse entities" in err_msg.lower() or "entity" in err_msg.lower():
                try:
                    kw = dict(kwargs)
                    kw.pop("parse_mode", None)
                    await bot.send_message(chat_id=cid, text=text, **kw)
                    continue
                except Exception as e2:
                    err_msg = str(e2)
            if "chat not found" in err_msg.lower():
                logging.info(f"Notification skipped for chat {cid} (bot not in chat or channel not created yet).")
            elif "blocked by the user" in err_msg.lower():
                logging.info(f"Notification skipped: User {cid} has blocked the bot.")
            else:
                logging.warning(f"Notification to {cid} failed: {e}")


async def _broadcast(bot: Bot, targets, text: str, **kwargs):
    await _send(bot, targets, text, **kwargs)


async def _broadcast_order(
    bot: Bot,
    targets,
    text: str,
    telegram_file_id: str = None,
    file_path: str = None,
    file_type: str = None,
    **kwargs
):
    await _send_order_media(
        bot,
        targets,
        caption=text,
        telegram_file_id=telegram_file_id,
        file_path=file_path,
        file_type=file_type,
        **kwargs
    )

async def notify_new_order(bot: Bot, order, customer):
    text = (
        "🆕 New Order Submitted\n\n"
        + _order_detail_block(order, customer)
    )
    targets = {
        *SUPER_ADMIN_IDS,
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

    status_obj = getattr(order, "status", None)
    if hasattr(status_obj, "value"):
        status_val = status_obj.value
    else:
        status_val = str(status_obj or "Updated")

    status_str_lower = status_val.lower().replace(" ", "_")
    status_key = None
    for enum_status, k in _STATUS_KEY.items():
        if (
            status_obj == enum_status
            or enum_status.value.lower() == status_val.lower()
            or enum_status.name.lower() == status_str_lower
        ):
            status_key = k
            break

    if status_key:
        status_msg = t(status_key, lang)
    else:
        status_msg = f"Your order status: {status_val}"

    driver_info = ""
    dp = getattr(order, "delivery_partner", None)
    dname = getattr(order, "driver_name", None) or (dp.full_name if dp else None)
    dphone = (dp.phone if dp and getattr(dp, "phone", None) else None)
    if dname:
        driver_info += f"\n🚗 Driver: {dname}"
    if dphone:
        driver_info += f"\n📞 Driver Phone: `{dphone}`"

    hotel_name = order.hotel.name if getattr(order, "hotel", None) else "—"

    text = (
        f"🔔 Order Update\n\n"
        f"🆔 Order: `{order.order_number}`\n"
        f"🏨 Hotel: {hotel_name}\n"
        f"📌 Status: {status_val}"
        f"{driver_info}\n"
        f"⏰ Time: {_now()}\n\n"
        f"{status_msg}"
    )

    reply_markup = None
    is_delivered = (
        status_obj == OrderStatus.DELIVERED
        or status_val.lower() in ("delivered", "status_delivered")
    )
    if is_delivered:
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
        targets = {
            *SUPER_ADMIN_IDS,
            ADMIN_ID,
            ORDERS_GROUP_ID,
            STORE_MANAGERS_GROUP_ID,
            SALES_MANAGERS_GROUP_ID
        }
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
    status_obj = getattr(order, "status", None)
    status_val = status_obj.value if hasattr(status_obj, "value") else str(status_obj or "Cancelled")
    hotel_name = order.hotel.name if getattr(order, "hotel", None) else "—"
    text = (
        f"❌ Order Rejected\n\n"
        f"🆔 Order: `{order.order_number}`\n"
        f"🏨 Hotel: {hotel_name}\n"
        f"📌 Status: {status_val}\n"
        f"⏰ Time: {_now()}\n\n"
        f"📋 Reason: {reason}"
    )
    await _send(bot, customer_telegram_id, text, parse_mode="Markdown")

async def notify_user_approved(bot: Bot, user):
    """Notify a user that their registration/account has been approved."""
    try:
        user_lang = getattr(user, "language", "en") or "en"
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        if role_val in ("driver", "delivery"):
            from keyboards.delivery import delivery_menu
            menu = delivery_menu(user_lang)
        elif role_val in ("hotel_admin", "hotel"):
            from keyboards.store_manager import hotel_admin_menu
            menu = hotel_admin_menu(user_lang)
        elif role_val == "store_manager":
            from keyboards.store_manager import store_manager_menu
            menu = store_manager_menu(user_lang)
        elif role_val == "admin":
            from keyboards.admin_menu import admin_main_menu
            menu = admin_main_menu(user_lang)
        else:
            from keyboards.customers import customer_menu
            menu = customer_menu(user_lang)

        msg_text = t("reg_success", user_lang, name=user.full_name)
        await _send(bot, user.telegram_id, msg_text, reply_markup=menu)
    except Exception as e:
        logging.error(f"Failed to notify approved user {getattr(user, 'telegram_id', 'unknown')}: {e}")

async def notify_user_rejected(bot: Bot, telegram_id: int, full_name: str = "", reason: str = None):
    """Notify a user that their registration has been rejected."""
    try:
        reason_str = f"\n\n📋 Reason: {reason}" if reason else ""
        text = (
            "❌ *Registration Rejected*\n\n"
            "Your registration has been rejected by the administrator.\n"
            "Please contact support if you believe this is an error."
            + reason_str
        )
        await _send(bot, telegram_id, text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Failed to notify rejected user {telegram_id}: {e}")

async def notify_sales_managers(bot: Bot, order, action: str):
    text = (
        f"📊 Sales Monitor — {action}\n\n"
        + _order_detail_block(order)
    )
    targets = {*SUPER_ADMIN_IDS, ADMIN_ID, SALES_MANAGERS_GROUP_ID}
    await _broadcast_order(
        bot,
        targets,
        text,
        telegram_file_id=getattr(order, "telegram_file_id", None),
        file_path=getattr(order, "file_path", None),
        file_type=getattr(order, "file_type", None),
        parse_mode="Markdown",
    )

async def notify_operations(bot: Bot, order, rating: int, feedback: str = None): # type: ignore
    import html
    stars = "⭐" * rating + "☆" * (5 - rating)
    driver_name = getattr(order, "driver_name", None)
    driver_line = f"\n🚗 <b>Driver</b>: {html.escape(str(driver_name))}" if driver_name else ""
    hotel_name = order.hotel.name if getattr(order, "hotel", None) else "—"
    cust_name = order.customer.full_name if getattr(order, "customer", None) else "—"
    text = (
        f"📋 <b>Customer Feedback Report</b>\n\n"
        f"🆔 <b>Order</b>: <code>{html.escape(str(order.order_number))}</code>\n"
        f"🏨 <b>Hotel</b>: {html.escape(str(hotel_name))}\n"
        f"👤 <b>Customer</b>: {html.escape(str(cust_name))}"
        f"{driver_line}\n"
        f"⏰ <b>Time</b>: {_now()}\n\n"
        f"⭐ <b>Rating</b>: {stars}  ({rating}/5)\n"
    )
    if feedback:
        text += f"💬 <b>Feedback</b>: {html.escape(str(feedback))}\n"

    targets = {*SUPER_ADMIN_IDS, ADMIN_ID, QUALITY_CONTROL_GROUP_ID, OPERATIONS_GROUP_ID}
    await _broadcast(bot, targets, text, parse_mode="HTML")


async def notify_returned_products(bot: Bot, order, description: str, photo_file_id: str = None, customer = None): # type: ignore
    import html
    order_num = getattr(order, "order_number", "—") if order else "—"
    hotel_name = order.hotel.name if order and getattr(order, "hotel", None) else "—"
    if not customer and order and getattr(order, "customer", None):
        customer = order.customer
    cust_name = customer.full_name if customer else "—"

    driver_name = getattr(order, "driver_name", None) if order else None
    dp = getattr(order, "delivery_partner", None) if order else None
    if not driver_name and dp:
        driver_name = dp.full_name
    driver_phone = getattr(order, "driver_phone", None) if order else (dp.phone if dp else None)
    driver_line = f"\n🚗 <b>Driver</b>: {html.escape(str(driver_name))}" if driver_name else ""
    if driver_phone:
        driver_line += f" (<code>{html.escape(str(driver_phone))}</code>)"

    text = (
        f"🔄 <b>Returned Products Report</b>\n\n"
        f"🆔 <b>Order</b>: <code>{html.escape(str(order_num))}</code>\n"
        f"🏨 <b>Hotel</b>: {html.escape(str(hotel_name))}\n"
        f"👤 <b>Customer</b>: {html.escape(str(cust_name))}"
        f"{driver_line}\n"
        f"⏰ <b>Time</b>: {_now()}\n\n"
        f"📦 <b>Returned Items / Reason</b>:\n{html.escape(str(description))}"
    )

    targets = _extract_chat_ids({*SUPER_ADMIN_IDS, ADMIN_ID, QUALITY_CONTROL_GROUP_ID, OPERATIONS_GROUP_ID})
    for cid in targets:
        if photo_file_id:
            try:
                caption_safe = text if len(text) <= 1024 else text[:1020] + "…"
                await bot.send_photo(
                    chat_id=cid,
                    photo=photo_file_id,
                    caption=caption_safe,
                    parse_mode="HTML",
                )
                continue
            except Exception as e:
                logging.warning(f"QC photo to {cid} failed: {e}")

        await _send(bot, cid, text, parse_mode="HTML")

async def notify_quality_control(
    bot: Bot,
    order,
    rating: int = None,
    feedback: str = None,
    returned_items: str = None,
    photo_file_id: str = None,
    customer = None,
):
    import html
    order_num = getattr(order, "order_number", "—") if order else "—"
    hotel_name = order.hotel.name if order and getattr(order, "hotel", None) else "—"
    if not customer and order and getattr(order, "customer", None):
        customer = order.customer
    cust_name = customer.full_name if customer else "—"

    driver_name = getattr(order, "driver_name", None) if order else None
    dp = getattr(order, "delivery_partner", None) if order else None
    if not driver_name and dp:
        driver_name = dp.full_name
    driver_phone = getattr(order, "driver_phone", None) if order else (dp.phone if dp else None)
    driver_line = f"\n🚗 <b>Driver</b>: {html.escape(str(driver_name))}" if driver_name else ""
    if driver_phone:
        driver_line += f" (<code>{html.escape(str(driver_phone))}</code>)"

    text = (
        f"🔒 <b>Quality Control Report</b>\n\n"
        f"🆔 <b>Order</b>: <code>{html.escape(str(order_num))}</code>\n"
        f"🏨 <b>Hotel</b>: {html.escape(str(hotel_name))}\n"
        f"👤 <b>Customer</b>: {html.escape(str(cust_name))}"
        f"{driver_line}\n"
        f"⏰ <b>Time</b>: {_now()}\n\n"
    )
    if rating is not None:
        stars_filled = "⭐" * rating
        stars_empty = "☆" * (5 - rating)
        text += f"⭐ <b>Rating</b>: {stars_filled}{stars_empty} ({rating}/5)\n"
    if feedback:
        text += f"💬 <b>Feedback</b>: {html.escape(str(feedback))}\n"
    if returned_items:
        text += f"🔄 <b>Returned Items</b>:\n{html.escape(str(returned_items))}\n"

    targets = _extract_chat_ids({*SUPER_ADMIN_IDS, ADMIN_ID, QUALITY_CONTROL_GROUP_ID, OPERATIONS_GROUP_ID})
    for cid in targets:
        if photo_file_id:
            try:
                caption_safe = text if len(text) <= 1024 else text[:1020] + "…"
                await bot.send_photo(
                    chat_id=cid,
                    photo=photo_file_id,
                    caption=caption_safe,
                    parse_mode="HTML",
                )
                continue
            except Exception as e:
                logging.warning(f"QC photo send to {cid} failed: {e}")

        await _send(bot, cid, text, parse_mode="HTML")

