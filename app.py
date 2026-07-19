import asyncio
from aiogram import Bot, Dispatcher
from middlewares.database import DatabaseMiddleware
from config import BOT_TOKEN # type: ignore
from handlers.start import router as start_router
from handlers.customer.register import router as register_router
from handlers.customer.place_order import router as place_order_router
from handlers.hotel.menu import  router as hotel_menu_orders
from handlers.hotel.orders import router as hotel_orders_router
bot = Bot(BOT_TOKEN) # type: ignore
dp = Dispatcher()
dp.update.middleware(DatabaseMiddleware())
dp.include_router(start_router)
dp.include_router(register_router)
dp.include_router(place_order_router)
dp.include_router(hotel_orders_router)
async def main():
    print("Bot Started")
    await dp.start_polling(bot)
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except(ValueError):
        print("Bot is stoped")