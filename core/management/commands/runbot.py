from django.core.management.base import BaseCommand
from django.conf import settings
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
import logging
import sys
import os, time
from dotenv import load_dotenv
from core.models import Category, Product, TelegramUser, Order, OrderItem, Language, CartItem
from django.db.models import Q
from asgiref.sync import sync_to_async

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables with override=True to ensure we get the latest values
load_dotenv(override=True)

# Get the bot token from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
# print(BOT_TOKEN)
if not BOT_TOKEN:
    logging.error("BOT_TOKEN not found in environment variables. Please check your .env file.")
    sys.exit(1)

# Initialize bot and dispatche
dp = Dispatcher()

# Language selection keyboard
def get_language_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
        ]
    ])
    return keyboard

# Main menu keyboards for different languages
def get_main_keyboard(lang):
    if lang == 'uz':
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🍔 Menyu"), KeyboardButton(text="🛒 Savat")],
                [KeyboardButton(text="📍 Buyurtmalarim"), KeyboardButton(text="💬 Aloqa")],
                [KeyboardButton(text="🌐 Tilni o'zgartirish")]
            ],
            resize_keyboard=True
        )
    elif lang == 'ru':
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🍔 Меню"), KeyboardButton(text="🛒 Корзина")],
                [KeyboardButton(text="📍 Мои заказы"), KeyboardButton(text="💬 Контакты")],
                [KeyboardButton(text="🌐 Сменить язык")]
            ],
            resize_keyboard=True
        )

    return keyboard

# Welcome messages in different languages
WELCOME_MESSAGES = {
    'uz': (
        "🍽️ Fast Food Botga xush kelibsiz!\n\n"
        "Men sizga quyidagilarda yordam bera olaman:\n"
        "🍔 Menyu ko'rish\n"
        "🛒 Buyurtma berish\n"
        "📍 Yetkazib berishni kuzatish\n"
        "💬 Mijozlar bilan aloqa\n\n"
        "Quyidagi tugmalardan foydalaning:"
    ),
    'ru': (
        "🍽️ Добро пожаловать в Fast Food Bot!\n\n"
        "Я могу помочь вам с:\n"
        "🍔 Просмотр меню\n"
        "🛒 Оформление заказа\n"
        "📍 Отслеживание доставки\n"
        "💬 Поддержка клиентов\n\n"
        "Используйте кнопки ниже:"
    )
}

# Menu messages in different languages
MENU_MESSAGES = {
    'uz': "Menyu ko'rsatilmoqda...",
    'ru': "Меню загружается..."
}

# Order messages in different languages
ORDER_MESSAGES = {
    'uz': "Buyurtma berish jarayoni boshlanmoqda...",
    'ru': "Процесс оформления заказа начинается..."
}

# Status messages in different languages
STATUS_MESSAGES = {
    'uz': "Buyurtma holati tekshirilmoqda...",
    'ru': "Проверка статуса заказа..."
}

# Contact messages in different languages
CONTACT_MESSAGES = {
    'uz': (
        "📞 Aloqa ma'lumotlari:\n\n"
        "Telefon: +998930514737\n"
        "Email: support@fastfood.com\n"
        "Ish vaqti: 24/7"
    ),
    'ru': (
        "📞 Контактная информация:\n\n"
        "Телефон: +998930514737\n"
        "Email: support@fastfood.com\n"
        "Часы работы: 24/7"
    )
}

# Store user language preferences
user_languages = {}

# Store user's cart data
user_carts = {}

# Store user's order state
user_order_states = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    start_message = (
        "🌐 Tilni tanlang / Выберите язык "
    )
    await message.answer(start_message, reply_markup=get_language_keyboard())

@dp.callback_query(lambda c: c.data.startswith('lang_'))
async def process_language_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = callback_query.data.split('_')[1]
    
    try:
        # Update user's language in database
        user = await TelegramUser.objects.aget(user_id=user_id)
        language = await Language.objects.aget(code=lang)
        user.language = language
        await user.asave()
        
        # Update language in memory
        user_languages[user_id] = lang
        
        # Send confirmation message in new language
        if lang == 'uz':
            text = "✅ Til muvaffaqiyatli o'zgartirildi!"
        else:
            text = "✅ Язык успешно изменен!"
        
        # Update the message with new keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🇺🇿 O'zbekcha {'✅' if lang == 'uz' else ''}", 
                    callback_data="lang_uz"
                ),
                InlineKeyboardButton(
                    text=f"🇷🇺 Русский {'✅' if lang == 'ru' else ''}", 
                    callback_data="lang_ru"
                )
            ]
        ])
        
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        
        # Send main menu in new language
        await callback_query.message.answer(
            "Bosh menyu:" if lang == 'uz' else "Главное меню:",
            reply_markup=get_main_keyboard(lang)
        )
        
    except Exception as e:
        logging.error(f"Error changing language: {str(e)}")
        if lang == 'uz':
            text = "❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
        else:
            text = "❌ Произошла ошибка. Пожалуйста, попробуйте еще раз."
        await callback_query.message.edit_text(text)
    
    await callback_query.answer()

def get_categories_keyboard(categories, lang_code, show_back=False):
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        # Use the appropriate name based on language
        name = category.name_uz if lang_code == "uz" else category.name_ru
        builder.add(InlineKeyboardButton(
            text=name,
            callback_data=f"category_{category.id}"
        ))
    
    # Add back button only if show_back is True
    if show_back:
        if lang_code == "uz":
            builder.add(InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data="back_to_menu"
            ))
        else:
            builder.add(InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="back_to_menu"
            ))
    
    builder.adjust(2)  # Arrange buttons in 2 columns
    return builder.as_markup()

def get_products_keyboard(products, lang_code):
    builder = InlineKeyboardBuilder()
    
    for product in products:
        # Use the appropriate name based on language
        name = product.name_uz if lang_code == "uz" else product.name_ru
        builder.add(InlineKeyboardButton(
            text=name,
            callback_data=f"product_{product.id}"
        ))
    
    # Add back button
    if lang_code == "uz":
        builder.add(InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="back_to_categories"
        ))
    else:
        builder.add(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="back_to_categories"
        ))
    
    builder.adjust(2)  # Arrange buttons in 2 columns
    return builder.as_markup()

@dp.message(F.text.in_(["/start", "🏠 Bosh menyu", "🏠 Главное меню"]))
async def handle_menu(message: types.Message):
    user_id = message.from_user.id
    language = user_languages.get(user_id, 'uz')
    
    # Foydalanuvchi mavjudligini tekshirish
    user, created = await TelegramUser.objects.aget_or_create(
        user_id=user_id,
        defaults={
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
            'language': await Language.objects.aget(code=language)
        }
    )
    
    # Agar yangi foydalanuvchi bo'lsa, tilni saqlash
    if created:
        user_languages[user_id] = language
    
    # Faol kategoriyalarni olish
    categories = await sync_to_async(list)(Category.objects.filter(is_available=True))
    
    if not categories:
        if language == 'uz':
            await message.answer("Hozircha kategoriyalar mavjud emas.")
        else:
            await message.answer("Пока нет доступных категорий.")
        return
    
    # Kategoriyalar tugmalarini yaratish
    keyboard = InlineKeyboardMarkup(row_width=2)
    for category in categories:
        if language == 'uz':
            keyboard.add(InlineKeyboardButton(
                text=category.name_uz,
                callback_data=f"category_{category.id}"
            ))
        else:
            keyboard.add(InlineKeyboardButton(
                text=category.name_ru,
                callback_data=f"category_{category.id}"
            ))
    
    # Send message based on language
    if language == 'uz':
        text = "Kategoriyalardan birini tanlang:"
    else:
        text = "Выберите категорию:"
    
    await message.answer(text, reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith('category_'))
async def handle_category(callback_query: types.CallbackQuery):
    category_id = int(callback_query.data.split("_")[1])
    
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')

    try:
        # Get category and its products using sync_to_async
        get_category = sync_to_async(Category.objects.get)
        get_products = sync_to_async(lambda: list(Product.objects.filter(category_id=category_id, is_available=True)))
        
        category = await get_category(id=category_id)
        products = await get_products()

        if not products:
            if lang_code == "uz":
                text = f"{category.name_uz} kategoriyasida hozircha mahsulotlar mavjud emas."
            else:
                text = f"В категории {category.name_ru} пока нет доступных продуктов."
            
            # Check if the message is a photo message
            if callback_query.message.photo:
                # For photo messages, send a new message instead of editing
                await callback_query.message.answer(text)
            else:
                # For text messages, edit the existing message
                await callback_query.message.edit_text(text)
            return

        # Create keyboard based on language
        keyboard = get_products_keyboard(products, lang_code)

        # Send message based on language
        if lang_code == "uz":
            text = f"{category.name_uz} kategoriyasidagi mahsulotlar:"
        else:
            text = f"Продукты категории {category.name_ru}:"
        
        # Check if the message is a photo message
        if callback_query.message.photo:
            # For photo messages, send a new message instead of editing
            await callback_query.message.answer(text, reply_markup=keyboard)
        else:
            # For text messages, edit the existing message
            await callback_query.message.edit_text(text, reply_markup=keyboard)
            
        await callback_query.answer()
        
        # Delete the message immediat
        # await asyncio.sleep(7)
        # await callback_query.message.delete()
    except Exception as e:
        logging.error(f"Error in handle_category: {str(e)}")
        if lang_code == "uz":
            await callback_query.message.edit_text("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        else:
            await callback_query.message.edit_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        await callback_query.answer()


@dp.callback_query(lambda c: c.data in ["back_to_products"])
async def handle_back(callback_query: types.CallbackQuery, bot: Bot):
    category_id = int(1)
    
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')

    try:
        # Get category and its products using sync_to_async
        get_category = sync_to_async(Category.objects.get)
        get_products = sync_to_async(lambda: list(Product.objects.filter(category_id=category_id, is_available=True)))
        
        category = await get_category(id=category_id)
        products = await get_products()

        if not products:
            if lang_code == "uz":
                text = f"{category.name_uz} kategoriyasida hozircha mahsulotlar mavjud emas."
            else:
                text = f"В категории {category.name_ru} пока нет доступных продуктов."
            
            # Check if the message is a photo message
            if callback_query.message.photo:
                # For photo messages, send a new message instead of editing
                await callback_query.message.answer(text)
            else:
                # For text messages, edit the existing message
                await callback_query.message.edit_text(text)
            return

        # Create keyboard based on language
        keyboard = get_products_keyboard(products, lang_code)

        # Send message based on language
        if lang_code == "uz":
            text = f"{category.name_uz} kategoriyasidagi mahsulotlar:"
        else:
            text = f"Продукты категории {category.name_ru}:"
        await callback_query.message.delete()
        # Check if the message is a photo message
        if callback_query.message.photo:
            # For photo messages, send a new message instead of editing
            await callback_query.message.answer(text, reply_markup=keyboard)
        else:
            # For text messages, edit the existing message
            await callback_query.message.edit_text(text, reply_markup=keyboard)
            
        await callback_query.answer()
        # await callback_query.message.delete()
    except Exception as e:
        logging.error(f"Error in handle_back: {str(e)}")
        if lang_code == "uz":
            error_text = "Xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
        else:
            error_text = "Произошла ошибка. Пожалуйста, попробуйте еще раз."
            
        # Check if the message is a photo message
        if callback_query.message.photo:
            # For photo messages, send a new message instead of editing
            await callback_query.message.answer(error_text)
        else:
            # For text messages, edit the existing message
            await callback_query.message.edit_text(error_text)
            
        await callback_query.answer()

@dp.message(lambda message: message.text in ["🛒 Savat", "🛒 Корзина"])
async def handle_cart(message: types.Message):
    user_id = message.from_user.id
    language = user_languages.get(user_id, 'uz')
    
    # Check if cart exists and has items
    if user_id not in user_carts or not user_carts[user_id]:
        if language == 'uz':
            await message.answer("Savat bo'sh")
        else:
            await message.answer("Корзина пуста")
        return
    
    # Calculate total and format cart items
    total = 0
    text = "🛒 Savatingiz:\n\n" if language == 'uz' else "🛒 Ваша корзина:\n\n"
    
    # Group identical items and calculate their totals
    for item in user_carts[user_id]:
        product_name = item['name_uz'] if language == 'uz' else item['name_ru']
        item_total = item['price'] * item['quantity']
        total += item_total
        text += f"{product_name} x {item['quantity']} = {item_total:,.2f} so'm\n"
    
    text += f"\nJami: {total:,.2f} so'm"
    
    # Create keyboard with action buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Buyurtma berish" if language == 'uz' else "✅ Оформить заказ",
                callback_data="checkout"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Savatni tozalash" if language == 'uz' else "❌ Очистить корзину",
                callback_data="clear_cart"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga" if language == 'uz' else "⬅️ Назад",
                callback_data="back_to_categories"
            )
        ]
    ])
    
    await message.answer(text, reply_markup=keyboard)

@dp.message(lambda message: message.text in ["📍 Buyurtmalarim", "📍 Мои заказы"])
async def handle_my_orders(message: types.Message):
    user_id = message.from_user.id
    language = user_languages.get(user_id, 'uz')
    
    # Foydalanuvchining buyurtmalarini olish
    orders = await sync_to_async(list)(Order.objects.filter(user__user_id=user_id).order_by('-created_at'))
    
    if not orders:
        if language == 'uz':
            await message.answer("Sizda hali buyurtmalar yo'q")
        else:
            await message.answer("У вас пока нет заказов")
        return
    
    # Buyurtmalarni ko'rsatish
    text = "📋 Buyurtmalarim:\n\n" if language == 'uz' else "📋 Мои заказы:\n\n"
    
    for order in orders:
        status = {
            'new': '⏳ Kutilmoqda' if language == 'uz' else '⏳ В ожидании',
            'confirmed': '✅ Tasdiqlangan' if language == 'uz' else '✅ Подтвержден',
            'preparing': '🔄 Tayyorlanmoqda' if language == 'uz' else '🔄 Готовится',
            'ready': '✅ Tayyor' if language == 'uz' else '✅ Готов',
            'delivered': '✅ Yetkazib berilgan' if language == 'uz' else '✅ Доставлен',
            'cancelled': '❌ Bekor qilingan' if language == 'uz' else '❌ Отменен'
        }[order.status]
        
        text += f"Buyurtma #{order.id}\n"
        text += f"Holat: {status}\n"
        text += f"Jami: {order.total_price} so'm\n"
        text += f"Sana: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    await message.answer(text)

@dp.message(lambda message: message.text in ["💬 Aloqa", "💬 Контакты"])
async def handle_contact_info(message: types.Message):
    user_id = message.from_user.id
    language = user_languages.get(user_id, 'uz')
    
    contact_info = """
📞 Aloqa ma'lumotlari:

📍 Manzil: Samarqand shahri
📱 Telefon: +998 93 051 47 37
📧 Email: support@fastfood.com
🕒 Ish vaqti: 09:00 - 23:00
""" if language == 'uz' else """
📞 Контактная информация:

📍 Адрес: г. Samarqand
📱 Телефон: +998 93 051 47 37
📧 Email: support@fastfood.com
🕒 Время работы: 09:00 - 23:00
"""
    
    await message.answer(contact_info)


@dp.message(lambda message: message.text in ["🌐 Tilni o'zgartirish", "🌐 Сменить язык"])
async def handler_lang(message: types.Message):
    start_message = (
        "🌐 Tilni tanlang / Выберите язык "
    )
    await message.answer(start_message, reply_markup=get_language_keyboard())


@dp.callback_query(F.data == "settings")
async def handle_settings(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = user_languages.get(user_id, 'uz')
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    if language == 'uz':
        keyboard.add(
            InlineKeyboardButton(text="🇺🇿 O'zbek tili", callback_data="language_uz"),
            InlineKeyboardButton(text="🇷🇺 Rus tili", callback_data="language_ru")
        )
        keyboard.add(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_menu"))
        await callback.message.edit_text("⚙️ Sozlamalar:", reply_markup=keyboard)
    else:
        keyboard.add(
            InlineKeyboardButton(text="🇺🇿 Узбекский", callback_data="language_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="language_ru")
        )
        keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu"))
        await callback.message.edit_text("⚙️ Настройки:", reply_markup=keyboard)

@dp.callback_query(F.data == "contact")
async def handle_contact(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language = user_languages.get(user_id, 'uz')
    
    contact_info = """
📞 Aloqa ma'lumotlari:

📍 Manzil: Samarqand shahri
📱 Telefon: +998 93 051 47 37
🕒 Ish vaqti: 09:00 - 23:00
""" if language == 'uz' else """
📞 Контактная информация:

📍 Адрес: г. Samarqand
📱 Телефон: +998 93 051 47 37
🕒 Время работы: 09:00 - 23:00
"""
    
    keyboard = InlineKeyboardMarkup()
    if language == 'uz':
        keyboard.add(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_menu"))
    else:
        keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu"))
    
    await callback.message.edit_text(contact_info, reply_markup=keyboard)

@dp.callback_query(F.data == "back_to_menu")
async def handle_back_to_menu(callback: types.CallbackQuery):
    await handle_menu(callback.message)

@dp.message(lambda message: message.text in ["🍔 Menyu", "🍔 Меню"])
async def handle_menu(message: types.Message):
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(message.from_user.id, 'uz')

    # Get all categories
    categories = await sync_to_async(list)(Category.objects.all())

    if not categories:
        if lang_code == "uz":
            await message.answer("Hozircha kategoriyalar mavjud emas.")
        else:
            await message.answer("Пока нет доступных категорий.")
        return

    # Create keyboard based on language with show_back=False for main menu
    keyboard = get_categories_keyboard(categories, lang_code, show_back=False)

    # Send message based on language
    if lang_code == "uz":
        text = "Kategoriyalardan birini tanlang:"
    else:
        text = "Выберите категорию:"

    await message.answer(text, reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith('product_'))
async def handle_product_callback(callback_query: types.CallbackQuery):
    product_id = int(callback_query.data.split("_")[1])
    
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')

    # Get product details
    product = await sync_to_async(Product.objects.get)(id=product_id)
    
    # Format message based on language
    if lang_code == "uz":
        text = (
            f"<b>{product.name_uz}</b>\n\n"
            f"{product.description_uz}\n\n"
            f"Narx: {product.price} so'm"
        )
    else:
        text = (
            f"<b>{product.name_ru}</b>\n\n"
            f"{product.description_ru}\n\n"
            f"Цена: {product.price} сум"
        )

    # Create keyboard with add to cart and back buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🛒 Savatga qo'shish" if lang_code == "uz" else "🛒 Добавить в корзину",
                callback_data=f"add_to_cart_{product.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga" if lang_code == "uz" else "⬅️ Назад",
                callback_data="back_to_products"
            )
        ]
    ])

    # Delete the previous products list message
    await callback_query.message.delete()

    # Send product details with photo if available
    if product.image and product.image.url:
        try:
            # Get the full URL by combining MEDIA_URL and image path
            # image_url = f"{settings.DOMAIN}{product.image.url}"
            photo = FSInputFile(f'/home/ziko2/Desktop/fast_food/img/{product.name_uz}.jpg')
            await callback_query.message.answer_photo(
                photo=photo,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception as e:
            # If there's an error with the image, just send the text
            print(e)
            await callback_query.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await callback_query.message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    await callback_query.answer()

@dp.callback_query(lambda c: c.data in ["back_to_menu", "back_to_categories"])
async def handle_back(callback_query: types.CallbackQuery):
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')

    # Get active categories
    categories = await sync_to_async(list)(Category.objects.all())

    # Create keyboard based on language
    keyboard = get_categories_keyboard(categories, lang_code)

    # Send message based on language
    if lang_code == "uz":
        text = "Kategoriyalardan birini tanlang:"
    else:
        text = "Выберите категорию:"

    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer()

@dp.message(lambda message: message.text in ["🛒 Buyurtma", "🛒 Заказать", "🛒 Order"])
async def handle_order(message: types.Message):
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(message.from_user.id, 'uz')

    # Initialize cart if not exists
    if message.from_user.id not in user_carts:
        user_carts[message.from_user.id] = []

    # Set order state to 'phone'
    user_order_states[message.from_user.id] = 'phone'

    # Create keyboard with contact sharing button
    contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="📱 Raqamni ulashish" if lang_code == "uz" else "📱 Поделиться номером",
                request_contact=True
            )]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    # Ask for phone number with contact sharing button
    if lang_code == "uz":
        text = "Iltimos, telefon raqamingizni yuboring:"
    else:
        text = "Пожалуйста, отправьте ваш номер телефона:"

    await message.answer(text, reply_markup=contact_keyboard)

@dp.message(lambda message: message.contact is not None or message.text or message.location)
async def handle_order_info(message: types.Message):
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(message.from_user.id, 'uz')
    user_id = message.from_user.id

    # Check if user is in order process
    if user_id not in user_order_states:
        return

    state = user_order_states[user_id]

    if state == 'phone':
        # Check if message contains contact info
        if message.contact is not None:
            phone = message.contact.phone_number
        else:
            # Validate manually entered phone number
            phone = message.text.strip()
            if not phone.isdigit() or len(phone) < 9:
                if lang_code == "uz":
                    await message.answer("Iltimos, to'g'ri telefon raqam kiriting yoki 'Raqamni ulashish' tugmasini bosing!")
                else:
                    await message.answer("Пожалуйста, введите правильный номер телефона или нажмите кнопку 'Поделиться номером'!")
                return

        # Store phone number and ask for address
        user_order_states[f"{user_id}_phone"] = phone
        user_order_states[user_id] = 'address'
        
        # Create keyboard with location sharing button
        location_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(
                    text="📍 Joylashuvni ulashish" if lang_code == "uz" else "📍 Поделиться местоположением",
                    request_location=True
                )]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        if lang_code == "uz":
            text = "Iltimos, manzilingizni yuboring:"
        else:
            text = "Пожалуйста, отправьте ваш адрес:"
        await message.answer(text, reply_markup=location_keyboard)

    elif state == 'address':
        # Store address and ask for comment
        if message.location:
            address = f"Location: {message.location.latitude}, {message.location.longitude}"
        else:
            address = message.text
        user_order_states[f"{user_id}_address"] = address
        user_order_states[user_id] = 'comment'
        
        if lang_code == "uz":
            text = "Buyurtmangizga izoh qoldirishingiz mumkin (agar kerak bo'lsa):"
        else:
            text = "Вы можете оставить комментарий к заказу (если нужно):"
        await message.answer(text, reply_markup=get_main_keyboard(lang_code))

    elif state == 'comment':
        # Create order
        try:
            # Get or create user
            user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
                user_id=user_id,
                defaults={
                    'username': message.from_user.username,
                    'first_name': message.from_user.first_name,
                    'last_name': message.from_user.last_name,
                    'language': await sync_to_async(Language.objects.get)(code=lang_code) if lang_code else None
                }
            )
            
            # Create order
            order = await sync_to_async(Order.objects.create)(
                user=user,
                phone_number=user_order_states.get(f"{user_id}_phone", ""),
                address=user_order_states.get(f"{user_id}_address", ""),
                comment=message.text,
                total_price=sum(item['price'] * item['quantity'] for item in user_carts[user_id])
            )

            # Create order items
            for item in user_carts[user_id]:
                await sync_to_async(OrderItem.objects.create)(
                    order=order,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    price=item['price']
                )

            # Clear cart and order state
            del user_carts[user_id]
            del user_order_states[user_id]

            if lang_code == "uz":
                text = (
                    "Buyurtmangiz qabul qilindi! Tez orada siz bilan bog'lanamiz.\n\n"
                    f"Buyurtma raqami: #{order.id}\n"
                    f"Jami narx: {order.total_price} so'm"
                )
            else:
                text = (
                    "Ваш заказ принят! Мы свяжемся с вами в ближайшее время.\n\n"
                    f"Номер заказа: #{order.id}\n"
                    f"Общая сумма: {order.total_price} сум"
                )

            await message.answer(text, reply_markup=get_main_keyboard(lang_code))

        except Exception as e:
            logging.error(f"Error creating order: {str(e)}")
            if lang_code == "uz":
                text = f"Xatolik yuz berdi: {str(e)}. Iltimos, qayta urinib ko'ring."
            else:
                text = f"Произошла ошибка: {str(e)}. Пожалуйста, попробуйте еще раз."
            await message.answer(text)

@dp.message(lambda message: message.text in ["📍 Buyurtma holati", "📍 Статус заказа", "📍 Order Status"])
async def handle_status(message: types.Message):
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(message.from_user.id, 'uz')
    user_id = message.from_user.id

    try:
        # Get user's last order
        user = await sync_to_async(TelegramUser.objects.get)(user_id=user_id)
        order = await sync_to_async(Order.objects.filter(user=user).order_by('-created_at').first)()

        if not order:
            if lang_code == "uz":
                text = "Sizda hali buyurtmalar mavjud emas."
            else:
                text = "У вас пока нет заказов."
            await message.answer(text)
            return

        # Format status message
        status_messages = {
            'new': {'uz': 'Yangi', 'ru': 'Новый'},
            'confirmed': {'uz': 'Tasdiqlangan', 'ru': 'Подтвержден'},
            'preparing': {'uz': 'Tayyorlanmoqda', 'ru': 'Готовится'},
            'ready': {'uz': 'Tayyor', 'ru': 'Готов'},
            'delivered': {'uz': 'Yetkazib berilgan', 'ru': 'Доставлен'},
            'cancelled': {'uz': 'Bekor qilingan', 'ru': 'Отменен'},
        }

        status = status_messages.get(order.status, {'uz': 'Noma\'lum', 'ru': 'Неизвестно'})

        if lang_code == "uz":
            text = (
                f"Buyurtma raqami: #{order.id}\n"
                f"Holati: {status['uz']}\n"
                f"Jami narx: {order.total_price} so'm\n"
                f"Sana: {order.created_at.strftime('%d.%m.%Y %H:%M')}"
            )
        else:
            text = (
                f"Номер заказа: #{order.id}\n"
                f"Статус: {status['ru']}\n"
                f"Общая сумма: {order.total_price} сум\n"
                f"Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}"
            )

        await message.answer(text)

    except Exception as e:
        if lang_code == "uz":
            text = "Xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
        else:
            text = "Произошла ошибка. Пожалуйста, попробуйте еще раз."
        await message.answer(text)

@dp.message(lambda message: message.text in ["💬 Aloqa", "💬 Контакты", "💬 Contact"])
async def handle_contact(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'en')
    contact_text = CONTACT_MESSAGES.get(lang, CONTACT_MESSAGES['en'])
    await message.answer(contact_text, reply_markup=get_main_keyboard(lang))

@dp.message(lambda message: message.text in ["🌐 Tilni o'zgartirish", "🌐 Сменить язык"])
async def handle_language_change(message: types.Message):
    start_message = (
        "🌐 Tilni tanlang / Выберите язык "
    )
    await message.answer(start_message, reply_markup=get_language_keyboard())

@dp.message(lambda message: message.text in ["⬅️ Orqaga", "⬅️ Назад", "⬅️ Back"])
async def handle_back(message: types.Message):
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(message.from_user.id, 'uz')

    # Get active categories
    categories = Category.objects.filter(is_available=True).all()

    if not categories:
        if lang_code == "uz":
            await message.answer("Hozircha kategoriyalar mavjud emas.")
        else:
            await message.answer("Пока нет доступных категорий.")
        return

    # Create keyboard based on language
    keyboard = get_categories_keyboard(categories, lang_code)

    # Send message based on language
    if lang_code == "uz":
        text = "Kategoriyalardan birini tanlang:"
    else:
        text = "Выберите категорию:"

    await message.answer(text, reply_markup=keyboard)

@dp.message()
async def handle_category(message: types.Message):
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(message.from_user.id, 'uz')

    # Check if user is in order process
    if message.from_user.id in user_order_states:
        return

    # Try to find category by name in both languages
    category = await sync_to_async(Category.objects.filter(
        Q(name_uz=message.text) | Q(name_ru=message.text)
    ).first)()

    if not category:
        if lang_code == "uz":
            await message.answer("Kategoriya topilmadi.")
        else:
            await message.answer("Категория не найдена.")
        return

    # Get products for this category
    products = await sync_to_async(list)(Product.objects.filter(category=category))

    if not products:
        if lang_code == "uz":
            await message.answer("Bu kategoriyada mahsulotlar mavjud emas.")
        else:
            await message.answer("В этой категории нет товаров.")
        return

    # Create keyboard based on language
    keyboard = get_products_keyboard(products, lang_code)

    # Send message based on language
    if lang_code == "uz":
        text = "Mahsulotlardan birini tanlang:"
    else:
        text = "Выберите товар:"

    await message.answer(text, reply_markup=keyboard)

@dp.message()
async def handle_product(message: types.Message):
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(message.from_user.id, 'uz')

    # Try to find product by name in both languages
    product = await sync_to_async(Product.objects.filter(
        Q(name_uz=message.text) | Q(name_ru=message.text)
    ).first)()

    if not product:
        if lang_code == "uz":
            await message.answer("Mahsulot topilmadi.")
        else:
            await message.answer("Товар не найден.")
        return

    # Get product details based on language
    if lang_code == "uz":
        text = f"<b>{product.name_uz}</b>\n\n{product.description_uz}\n\nNarxi: {product.price} so'm"
        print("slkdfjskldfjks")
    else:
        text = f"<b>{product.name_ru}</b>\n\n{product.description_ru}\n\nЦена: {product.price} сум"

    # Create keyboard with add to cart and back buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🛒 Savatga qo'shish" if lang_code == "uz" else "🛒 Добавить в корзину",
                callback_data=f"add_to_cart_{product.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga" if lang_code == "uz" else "⬅️ Назад",
                callback_data="back_to_products"
            )
        ]
    ])

    # Send product details with photo if available
    if product.image and product.image.url:
        try:
            # Get the full URL by combining MEDIA_URL and image path
            # image_url = f"{settings.DOMAIN}{product.image.url}"
            photo = FSInputFile(f'/home/ziko2/Desktop/fast_food/img/{product.name_uz}.jpg')
            await message.answer_photo(
                photo=photo,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception as e:
            # If there's an error with the image, just send the text
            print(e)
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(lambda c: c.data.startswith('add_to_cart_'))
async def handle_add_to_cart(callback_query: types.CallbackQuery):
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')
    user_id = callback_query.from_user.id

    # Get product ID from callback data
    product_id = int(callback_query.data.split('_')[-1])

    try:
        # Get product details
        product = await sync_to_async(Product.objects.get)(id=product_id)

        # Initialize cart if not exists
        if user_id not in user_carts:
            user_carts[user_id] = []

        # Check if product already exists in cart
        for item in user_carts[user_id]:
            if item['product_id'] == product.id:
                item['quantity'] += 1
                break
        else:
            # Add new product to cart if not found
            user_carts[user_id].append({
                'product_id': product.id,
                'name_uz': product.name_uz,
                'name_ru': product.name_ru,
                'price': product.price,
                'quantity': 1
            })

        # Create cart keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Savatni ko'rish" if lang_code == "uz" else "🛒 Посмотреть корзину",
                    callback_data="view_cart"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga" if lang_code == "uz" else "⬅️ Назад",
                    callback_data="back_to_categories"
                )
            ]
        ])

        await callback_query.message.delete()

        if lang_code == "uz":
            text = f"{product.name_uz} savatga qo'shildi!"
        else:
            text = f"{product.name_ru} добавлен в корзину!"

        # Check if the message is a photo message
        if callback_query.message.photo:
            # For photo messages, send a new message instead of editing
            await callback_query.message.answer(text, reply_markup=keyboard)
        else:
            # For text messages, edit the existing message
            await callback_query.message.edit_text(text, reply_markup=keyboard)
            
        await callback_query.answer()
    except Exception as e:
        logging.error(f"Error adding to cart: {str(e)}")
        if lang_code == "uz":
            # For photo messages, send a new message instead of editing
            if callback_query.message.photo:
                await callback_query.message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
            else:
                await callback_query.message.edit_text("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        else:
            # For photo messages, send a new message instead of editing
            if callback_query.message.photo:
                await callback_query.message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз.")
            else:
                await callback_query.message.edit_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.")

@dp.callback_query(lambda c: c.data == "view_cart")
async def handle_view_cart(callback_query: types.CallbackQuery):
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')
    user_id = callback_query.from_user.id

    # Check if cart is empty
    if user_id not in user_carts or not user_carts[user_id]:
        if lang_code == "uz":
            text = "Savat bo'sh!"
        else:
            text = "Корзина пуста!"
        await callback_query.message.edit_text(text)
        await callback_query.answer()
        return

    # Calculate total
    total = sum(item['price'] * item['quantity'] for item in user_carts[user_id])

    # Format cart items
    if lang_code == "uz":
        text = "🛒 Savatingiz:\n\n"
        for item in user_carts[user_id]:
            text += f"{item['name_uz']} x {item['quantity']} = {item['price'] * item['quantity']} so'm\n"
        text += f"\nJami: {total} so'm"
    else:
        text = "🛒 Ваша корзина:\n\n"
        for item in user_carts[user_id]:
            text += f"{item['name_ru']} x {item['quantity']} = {item['price'] * item['quantity']} сум\n"
        text += f"\nИтого: {total} сум"

    # Create cart keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Buyurtma berish" if lang_code == "uz" else "✅ Оформить заказ",
                callback_data="checkout"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Savatni tozalash" if lang_code == "uz" else "❌ Очистить корзину",
                callback_data="clear_cart"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga" if lang_code == "uz" else "⬅️ Назад",
                callback_data="back_to_categories"
            )
        ]
    ])

    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "clear_cart")
async def handle_clear_cart(callback_query: types.CallbackQuery):
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')
    user_id = callback_query.from_user.id

    # Clear cart
    if user_id in user_carts:
        del user_carts[user_id]

    if lang_code == "uz":
        text = "Savat tozalandi!"
    else:
        text = "Корзина очищена!"

    await callback_query.message.answer(text)
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "checkout")
async def handle_checkout(callback_query: types.CallbackQuery):
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')
    user_id = callback_query.from_user.id

    # Check if cart is empty
    if user_id not in user_carts or not user_carts[user_id]:
        if lang_code == "uz":
            text = "Savat bo'sh!"
        else:
            text = "Корзина пуста!"
        await callback_query.message.answer(text)
        await callback_query.answer()
        return

    # Set order state to 'phone'
    user_order_states[user_id] = 'phone'

    # Create keyboard with contact sharing button
    contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="📱 Raqamni ulashish" if lang_code == "uz" else "📱 Поделиться номером",
                request_contact=True
            )]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    # Ask for phone number with contact sharing button
    if lang_code == "uz":
        text = "Iltimos, telefon raqamingizni yuboring:"
    else:
        text = "Пожалуйста, отправьте ваш номер телефона:"

    await callback_query.message.answer(text, reply_markup=contact_keyboard)
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "back_to_categories")
async def handle_back_to_categories(callback_query: types.CallbackQuery):
    # Get user's language from memory or default to 'uz'
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')

    try:
        # Get all categories
        categories = await sync_to_async(list)(Category.objects.all())

        if not categories:
            if lang_code == "uz":
                await callback_query.message.edit_text("Hozircha kategoriyalar mavjud emas.")
            else:
                await callback_query.message.edit_text("Пока нет доступных категорий.")
            return

        # Create keyboard based on language
        keyboard = get_categories_keyboard(categories, lang_code)

        # Send message based on language
        if lang_code == "uz":
            text = "Kategoriyalardan birini tanlang:"
        else:
            text = "Выберите категорию:"

        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer()
    except Exception as e:
        logging.error(f"Error in back_to_categories: {str(e)}")
        if lang_code == "uz":
            await callback_query.message.edit_text("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        else:
            await callback_query.message.edit_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        await callback_query.answer()

async def main():
    logging.info("Starting bot...")
    # Reload environment variables before starting the bot
    load_dotenv(override=True)
    # Get the latest bot token
    global bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN not found in environment variables. Please check your .env file.")
        return
    # Create a new bot instance with the latest token
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)

class Command(BaseCommand):
    help = 'Starts the Telegram bot using aiogram'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting bot server...'))
        
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Bot stopped'))
            sys.exit(0) 