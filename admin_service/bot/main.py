import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from config import settings
from handlers.routes.start_router import router as start_router


bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

    
    
async def main():
    dp.include_router(start_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())