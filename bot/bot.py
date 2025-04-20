import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Muhit o'zgaruvchilarini yuklash
load_dotenv()

# Bot va dispatcher ni ishga tushirish
bot = Bot(token=os.getenv('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Handlerlarni import qilish
from .handlers import register_all_handlers

# Barcha handlerlarni ro'yxatdan o'tkazish
register_all_handlers(dp) 