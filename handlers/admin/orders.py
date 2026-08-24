import os
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.order import Order, OrderStatus
from database.repositories.order_repository import OrderRepository
from database.repositories.user_repository import UserRepository
from filters.role_filter import RoleFilter
from keyboards.admin_menu import admin_main_menu
from keyboards.admin import assign_driver_keyboard
from keyboards.customers import customer_menu

router = Router()
router.message.filter(RoleFilter(["admin"]))
router.callback_query.filter(RoleFilter(["admin"]))

ADMIN_ORDERS_BTNS = [
    "📥 New Orders", "📦 New Orders", "📥 አዳዲስ ትዕዛዞች", "📥 Ajajawwan Haaraa",
    "New Orders", "/orders", "/new_orders"
]

@router.message(F.text.in_(ADMIN_ORDERS_BTNS))
async def new_orders(message: Message, session: AsyncSession, lang: str = "en") -> None:
    repo = OrderRepository(session)
    orders = await repo.pending_orders()
    if not orders:
        no_orders_text = "✅ No pending orders."
        if lang == "am":
            no_orders_text = "✅ ምንም የሚጠብቁ አዳዲስ ትዕዛዞች የሉም።"
        elif lang == "om":
            no_orders_text = "✅ Ajajawwan haaraa eegaa jiran hin jiran."
        await message.answer(no_orders_text)
        return

    for order in orders:
        hotel    = order.hotel.name         if order.hotel    else "—"
        customer = order.customer.full_name if order.customer else "—"
        status_str = order.status.value if hasattr(order.status, "value") else str(order.status)
        text = (
            f"🆔 *{order.order_number}*\n"
            f"🏨 Hotel: *{hotel}*\n"
            f"👤 Customer: *{customer}*\n"
            f"📌 Status: *{status_str}*"
        )
        if getattr(order, "items", None):
            items_list = [
                f"  • {item.product.name} — {item.quantity} {item.product.unit}"
                for item in order.items
                if getattr(item, "product", None)
            ]
            if items_list:
                text += "\n\n🛒 *Products Ordered:*\n" + "\n".join(items_list)

        if order.file_path:
            text += f"\n📁 *Type*: Upload ({order.original_filename or 'file'})"
        if order.note:
            text += f"\n📝 *Note*: _{order.note}_"

        kb = assign_driver_keyboard(order.id)
        sent = False
        if order.telegram_file_id:
            try:
                if order.file_type == "photo":
                    await message.answer_photo(photo=order.telegram_file_id, caption=text, reply_markup=kb, parse_mode="Markdown")
                    sent = True
                else:
                    await message.answer_document(document=order.telegram_file_id, caption=text, reply_markup=kb, parse_mode="Markdown")
                    sent = True
            except Exception as e:
                logging.warning(f"Admin photo/doc via telegram_file_id failed: {e}")

        if not sent and order.file_path:
            full_path = os.path.join(os.getcwd(), order.file_path) if not os.path.isabs(order.file_path) else order.file_path
            if os.path.exists(full_path):
                file_input = FSInputFile(full_path)
                try:
                    if order.file_type == "photo":
                        await message.answer_photo(photo=file_input, caption=text, reply_markup=kb, parse_mode="Markdown")
                        sent = True
                    else:
                        await message.answer_document(document=file_input, caption=text, reply_markup=kb, parse_mode="Markdown")
                        sent = True
                except Exception as e:
                    logging.warning(f"Admin photo/doc via FSInputFile failed: {e}")

        if not sent:
            await message.answer(text, reply_markup=kb, parse_mode="Markdown")


from keyboards.delivery import delivery_menu
from keyboards.store_manager import store_manager_menu
from utils.i18n import t

@router.callback_query(F.data.startswith("approve_user:"))
async def approve_user(callback: CallbackQuery, session: AsyncSession) -> None:
    user_id = int(callback.data.split(":")[1]) # type: ignore
    repo = UserRepository(session)
    user = await repo.get(user_id)
    if not user:
        await callback.answer("User not found.", show_alert=True)
        return

    await repo.set_active(user, True)
    try:
        user_lang = getattr(user, "language", "en") or "en"
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        if role_val == "delivery":
            menu = delivery_menu(user_lang)
        elif role_val == "hotel":
            menu = store_manager_menu()
        elif role_val == "admin":
            menu = admin_main_menu()
        else:
            menu = customer_menu(user_lang)

        await callback.bot.send_message( # type: ignore
            chat_id=user.telegram_id,
            text=t("reg_success", user_lang, name=user.full_name),
            reply_markup=menu,
        )
    except Exception as e:
        logging.error(f"Failed to notify approved user {user.telegram_id}: {e}")

    await callback.message.edit_text( # type: ignore
        f"✅ Approved: *{user.full_name}*", parse_mode="Markdown"
    )
    await callback.answer("User approved!")


@router.callback_query(F.data.startswith("reject_user:"))
async def reject_user(callback: CallbackQuery, session: AsyncSession) -> None:
    user_id = int(callback.data.split(":")[1]) # type: ignore
    repo = UserRepository(session)
    user = await repo.get(user_id)
    if not user:
        await callback.answer("User not found.", show_alert=True)
        return

    telegram_id = user.telegram_id
    full_name   = user.full_name
    await repo.delete(user)

    try:
        await callback.bot.send_message( # type: ignore
            chat_id=telegram_id,
            text=(
                "❌ *Registration Rejected*\n\n"
                "Your registration has been rejected by the administrator.\n"
                "Please contact support if you believe this is an error."
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        logging.error(f"Failed to notify rejected user {telegram_id}: {e}")

    await callback.message.edit_text( # type: ignore
        f"❌ Rejected: *{full_name}*", parse_mode="Markdown"
    )
    await callback.answer("User rejected.")

@router.callback_query(F.data.startswith("admin_view_file:"))
async def admin_view_file(callback: CallbackQuery, session: AsyncSession) -> None:
    order_id = int(callback.data.split(":")[1]) # type: ignore
    repo  = OrderRepository(session)
    order = await repo.get_order(order_id)
    if not order or not order.file_path:
        await callback.answer("File not found.", show_alert=True)
        return
    full_path = os.path.join(os.getcwd(), order.file_path)
    if not os.path.exists(full_path):
        await callback.answer("File not found on disk.", show_alert=True)
        return

    await callback.answer("Sending document…")
    await callback.message.reply_document( # type: ignore
        FSInputFile(full_path),
        caption=f"📄 Order: {order.order_number}",
    )
