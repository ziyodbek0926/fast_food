import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize bot and dispatcher
bot = Bot(token=os.getenv('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Import handlers
from .handlers import register_all_handlers

# Register all handlers
register_all_handlers(dp) 