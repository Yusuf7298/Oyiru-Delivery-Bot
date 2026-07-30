from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

def admin_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏨 Hotels"),     KeyboardButton(text="🗂 Categories")],
            [KeyboardButton(text="📦 Products"),   KeyboardButton(text="👥 Users")],
            [KeyboardButton(text="📦 New Orders"), KeyboardButton(text="📊 Statistics")],
            [KeyboardButton(text="📢 Broadcast")],
        ],
        resize_keyboard=True,
    )


def hotel_list_keyboard(hotels):
    """Inline list of all hotels with manage button."""
    builder = InlineKeyboardBuilder()
    for h in hotels:
        status = "✅" if h.is_active else "❌"
        builder.button(
            text=f"{status} {h.name}",
            callback_data=f"admin_hotel:{h.id}",
        )
    builder.button(text="➕ Add Hotel", callback_data="admin_hotel_add")
    builder.adjust(1)
    return builder.as_markup()


def hotel_detail_keyboard(hotel):
    toggle = "🔴 Deactivate" if hotel.is_active else "🟢 Activate"
    toggle_cb = f"admin_hotel_deactivate:{hotel.id}" if hotel.is_active else f"admin_hotel_activate:{hotel.id}"
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Edit Name",    callback_data=f"admin_hotel_edit_name:{hotel.id}")
    builder.button(text="✏️ Edit Address", callback_data=f"admin_hotel_edit_addr:{hotel.id}")
    builder.button(text="✏️ Edit Phone",   callback_data=f"admin_hotel_edit_phone:{hotel.id}")
    builder.button(text=toggle,            callback_data=toggle_cb)
    builder.button(text="🗑 Delete",        callback_data=f"admin_hotel_delete:{hotel.id}")
    builder.button(text="⬅️ Back",          callback_data="admin_hotels_back")
    builder.adjust(2, 2, 2)
    return builder.as_markup()


def confirm_delete_keyboard(entity: str, entity_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yes, Delete", callback_data=f"confirm_delete_{entity}:{entity_id}")
    builder.button(text="❌ Cancel",      callback_data=f"cancel_delete_{entity}:{entity_id}")
    builder.adjust(2)
    return builder.as_markup()


def category_list_keyboard(categories):
    builder = InlineKeyboardBuilder()
    for c in categories:
        status = "✅" if c.is_active else "❌"
        builder.button(
            text=f"{status} {c.name}",
            callback_data=f"admin_cat:{c.id}",
        )
    builder.button(text="➕ Add Category", callback_data="admin_cat_add")
    builder.adjust(1)
    return builder.as_markup()


def category_detail_keyboard(category):
    toggle = "🔴 Deactivate" if category.is_active else "🟢 Activate"
    toggle_cb = (
        f"admin_cat_deactivate:{category.id}"
        if category.is_active
        else f"admin_cat_activate:{category.id}"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Edit Name", callback_data=f"admin_cat_edit:{category.id}")
    builder.button(text=toggle,         callback_data=toggle_cb)
    builder.button(text="📦 Products",  callback_data=f"admin_cat_products:{category.id}")
    builder.button(text="🗑 Delete",     callback_data=f"admin_cat_delete:{category.id}")
    builder.button(text="⬅️ Back",       callback_data="admin_categories_back")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def product_list_keyboard(products, category_id: int):
    builder = InlineKeyboardBuilder()
    for p in products:
        status = "✅" if p.is_active else "❌"
        builder.button(
            text=f"{status} {p.name} ({p.unit})",
            callback_data=f"admin_prod:{p.id}",
        )
    builder.button(text="➕ Add Product", callback_data=f"admin_prod_add:{category_id}")
    builder.button(text="⬅️ Back to Category", callback_data=f"admin_cat:{category_id}")
    builder.adjust(1)
    return builder.as_markup()


def product_detail_keyboard(product):
    toggle = "🔴 Deactivate" if product.is_active else "🟢 Activate"
    toggle_cb = (
        f"admin_prod_deactivate:{product.id}"
        if product.is_active
        else f"admin_prod_activate:{product.id}"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Edit Name",     callback_data=f"admin_prod_edit_name:{product.id}")
    builder.button(text="✏️ Edit Unit",     callback_data=f"admin_prod_edit_unit:{product.id}")
    builder.button(text="✏️ Move Category", callback_data=f"admin_prod_edit_cat:{product.id}")
    builder.button(text=toggle,             callback_data=toggle_cb)
    builder.button(text="🗑 Delete",         callback_data=f"admin_prod_delete:{product.id}")
    builder.button(text="⬅️ Back",           callback_data=f"admin_cat_products:{product.category_id}")
    builder.adjust(2, 2, 2)
    return builder.as_markup()


def category_pick_keyboard(categories, prefix: str):
    """Used when selecting a category for a new/moved product."""
    builder = InlineKeyboardBuilder()
    for c in categories:
        builder.button(text=c.name, callback_data=f"{prefix}:{c.id}")
    builder.button(text="❌ Cancel", callback_data="admin_prod_cancel")
    builder.adjust(2)
    return builder.as_markup()

def user_section_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Customers",      callback_data="admin_users_list:customer:1")
    builder.button(text="🏪 Store Managers", callback_data="admin_users_list:hotel:1")
    builder.button(text="🚚 Delivery",       callback_data="admin_users_list:delivery:1")
    builder.button(text="👑 Admins",         callback_data="admin_users_list:admin:1")
    builder.button(text="📋 All Users",      callback_data="admin_users_list:all:1")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def user_detail_keyboard(user, back_role: str = "all", back_page: int = 1):
    builder = InlineKeyboardBuilder()
    active_label = "🔴 Deactivate" if user.is_active else "🟢 Activate"
    active_cb = (
        f"admin_user_deactivate:{user.id}:{back_role}:{back_page}"
        if user.is_active
        else f"admin_user_activate:{user.id}:{back_role}:{back_page}"
    )
    builder.button(text=active_label,    callback_data=active_cb)
    builder.button(text="🔑 Change Role", callback_data=f"admin_user_change_role:{user.id}:{back_role}:{back_page}")
    builder.button(text="⬅️ Back",        callback_data=f"admin_users_list:{back_role}:{back_page}")
    builder.adjust(2, 1)
    return builder.as_markup()


def role_pick_keyboard(user_id: int, back_role: str = "all", back_page: int = 1):
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Customer",      callback_data=f"admin_set_role:{user_id}:customer:{back_role}:{back_page}")
    builder.button(text="🏪 Store Manager", callback_data=f"admin_set_role:{user_id}:hotel:{back_role}:{back_page}")
    builder.button(text="🚚 Delivery",      callback_data=f"admin_set_role:{user_id}:delivery:{back_role}:{back_page}")
    builder.button(text="👑 Admin",         callback_data=f"admin_set_role:{user_id}:admin:{back_role}:{back_page}")
    builder.button(text="❌ Cancel",        callback_data=f"admin_user_detail:{user_id}:{back_role}:{back_page}")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def back_keyboard(callback_data: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Back", callback_data=callback_data)]]
    )
