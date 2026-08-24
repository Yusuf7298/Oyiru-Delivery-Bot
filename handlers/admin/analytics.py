import io
from aiogram import Router, F
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

def _stats_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Export Excel", callback_data="stats_export_excel")
    builder.button(text="🔄 Refresh",      callback_data="stats_refresh")
    builder.adjust(2)
    return builder.as_markup()


def _bar(value: int, max_value: int, width: int = 10) -> str:
    if max_value == 0:
        return "░" * width
    filled = round(value / max_value * width)
    return "█" * filled + "░" * (width - filled)

async def _gather_stats(repo: AnalyticsRepository) -> dict:
    """Run all analytics queries and return a stats dict."""
    today   = await repo.orders_today()
    week    = await repo.orders_this_week()
    month   = await repo.orders_this_month()
    total   = await repo.orders_total()

    by_status   = await repo.count_by_status()
    delivered   = by_status.get(OrderStatus.DELIVERED.value,   0)
    cancelled   = by_status.get(OrderStatus.CANCELLED.value,   0)
    submitted   = by_status.get(OrderStatus.SUBMITTED.value,   0)
    approved    = by_status.get(OrderStatus.APPROVED.value,    0)
    preparing   = by_status.get(OrderStatus.PREPARING.value,   0)
    packed      = by_status.get(OrderStatus.PACKED.value,      0)
    out_del     = by_status.get(OrderStatus.OUT_FOR_DELIVERY.value, 0)
    pending     = submitted + approved + preparing + packed + out_del

    avg_minutes = await repo.avg_delivery_minutes()
    top_hotels  = await repo.top_hotels(5)
    top_products = await repo.top_products(5)
    top_drivers  = await repo.top_drivers(5)

    return dict(
        today=today, week=week, month=month, total=total,
        delivered=delivered, cancelled=cancelled, pending=pending,
        avg_minutes=avg_minutes,
        top_hotels=top_hotels,
        top_products=top_products,
        top_drivers=top_drivers,
    )


def _format_stats(s: dict) -> str:
    lines = ["📊 *Oyirubot Analytics Dashboard*\n"]
    lines.append("📅 *Orders by Period*")
    lines.append(f"  Today:      *{s['today']}*")
    lines.append(f"  This Week:  *{s['week']}*")
    lines.append(f"  This Month: *{s['month']}*")
    lines.append(f"  All Time:   *{s['total']}*\n")

    # Status breakdown
    total = max(s['total'], 1)
    lines.append("📌 *Order Status Breakdown*")
    lines.append(f"  ✅ Delivered: *{s['delivered']}*  {_bar(s['delivered'], total)}")
    lines.append(f"  ❌ Cancelled: *{s['cancelled']}*  {_bar(s['cancelled'], total)}")
    lines.append(f"  ⏳ Pending:   *{s['pending']}*   {_bar(s['pending'],   total)}\n")

    # Avg delivery time
    avg = s["avg_minutes"]
    if avg is not None:
        h, m = divmod(int(avg), 60)
        time_str = f"{h}h {m}m" if h else f"{m} min"
        lines.append(f"⏱ *Avg Delivery Time*: {time_str}\n")
    else:
        lines.append("⏱ *Avg Delivery Time*: —\n")

    # Top Hotels
    lines.append("🏨 *Top Hotels*")
    if s["top_hotels"]:
        max_cnt = s["top_hotels"][0][1]
        for i, (name, cnt) in enumerate(s["top_hotels"], 1):
            lines.append(f"  {i}. {name}  —  *{cnt}* orders  {_bar(cnt, max_cnt, 8)}")
    else:
        lines.append("  No data yet.")
    lines.append("")

    # Top Products
    lines.append("📦 *Top Products*")
    if s["top_products"]:
        max_qty = s["top_products"][0][1]
        for i, (name, qty, unit) in enumerate(s["top_products"], 1):
            lines.append(f"  {i}. {name}  —  *{qty:.0f} {unit}*  {_bar(qty, max_qty, 8)}")
    else:
        lines.append("  No data yet.")
    lines.append("")

    # Top Drivers
    lines.append("🚗 *Top Drivers*")
    if s["top_drivers"]:
        max_cnt = s["top_drivers"][0][1]
        for i, (name, cnt) in enumerate(s["top_drivers"], 1):
            lines.append(f"  {i}. {name}  —  *{cnt}* deliveries  {_bar(cnt, max_cnt, 8)}")
    else:
        lines.append("  No data yet.")

    return "\n".join(lines)

STATS_MENU_BTNS = ["📊 Statistics", "📊 ስታቲስቲክስ", "📊 Istaatistiksii", "/stats"]

@router.message(F.text.in_(STATS_MENU_BTNS))
async def show_statistics(message: Message, session: AsyncSession):
    repo  = AnalyticsRepository(session)
    stats = await _gather_stats(repo)
    text  = _format_stats(stats)
    await message.answer(text, reply_markup=_stats_keyboard(), parse_mode="Markdown")


@router.callback_query(F.data == "stats_refresh")
async def refresh_statistics(callback: CallbackQuery, session: AsyncSession):
    repo  = AnalyticsRepository(session)
    stats = await _gather_stats(repo)
    text  = _format_stats(stats)
    try:
        await callback.message.edit_text( # type: ignore
            text, reply_markup=_stats_keyboard(), parse_mode="Markdown"
        )
    except Exception:
        pass 
    await callback.answer("Refreshed ✅")


@router.callback_query(F.data == "stats_export_excel")
async def export_excel(callback: CallbackQuery, session: AsyncSession):
    await callback.answer("Generating Excel…")
    await callback.message.answer("⏳ Generating Excel export, please wait…") # type: ignore

    try:
        repo   = AnalyticsRepository(session)
        stats  = await _gather_stats(repo)
        orders = await repo.all_orders_for_export()

        xlsx_bytes = generate_excel(orders, stats)

        from datetime import datetime, timezone
        ts       = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        filename = f"oyiru_analytics_{ts}.xlsx"

        await callback.message.answer_document( # type: ignore
            document=BufferedInputFile(xlsx_bytes, filename=filename),
            caption=(
                f"📊 *Oyiru Analytics Export*\n"
                f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
                f"Total orders: {stats['total']}"
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Excel export failed: {e}")
        await callback.message.answer(f"❌ Export failed: {e}") # type: ignore
