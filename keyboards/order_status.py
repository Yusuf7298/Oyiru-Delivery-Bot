from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models.order import OrderStatus

def order_status_keyboard(order):
    builder = InlineKeyboardBuilder()

    if order.status == OrderStatus.SUBMITTED:
        builder.button(
            text="✅ Approve Order",
            callback_data=f"approve_prompt:{order.id}",
        )
        builder.button(
            text="❌ Reject Order",
            callback_data=f"status:{order.id}:CANCELLED",
        )

    elif order.status == OrderStatus.APPROVED:
        builder.button(
            text="👨‍🍳 Start Preparing",
            callback_data=f"status:{order.id}:PREPARING",
        )
        builder.button(
            text="❌ Cancel Order",
            callback_data=f"status:{order.id}:CANCELLED",
        )

    elif order.status == OrderStatus.PREPARING:
        builder.button(
            text="📦 Mark Packed",
            callback_data=f"status:{order.id}:PACKED",
        )
        builder.button(
            text="❌ Cancel Order",
            callback_data=f"status:{order.id}:CANCELLED",
        )

    elif order.status == OrderStatus.PACKED:
        builder.button(
            text="🚛 Send Out for Delivery",
            callback_data=f"status:{order.id}:OUT_FOR_DELIVERY",
        )
        builder.button(
            text="❌ Cancel Order",
            callback_data=f"status:{order.id}:CANCELLED",
        )

    elif order.status == OrderStatus.OUT_FOR_DELIVERY:
        builder.button(
            text="✅ Mark Delivered",
            callback_data=f"status:{order.id}:DELIVERED",
        )
        builder.button(
            text="❌ Cancel Order",
            callback_data=f"status:{order.id}:CANCELLED",
        )

    # Add file download option if file exists
    if order.file_path:
        builder.button(
            text="📄 View Document",
            callback_data=f"hotel_view_file:{order.id}"
        )

    builder.adjust(1)
    return builder.as_markup()