from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.i18n import t

def admin_main_menu(lang: str = "en") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("btn_admin_hotels", lang)), KeyboardButton(text=t("btn_admin_categories", lang))],
            [KeyboardButton(text=t("btn_admin_products", lang)), KeyboardButton(text=t("btn_admin_users", lang))],
            [KeyboardButton(text=t("btn_admin_orders", lang)), KeyboardButton(text=t("btn_admin_stats", lang))],
            [KeyboardButton(text=t("btn_admin_export", lang)), KeyboardButton(text=t("btn_admin_broadcast", lang))],
            [KeyboardButton(text=t("btn_language", lang))],
        ],
        resize_keyboard=True,
    )

def hotel_list_keyboard(hotels, lang: str = "en"):
    builder = InlineKeyboardBuilder()
    for h in hotels:
        status = "✅" if h.is_active else "❌"
        builder.button(
            text=f"{status} {h.name}",
            callback_data=f"admin_hotel:{h.id}",
        )
    builder.button(text=t("btn_add_hotel", lang), callback_data="admin_hotel_add")
    builder.adjust(1)
    return builder.as_markup()

def hotel_detail_keyboard(hotel, lang: str = "en"):
    toggle = t("btn_deactivate", lang) if hotel.is_active else t("btn_activate", lang)
    toggle_cb = f"admin_hotel_deactivate:{hotel.id}" if hotel.is_active else f"admin_hotel_activate:{hotel.id}"
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_edit_name", lang), callback_data=f"admin_hotel_edit_name:{hotel.id}")
    builder.button(text=t("btn_edit_address", lang), callback_data=f"admin_hotel_edit_addr:{hotel.id}")
    builder.button(text=t("btn_edit_phone", lang), callback_data=f"admin_hotel_edit_phone:{hotel.id}")
    builder.button(text=toggle, callback_data=toggle_cb)
    builder.button(text=t("btn_delete", lang), callback_data=f"admin_hotel_delete:{hotel.id}")
    builder.button(text=t("btn_back", lang), callback_data="admin_hotels_back")
    builder.adjust(2, 2, 2)
    return builder.as_markup()

def confirm_delete_keyboard(entity: str, entity_id: int, lang: str = "en"):
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_confirm_delete", lang), callback_data=f"confirm_delete_{entity}:{entity_id}")
    builder.button(text=t("btn_cancel", lang), callback_data=f"cancel_delete_{entity}:{entity_id}")
    builder.adjust(2)
    return builder.as_markup()

def category_list_keyboard(categories, lang: str = "en"):
    builder = InlineKeyboardBuilder()
    for c in categories:
        status = "✅" if c.is_active else "❌"
        builder.button(
            text=f"{status} {c.name}",
            callback_data=f"admin_cat:{c.id}",
        )
    builder.button(text=t("btn_add_category", lang), callback_data="admin_cat_add")
    builder.adjust(1)
    return builder.as_markup()

def category_detail_keyboard(category, lang: str = "en"):
    toggle = t("btn_deactivate", lang) if category.is_active else t("btn_activate", lang)
    toggle_cb = (
        f"admin_cat_deactivate:{category.id}"
        if category.is_active
        else f"admin_cat_activate:{category.id}"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_edit_name", lang), callback_data=f"admin_cat_edit:{category.id}")
    builder.button(text=toggle, callback_data=toggle_cb)
    builder.button(text=t("btn_view_products", lang), callback_data=f"admin_cat_products:{category.id}")
    builder.button(text=t("btn_delete", lang), callback_data=f"admin_cat_delete:{category.id}")
    builder.button(text=t("btn_back", lang), callback_data="admin_categories_back")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def product_list_keyboard(products, category_id: int, lang: str = "en"):
    builder = InlineKeyboardBuilder()
    for p in products:
        status = "✅" if p.is_active else "❌"
        builder.button(
            text=f"{status} {p.name} ({p.unit})",
            callback_data=f"admin_prod:{p.id}",
        )
    builder.button(text=t("btn_add_product", lang), callback_data=f"admin_prod_add:{category_id}")
    builder.button(text=t("btn_back_to_category", lang), callback_data=f"admin_cat:{category_id}")
    builder.adjust(1)
    return builder.as_markup()

def product_detail_keyboard(product, lang: str = "en"):
    toggle = t("btn_deactivate", lang) if product.is_active else t("btn_activate", lang)
    toggle_cb = (
        f"admin_prod_deactivate:{product.id}"
        if product.is_active
        else f"admin_prod_activate:{product.id}"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_edit_name", lang), callback_data=f"admin_prod_edit_name:{product.id}")
    builder.button(text=t("btn_edit_unit", lang), callback_data=f"admin_prod_edit_unit:{product.id}")
    builder.button(text=t("btn_move_category", lang), callback_data=f"admin_prod_edit_cat:{product.id}")
    builder.button(text=toggle, callback_data=toggle_cb)
    builder.button(text=t("btn_delete", lang), callback_data=f"admin_prod_delete:{product.id}")
    builder.button(text=t("btn_back", lang), callback_data=f"admin_cat_products:{product.category_id}")
    builder.adjust(2, 2, 2)
    return builder.as_markup()

def category_pick_keyboard(categories, prefix: str, lang: str = "en"):
    builder = InlineKeyboardBuilder()
    for c in categories:
        builder.button(text=c.name, callback_data=f"{prefix}:{c.id}")
    builder.button(text=t("btn_cancel", lang), callback_data="admin_prod_cancel")
    builder.adjust(2)
    return builder.as_markup()

def user_section_keyboard(lang: str = "en"):
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_customers", lang), callback_data="admin_users_list:customer:1")
    builder.button(text=t("btn_store_managers", lang), callback_data="admin_users_list:hotel:1")
    builder.button(text=t("btn_delivery_partners", lang), callback_data="admin_users_list:delivery:1")
    builder.button(text=t("btn_admins", lang), callback_data="admin_users_list:admin:1")
    builder.button(text=t("btn_all_users", lang), callback_data="admin_users_list:all:1")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def user_detail_keyboard(user, back_role: str = "all", back_page: int = 1, lang: str = "en"):
    builder = InlineKeyboardBuilder()
    active_label = t("btn_deactivate", lang) if user.is_active else t("btn_activate", lang)
    active_cb = (
        f"admin_user_deactivate:{user.id}:{back_role}:{back_page}"
        if user.is_active
        else f"admin_user_activate:{user.id}:{back_role}:{back_page}"
    )
    builder.button(text=active_label, callback_data=active_cb)
    builder.button(text=t("btn_change_role", lang), callback_data=f"admin_user_change_role:{user.id}:{back_role}:{back_page}")
    builder.button(text=t("btn_back", lang), callback_data=f"admin_users_list:{back_role}:{back_page}")
    builder.adjust(2, 1)
    return builder.as_markup()

def role_pick_keyboard(user_id: int, back_role: str = "all", back_page: int = 1, lang: str = "en"):
    builder = InlineKeyboardBuilder()
    builder.button(text=t("role_customer", lang), callback_data=f"admin_set_role:{user_id}:customer:{back_role}:{back_page}")
    builder.button(text=t("role_store_manager", lang), callback_data=f"admin_set_role:{user_id}:hotel:{back_role}:{back_page}")
    builder.button(text=t("role_delivery", lang), callback_data=f"admin_set_role:{user_id}:delivery:{back_role}:{back_page}")
    builder.button(text=t("role_admin", lang), callback_data=f"admin_set_role:{user_id}:admin:{back_role}:{back_page}")
    builder.button(text=t("btn_cancel", lang), callback_data=f"admin_user_detail:{user_id}:{back_role}:{back_page}")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def back_keyboard(callback_data: str, lang: str = "en"):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("btn_back", lang), callback_data=callback_data)]]
    )

