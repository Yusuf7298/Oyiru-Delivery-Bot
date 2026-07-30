import io
from datetime import datetime, timezone
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
_HEADER_FONT    = Font(bold=True, color="FFFFFF")
_HEADER_FILL    = PatternFill("solid", fgColor="1F4E79")
_ALT_FILL       = PatternFill("solid", fgColor="D9E1F2")
_CENTER         = Alignment(horizontal="center", vertical="center")


def _header_row(ws, headers: list[str]):
    ws.append(headers)
    for cell in ws[ws.max_row]:
        cell.font      = _HEADER_FONT
        cell.fill      = _HEADER_FILL
        cell.alignment = _CENTER


def _auto_width(ws):
    for col in ws.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=10)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 50)


def _fmt(dt) -> str:
    if dt is None:
        return ""
    if hasattr(dt, "strftime"):
        return dt.strftime("%Y-%m-%d %H:%M")
    return str(dt)


def _products_text(order) -> str:
    if order.file_path:
        fname = getattr(order, "original_filename", None) or "uploaded"
        return f"[File: {fname}]"
    if not order.items:
        return ""
    return "; ".join(
        f"{item.product.name} {item.quantity} {item.product.unit}"
        for item in order.items
        if item.product
    )

def generate_excel(orders: list, stats: dict) -> bytes:
    wb = openpyxl.Workbook()
    ws_orders = wb.active
    ws_orders.title = "Orders" # type: ignore
    ws_orders.freeze_panes = "A2" # type: ignore

    _header_row(ws_orders, [
        "Order Number", "Hotel", "Customer", "Phone",
        "Status", "Driver", "Note",
        "Submitted", "Accepted", "Delivered",
        "Rating", "Feedback",
        "Products / File",
    ])

    for i, order in enumerate(orders, start=2):
        hotel    = order.hotel.name    if order.hotel    else ""
        customer = order.customer.full_name if order.customer else ""
        phone    = order.customer.phone     if order.customer else ""
        row = [
            order.order_number,
            hotel,
            customer,
            phone,
            order.status.value,
            order.driver_name or "",
            order.note or "",
            _fmt(order.created_at),
            _fmt(order.accepted_at),
            _fmt(order.delivered_at),
            order.rating or "",
            order.feedback or "",
            _products_text(order),
        ]
        ws_orders.append(row) # type: ignore
        if i % 2 == 0:
            for cell in ws_orders[i]: # type: ignore
                cell.fill = _ALT_FILL

    _auto_width(ws_orders)
    ws_items = wb.create_sheet("Order Items")
    ws_items.freeze_panes = "A2"

    _header_row(ws_items, [
        "Order Number", "Hotel", "Customer",
        "Product", "Quantity", "Unit", "Submitted",
    ])

    for i, order in enumerate(orders, start=2):
        hotel    = order.hotel.name         if order.hotel    else ""
        customer = order.customer.full_name if order.customer else ""
        if not order.items:
            continue
        for item in order.items:
            if not item.product:
                continue
            row = [
                order.order_number,
                hotel,
                customer,
                item.product.name,
                item.quantity,
                item.product.unit,
                _fmt(order.created_at),
            ]
            ws_items.append(row)
            r = ws_items.max_row
            if r % 2 == 0:
                for cell in ws_items[r]:
                    cell.fill = _ALT_FILL

    _auto_width(ws_items)
    ws_sum = wb.create_sheet("Summary")
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    summary_rows = [
        ("Generated At", generated_at),
        ("", ""),
        ("── Period ──", ""),
        ("Orders Today",       stats.get("today", 0)),
        ("Orders This Week",   stats.get("week",  0)),
        ("Orders This Month",  stats.get("month", 0)),
        ("Total Orders",       stats.get("total", 0)),
        ("", ""),
        ("── By Status ──", ""),
        ("Delivered",          stats.get("delivered",   0)),
        ("Cancelled",          stats.get("cancelled",   0)),
        ("Pending / Active",   stats.get("pending",     0)),
        ("", ""),
        ("── Performance ──", ""),
        ("Avg Delivery Time",  f"{stats.get('avg_minutes', '—')} min"),
        ("", ""),
        ("── Top Hotels ──", ""),
    ]

    for rank, (name, cnt) in enumerate(stats.get("top_hotels", []), 1):
        summary_rows.append((f"  #{rank}  {name}", cnt))

    summary_rows += [("", ""), ("── Top Products ──", "")]
    for rank, (name, qty, unit) in enumerate(stats.get("top_products", []), 1):
        summary_rows.append((f"  #{rank}  {name}", f"{qty} {unit}"))

    summary_rows += [("", ""), ("── Top Drivers ──", "")]
    for rank, (name, cnt) in enumerate(stats.get("top_drivers", []), 1):
        summary_rows.append((f"  #{rank}  {name}", f"{cnt} deliveries"))

    for row in summary_rows:
        ws_sum.append(list(row))
        r = ws_sum.max_row
        if str(row[0]).startswith("──"):
            for cell in ws_sum[r]:
                cell.font = Font(bold=True)
                cell.fill = PatternFill("solid", fgColor="BDD7EE")

    ws_sum.column_dimensions["A"].width = 30
    ws_sum.column_dimensions["B"].width = 20
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()
