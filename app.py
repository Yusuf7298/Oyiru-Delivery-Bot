import asyncio
from aiogram import Bot, Dispatcher
from middlewares.database import DatabaseMiddleware
from middlewares.language import LanguageMiddleware
from config import BOT_TOKEN  # type: ignore

from handlers.common.cancel import router as cancel_router
from handlers.start import router as start_router
from handlers.common.language import router as language_router
from handlers.common.support import router as support_router
from handlers.customer.register import router as register_router
from handlers.customer.select_hotel import router as select_hotel_router
from handlers.customer.place_order import router as place_order_router
from handlers.customer.order import router as order_router
from handlers.customer.upload_order import router as upload_order_router
from handlers.customer.view_order import router as view_order_router
from handlers.customer.returns import router as returns_router
from handlers.customer.rating import router as rating_router

from handlers.hotel.menu import router as hotel_menu_router
from handlers.hotel.orders import router as hotel_orders_router
from handlers.hotel.staff import router as hotel_staff_router
from handlers.store_manager.orders import router as store_manager_orders_router

from handlers.delivery.orders import router as delivery_orders_router

from handlers.admin.dashboard import router as admin_dashboard_router
from handlers.admin.hotels import router as admin_hotels_router
from handlers.admin.categories import router as admin_categories_router
from handlers.admin.products import router as admin_products_router
from handlers.admin.users import router as admin_users_router
from handlers.admin.analytics import router as admin_analytics_router
from handlers.admin.broadcasts import router as admin_broadcasts_router
from handlers.admin.assign_driver import router as admin_assign_driver_router
from handlers.admin.orders import router as admin_orders_router
from handlers.admin.reports import router as admin_reports_router
from handlers.admin.support import router as admin_support_router
from handlers.common.fallback import router as fallback_router

bot = Bot(BOT_TOKEN)  # type: ignore
dp = Dispatcher()

# Middlewares
dp.update.middleware(DatabaseMiddleware())
dp.update.middleware(LanguageMiddleware())

# Include Routers (ordered from specific commands to general fallbacks)
dp.include_router(cancel_router)
dp.include_router(start_router)
dp.include_router(language_router)
dp.include_router(support_router)
dp.include_router(register_router)
dp.include_router(select_hotel_router)

dp.include_router(place_order_router)
dp.include_router(order_router)
dp.include_router(upload_order_router)
dp.include_router(view_order_router)
dp.include_router(returns_router)
dp.include_router(rating_router)

dp.include_router(hotel_menu_router)
dp.include_router(hotel_orders_router)
dp.include_router(hotel_staff_router)
dp.include_router(store_manager_orders_router)

dp.include_router(delivery_orders_router)

dp.include_router(admin_dashboard_router)
dp.include_router(admin_hotels_router)
dp.include_router(admin_categories_router)
dp.include_router(admin_products_router)
dp.include_router(admin_users_router)
dp.include_router(admin_analytics_router)
dp.include_router(admin_broadcasts_router)
dp.include_router(admin_assign_driver_router)
dp.include_router(admin_orders_router)
dp.include_router(admin_reports_router)
dp.include_router(admin_support_router)

dp.include_router(fallback_router)

from aiogram.exceptions import TelegramBadRequest
from loguru import logger

@dp.errors()
async def global_error_handler(event):
    if isinstance(event.exception, TelegramBadRequest):
        exc_str = str(event.exception).lower()
        if "query is too old" in exc_str or "message is not modified" in exc_str or "message to edit not found" in exc_str:
            return True
    logger.warning(f"Handled dispatcher error: {event.exception}")
    return True

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

async def main():
    logger.info("Starting Oyirubot in Long-Polling Mode...")
    # Explicitly remove any active webhook so polling works seamlessly without port/SSL issues
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhooks cleared. Oyirubot Long-Polling Started Successfully!")
    print("[OK] Webhooks cleared. Oyirubot Long-Polling Started Successfully!")
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot is stopped")
