from __future__ import annotations
import os
import uuid
from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from database.repositories.user_repository import UserRepository
from database.repositories.order_repository import OrderRepository
from services.order_service import OrderService
from services.notification_service import notify_new_order as notify_admin_new_order
from states.order import OrderState
from keyboards.customer.order import upload_review_keyboard, skip_note_keyboard
from keyboards.customers import customer_menu, customer_reorder_menu
from filters.role_filter import RoleFilter

router = Router()
router.message.filter(RoleFilter(["customer"]))
router.callback_query.filter(RoleFilter(["customer"]))

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
ALLOWED_EXTENSIONS = {".pdf", ".xls", ".xlsx", ".doc", ".docx", ".txt"}
FILE_TYPE_LABELS = {
    "photo":    "🖼 Photo",
    "pdf":      "📄 PDF",
    "document": "📎 Document",
}


def _cleanup_file(path: str | None) -> None:
    if path:
        try:
            full = os.path.join(os.getcwd(), path) if not os.path.isabs(path) else path
            if os.path.exists(full):
                os.remove(full)
        except Exception as e:
            logger.warning(f"Failed to clean up file {path}: {e}")

# ── Entry ─────────────────────────────────────────────────────────────────────
@router.message(F.text.in_(["📄 Upload Photo", "📄 Upload Product List", "📄 Upload New Product List"]))
async def start_upload_order(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(order_method="upload")
    await message.answer(
        "📄 *Upload Your Product List*\n\n"
        "Send one of the following:\n"
        "  • 📷 Photo of your product list\n"
        "  • 📄 PDF document\n"
        "  • 📎 Excel / Word / Text file\n\n"
        "Type /cancel to go back.",
        parse_mode="Markdown",
    )
    await state.set_state(OrderState.waiting_for_document)

@router.callback_query(F.data == "upload_replace_file")
async def replace_file(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    _cleanup_file(data.get("file_path"))
    await state.update_data(file_path=None, telegram_file_id=None,file_type=None, original_filename=None, uploaded_at=None)
    await callback.message.answer( # type: ignore
        "📄 Send a replacement file:\n"
        "  • 📷 Photo\n  • 📄 PDF\n  • 📎 Excel / Word / Text",
        parse_mode="Markdown",
    )
    await state.set_state(OrderState.waiting_for_document)
    await callback.answer()

@router.message(
    OrderState.waiting_for_document,
    F.content_type.in_([ContentType.DOCUMENT, ContentType.PHOTO]),
)
async def handle_uploaded_file(message: Message, state: FSMContext) -> None:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    telegram_file_id: str | None = None
    file_type: str | None = None
    original_filename: str | None = None
    local_path: str | None = None
    if message.photo:
        photo = message.photo[-1]
        telegram_file_id = photo.file_id
        file_type = "photo"
        fname = f"photo_{message.from_user.id}_{uuid.uuid4().hex[:8]}.jpg" # type: ignore
        original_filename = fname
        local_path = os.path.join(UPLOAD_DIR, fname)
        try:
            file_info = await message.bot.get_file(photo.file_id) # type: ignore
            await message.bot.download_file(file_info.file_path, local_path) # type: ignore
        except Exception as e:
            logger.error(f"Photo download failed for user {message.from_user.id}: {e}") # type: ignore
            _cleanup_file(local_path)
            await message.answer("❌ Failed to download your photo. Please try again.")
            return

    elif message.document:
        doc = message.document
        raw_name = doc.file_name or "upload"
        ext = os.path.splitext(raw_name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            await message.answer(
                "❌ Unsupported file type.\n\n"
                "Please send one of:\n"
                "  • PDF (.pdf)\n  • Excel (.xls / .xlsx)\n"
                "  • Word (.doc / .docx)\n  • Text (.txt)\n  • Photo",
                parse_mode="Markdown",
            )
            return

        telegram_file_id = doc.file_id
        file_type = "pdf" if ext == ".pdf" else "document"
        original_filename = raw_name
        safe_name = f"{uuid.uuid4().hex}{ext}"
        local_path = os.path.join(UPLOAD_DIR, safe_name)
        try:
            file_info = await message.bot.get_file(doc.file_id) # type: ignore
            await message.bot.download_file(file_info.file_path, local_path) # type: ignore
        except Exception as e:
            logger.error(f"Document download failed for user {message.from_user.id}: {e}") # type: ignore
            _cleanup_file(local_path)
            await message.answer("❌ Failed to download your document. Please try again.")
            return

    if not telegram_file_id:
        await message.answer("❌ Could not process the file. Please try again.")
        return

    relative_path = os.path.relpath(local_path, os.getcwd()).replace("\\", "/") # type: ignore
    uploaded_at = datetime.now(timezone.utc).isoformat()
    await state.update_data(
        file_path=relative_path,
        telegram_file_id=telegram_file_id,
        file_type=file_type,
        original_filename=original_filename,
        uploaded_at=uploaded_at,
    )

    await message.answer(
        f"✅ File received: {original_filename}\n\n"
        "📝 Optional Note\n"
        "Add a note for this order _(e.g. Urgent / Deliver before 9 AM)_\n\n"
        "Or tap ⏭ Skip Note to continue.",
        reply_markup=skip_note_keyboard(),
        parse_mode="Markdown",
    )
    await state.set_state(OrderState.entering_note)


@router.message(OrderState.waiting_for_document, F.text.in_(["/cancel", "cancel", "❌ Cancel"]))
async def cancel_upload(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    _cleanup_file(data.get("file_path"))
    await state.clear()
    await message.answer("❌ Upload cancelled.", reply_markup=customer_menu())


@router.message(OrderState.waiting_for_document)
async def invalid_upload(message: Message) -> None:
    await message.answer(
        "❌ Please send a photo or document file, or type /cancel to go back.",
        parse_mode="Markdown",
    )

async def show_upload_review(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(
        message.from_user.id if message.from_user else message.chat.id
    )
    hotel_name = customer.hotel.name if (customer and customer.hotel) else "—"
    file_type = data.get("file_type", "document")
    original_filename = data.get("original_filename", "—")
    telegram_file_id = data.get("telegram_file_id")
    file_path = data.get("file_path")
    note = data.get("note")
    file_label = FILE_TYPE_LABELS.get(file_type, "📎 File")

    text = (
        "📋 Order Review\n\n"
        f"🆔 Order Number: _Will be assigned on submit_\n"
        f"🏨 Hotel: {hotel_name}\n"
        f"👤 Customer: {customer.full_name if customer else '—'}\n\n"
        f"📁 Uploaded File:\n"
        f"  {file_label}  —  `{original_filename}`\n\n"
        f"📝 Note: {note or '—'}"
    )

    sent = False
    if telegram_file_id:
        try:
            if file_type == "photo":
                await message.answer_photo(
                    photo=telegram_file_id,
                    caption=text,
                    reply_markup=upload_review_keyboard(),
                    parse_mode="Markdown",
                )
                sent = True
            else:
                await message.answer_document(
                    document=telegram_file_id,
                    caption=text,
                    reply_markup=upload_review_keyboard(),
                    parse_mode="Markdown",
                )
                sent = True
        except Exception as e:
            logger.warning(f"Sending photo/doc review via telegram_file_id failed: {e}")

    if not sent and file_path:
        full_path = os.path.join(os.getcwd(), file_path) if not os.path.isabs(file_path) else file_path
        if os.path.exists(full_path):
            from aiogram.types import FSInputFile
            file_input = FSInputFile(full_path)
            try:
                if file_type == "photo":
                    await message.answer_photo(
                        photo=file_input,
                        caption=text,
                        reply_markup=upload_review_keyboard(),
                        parse_mode="Markdown",
                    )
                    sent = True
                else:
                    await message.answer_document(
                        document=file_input,
                        caption=text,
                        reply_markup=upload_review_keyboard(),
                        parse_mode="Markdown",
                    )
                    sent = True
            except Exception as e:
                logger.warning(f"Sending photo/doc review via FSInputFile failed: {e}")

    if not sent:
        await message.answer(text, reply_markup=upload_review_keyboard(), parse_mode="Markdown")

    await state.set_state(OrderState.reviewing_uploaded_order)


@router.callback_query(OrderState.reviewing_uploaded_order, F.data == "upload_edit_note")
async def upload_edit_note(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer( # type: ignore
        "📝 Enter a new note, or tap ⏭ Skip Note to remove it:",
        reply_markup=skip_note_keyboard(),
        parse_mode="Markdown",
    )
    await state.set_state(OrderState.entering_note)
    await callback.answer()

@router.callback_query(OrderState.reviewing_uploaded_order, F.data == "upload_submit")
async def submit_upload_order(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    user_repo = UserRepository(session)
    customer = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not customer or not customer.hotel_id:
        await callback.answer("❌ You are not associated with a hotel.", show_alert=True)
        return

    await callback.answer("Order submitted!")

    order_service = OrderService(session)
    order = await order_service.create_order(
        customer_id=customer.id,
        hotel_id=customer.hotel_id,
        note=data.get("note"), # type: ignore
        file_path=data.get("file_path"), # type: ignore
        telegram_file_id=data.get("telegram_file_id"), # type: ignore
        file_type=data.get("file_type"), # type: ignore
        original_filename=data.get("original_filename"), # type: ignore
        uploaded_at=data.get("uploaded_at"), # type: ignore
    )
    await state.clear()

    try:
        await notify_admin_new_order(callback.bot, order, customer) # type: ignore
    except Exception as exc:
        logger.error(f"Notification failed for {order.order_number}: {exc}")

    last = await OrderRepository(session).get_last_order(customer.id)
    menu = customer_reorder_menu() if last else customer_menu()
    file_label = FILE_TYPE_LABELS.get(order.file_type or "", "📎 File")

    from utils.helpers import safe_edit_text_or_caption
    await safe_edit_text_or_caption(
        callback,
        f"✅ Order Submitted!\n\n"
        f"🆔 Order Number: `{order.order_number}`\n"
        f"🏨 Hotel: {customer.hotel.name if customer.hotel else '—'}\n"
        f"📁 File: {file_label} — `{order.original_filename or '—'}`\n"
        f"📌 Status: {order.status.value}",
        parse_mode="Markdown",
    )
    await callback.message.answer("Choose an option:", reply_markup=menu) # type: ignore
