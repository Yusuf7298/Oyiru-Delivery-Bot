import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN # type: ignore
bot = Bot(BOT_TOKEN) # type: ignore
dp = Dispatcher()
async def main():
    print("Bot Started")
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())