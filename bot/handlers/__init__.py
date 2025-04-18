from aiogram import Dispatcher
from .start import register_start_handlers
from .menu import register_menu_handlers
from .cart import register_cart_handlers
from .orders import register_orders_handlers
from .settings import register_settings_handlers

def register_all_handlers(dp: Dispatcher):
    register_start_handlers(dp)
    register_menu_handlers(dp)
    register_cart_handlers(dp)
    register_orders_handlers(dp)
    register_settings_handlers(dp) 