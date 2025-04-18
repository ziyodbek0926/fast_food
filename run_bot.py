import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    # Initialize bot and dispatcher
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Import and register handlers
    from bot.handlers import register_all_handlers
    register_all_handlers(dp)

    # Start polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main()) 