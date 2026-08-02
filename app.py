import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN  # type: ignore
from middlewares.auth import ErrorHandlingMiddleware
from middlewares.logging import LoggingMiddleware
from middlewares.throttling import ThrottlingMiddleware
from middlewares.database import DatabaseMiddleware
from handlers.start import router as start_router
from handlers.common.cancel import router as cancel_router
from handlers.customer.register import router as register_router
from handlers.customer.select_hotel import router as select_hotel_router
from handlers.customer.place_order import router as customer_place_order_router
from handlers.customer.order import router as customer_order_router
from handlers.customer.upload_order import router as customer_upload_router
from handlers.customer.view_order import router as customer_history_router
from handlers.customer.rating import router as customer_rating_router
from handlers.customer.returns import router as customer_returns_router
from handlers.store_manager.orders import router as store_manager_router
from handlers.admin.dashboard import router as admin_dashboard_router
from handlers.admin.hotels import router as admin_hotels_router
from handlers.admin.categories import router as admin_categories_router
from handlers.admin.products import router as admin_products_router
from handlers.admin.users import router as admin_users_router
from handlers.admin.broadcasts import router as admin_broadcasts_router
from handlers.admin.analytics import router as admin_analytics_router
from handlers.admin.orders import router as admin_orders_router
from handlers.admin.assign_driver import router as admin_assign_driver_router
from config.logging import setup_logging # type: ignore
from loguru import logger

import os
from aiogram.client.session.aiohttp import AiohttpSession
_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy") or os.getenv("HTTP_PROXY")

if _proxy:
    session = AiohttpSession(proxy=_proxy)
    bot = Bot(BOT_TOKEN, session=session)  # type: ignore
else:
    bot = Bot(BOT_TOKEN)  # type: ignore

dp = Dispatcher()
dp.update.middleware(ErrorHandlingMiddleware())
dp.update.middleware(LoggingMiddleware())
dp.update.middleware(ThrottlingMiddleware())
dp.update.middleware(DatabaseMiddleware())
dp.include_router(cancel_router)
dp.include_router(start_router)
dp.include_router(admin_dashboard_router)
dp.include_router(admin_hotels_router)
dp.include_router(admin_categories_router)
dp.include_router(admin_products_router)
dp.include_router(admin_users_router)
dp.include_router(admin_broadcasts_router)
dp.include_router(admin_analytics_router)
dp.include_router(admin_orders_router)
dp.include_router(admin_assign_driver_router)
# Store Manager
dp.include_router(store_manager_router)

# Delivery
from handlers.delivery.orders import router as delivery_router
dp.include_router(delivery_router)

# Customer
dp.include_router(register_router)
dp.include_router(select_hotel_router)
dp.include_router(customer_place_order_router)  # "📦 Place Order" entry point
dp.include_router(customer_order_router)
dp.include_router(customer_upload_router)
dp.include_router(customer_history_router)
dp.include_router(customer_rating_router)
dp.include_router(customer_returns_router)

# Fallback — must be LAST — catches role-mismatched button presses
from handlers.common.fallback import router as fallback_router
dp.include_router(fallback_router)

from aiohttp import web

async def start_health_server() -> None:
    port = int(os.getenv("PORT") or os.getenv("WEBSITES_PORT") or 8000)
    app_web = web.Application()
    async def health_check(request):
        return web.Response(text="Oyiru Delivery Bot is running OK!")
    app_web.router.add_get("/", health_check)
    app_web.router.add_get("/health", health_check)
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check web server running on port {port}")

async def main() -> None:
    setup_logging()
    from config import BOT_TOKEN, DATABASE_URL
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not DATABASE_URL:
        missing.append("DATABASE_URL")
    if missing:
        logger.error(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Create a .env file with these values in Azure Portal Environment Variables and restart."
        )
        raise SystemExit(1)
    import os
    uploads_dir = os.path.join(os.getcwd(), "uploads")
    try:
        os.makedirs(uploads_dir, exist_ok=True)
        test_file = os.path.join(uploads_dir, ".write_test")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
    except Exception as e:
        logger.error(f"uploads/ directory is not writable: {e}")
        raise SystemExit(1)

    await start_health_server()
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Cleared old Telegram webhooks")
    except Exception as e:
        logger.warning(f"Could not delete webhook: {e}")

    logger.info("Bot started — polling")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")

