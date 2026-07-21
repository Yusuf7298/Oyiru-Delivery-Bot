from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models.order import OrderStatus


def order_status_keyboard(order):
    builder = InlineKeyboardBuilder()

    if order.status == OrderStatus.SUBMITTED:
        builder.button(
            text="✅ Under Review",
            callback_data=f"status:{order.id}:UNDER_REVIEW",
        )

        builder.button(
            text="❌ Cancel",
            callback_data=f"status:{order.id}:CANCELLED",
        )

    elif order.status == OrderStatus.UNDER_REVIEW:
        builder.button(
            text="📦 Inventory Checking",
            callback_data=f"status:{order.id}:INVENTORY_CHECKING",
        )

    elif order.status == OrderStatus.INVENTORY_CHECKING:
        builder.button(
            text="👨‍🍳 Preparing",
            callback_data=f"status:{order.id}:PREPARING",
        )

    elif order.status == OrderStatus.PREPARING:
        builder.button(
            text="📦 Packed",
            callback_data=f"status:{order.id}:PACKED",
        )

    elif order.status == OrderStatus.PACKED:
        builder.button(
            text="🚚 Ready For Delivery",
            callback_data=f"status:{order.id}:READY_FOR_DELIVERY",
        )

    elif order.status == OrderStatus.READY_FOR_DELIVERY:
        builder.button(
            text="🚛 Out For Delivery",
            callback_data=f"status:{order.id}:OUT_FOR_DELIVERY",
        )

    elif order.status == OrderStatus.OUT_FOR_DELIVERY:
        builder.button(
            text="✅ Delivered",
            callback_data=f"status:{order.id}:DELIVERED",
        )

    builder.adjust(1)
    return builder.as_markup()