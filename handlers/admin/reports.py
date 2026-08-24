from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from database.repositories.analytics_repository import AnalyticsRepository
from database.models.order import OrderStatus
from filters.role_filter import RoleFilter
from utils.excel_export import generate_excel

router = Router()
router.message.filter(RoleFilter(["admin"]))
router.callback_query.filter(RoleFilter(["admin"]))

async def send_excel_report(target, session: AsyncSession):
    try:
        repo = AnalyticsRepository(session)
        orders = await repo.all_orders_for_export()
        returns_map = await repo.returns_map_for_export()
        
        today = await repo.orders_today()
        week = await repo.orders_this_week()
        month = await repo.orders_this_month()
        total = await repo.orders_total()
        stats = {"today": today, "week": week, "month": month, "total": total}

        xlsx_bytes = generate_excel(orders, stats, returns_map)

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        filename = f"oyirubot_superadmin_weekly_report_{ts}.xlsx"

        doc = BufferedInputFile(xlsx_bytes, filename=filename)
        caption = (
            "📊 *Oyirubot Super Admin Weekly Report*\n\n"
            f"📅 Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"📦 Total Orders Exported: *{len(orders)}*\n\n"
            "Included Sheets:\n"
            "1️⃣ *Hotel Delivery & Returns* (Hotel name, ordered person, product vs kg/day, returns)\n"
            "2️⃣ *Delivery Partners Report* (Driver name, product vs kg, destination hotel, returns)\n"
            "3️⃣ *Store Managers Weekly Report* (Delivered & returned products weekly summary)\n"
            "4️⃣ *Master Orders Overview* (Full system breakdown)"
        )
        if isinstance(target, CallbackQuery):
            await target.message.answer_document(doc, caption=caption, parse_mode="Markdown")
        else:
            await target.answer_document(doc, caption=caption, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Excel report export error: {e}")
        error_msg = f"❌ Export failed: {e}"
        if isinstance(target, CallbackQuery):
            await target.message.answer(error_msg)
        else:
            await target.answer(error_msg)

ADMIN_EXPORT_BTNS = ["📊 Export Excel Report", "📊 Export Data", "📊 Export Excel", "📊 ኤክሴል አውርድ", "📊 Excel Buusi"]

@router.message(F.text.in_(ADMIN_EXPORT_BTNS))
@router.message(Command("export"))
@router.message(Command("export_excel"))
async def handle_export_command(message: Message, session: AsyncSession):
    await message.answer("⏳ Generating comprehensive Super Admin Excel report, please wait...")
    await send_excel_report(message, session)

@router.callback_query(F.data == "stats_export_excel")
async def handle_export_callback(callback: CallbackQuery, session: AsyncSession):
    await callback.answer("Generating Excel report...")
    await callback.message.answer("⏳ Generating comprehensive Super Admin Excel report, please wait...")
    await send_excel_report(callback, session)
