from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ..keyboards.language import get_language_keyboard
from core.models import TelegramUser, Language

router = Router()

# /start buyrug'ini qayta ishlash
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    # Foydalanuvchi mavjudligini tekshirish
    user, created = await TelegramUser.objects.aget_or_create(
        user_id=message.from_user.id,
        defaults={
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
        }
    )

    # Til tanlash klaviaturasini yuborish
    await message.answer(
        "Please select your language:\n\n"
        "Iltimos, tilni tanlang:",
        reply_markup=get_language_keyboard()
    )

# Til tanlashni qayta ishlash
@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery, state: FSMContext):
    # Tanlangan til kodini olish
    lang_code = callback.data.split("_")[1]
    
    # Til obyektini olish
    language = await Language.objects.aget(code=lang_code)
    
    # Foydalanuvchi tilini yangilash
    user = await TelegramUser.objects.aget(user_id=callback.from_user.id)
    user.language = language
    await user.asave()

    # Tanlangan tilda xabar yuborish
    if lang_code == "uz":
        welcome_text = (
            "Assalomu alaykum! Fast Food botiga xush kelibsiz.\n\n"
            "🍔 Menyular - mahsulotlar ro'yxati\n"
            "🛒 Savat - tanlangan mahsulotlar\n"
            "📦 Buyurtmalarim - buyurtmalar tarixi\n"
            "⚙️ Sozlamalar - tilni o'zgartirish"
        )
    else:
        welcome_text = (
            "Здравствуйте! Добро пожаловать в бот Fast Food.\n\n"
            "🍔 Меню - список продуктов\n"
            "🛒 Корзина - выбранные товары\n"
            "📦 Мои заказы - история заказов\n"
            "⚙️ Настройки - изменить язык"
        )

    await callback.message.edit_text(welcome_text)
    await callback.answer() 