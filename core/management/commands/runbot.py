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

# Logging sozlamalari - xatoliklarni kuzatish uchun
logging.basicConfig(level=logging.INFO)

# Muhit o'zgaruvchilarini yangi qiymatlar bilan yuklash
load_dotenv(override=True)

# Bot tokenini muhit o'zgaruvchilaridan olish
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logging.error("BOT_TOKEN muhit o'zgaruvchilarida topilmadi. .env faylini tekshiring.")
    sys.exit(1)

# Bot va dispatcher ni ishga tushirish
dp = Dispatcher()

# Til tanlash klaviaturasini yaratish - foydalanuvchiga til tanlash imkoniyatini beradi
def get_language_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
        ]
    ])
    return keyboard

# Har xil tillar uchun asosiy menyu klaviaturalari - foydalanuvchi interfeysini yaratish
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

# Har xil tillardagi xush kelibsiz xabarlari - foydalanuvchiga dastur haqida ma'lumot berish
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

# Har xil tillardagi menyu xabarlari - menyu yuklanishini bildirish
MENU_MESSAGES = {
    'uz': "Menyu ko'rsatilmoqda...",
    'ru': "Меню загружается..."
}

# Har xil tillardagi buyurtma xabarlari - buyurtma jarayonini bildirish
ORDER_MESSAGES = {
    'uz': "Buyurtma berish jarayoni boshlanmoqda...",
    'ru': "Процесс оформления заказа начинается..."
}

# Har xil tillardagi holat xabarlari - buyurtma holatini tekshirish
STATUS_MESSAGES = {
    'uz': "Buyurtma holati tekshirilmoqda...",
    'ru': "Проверка статуса заказа..."
}

# Har xil tillardagi aloqa xabarlari - aloqa ma'lumotlarini ko'rsatish
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

# Foydalanuvchi til sozlamalarini saqlash - har bir foydalanuvchi uchun tanlangan tilni saqlash
user_languages = {}

# Foydalanuvchi savat ma'lumotlarini saqlash - har bir foydalanuvchi uchun savatdagi mahsulotlarni saqlash
user_carts = {}

# Foydalanuvchi buyurtma holatini saqlash - har bir foydalanuvchi uchun buyurtma jarayonini kuzatish
user_order_states = {}

# /start buyrug'ini qayta ishlash - foydalanuvchi botni ishga tushganda
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    start_message = (
        "🌐 Tilni tanlang / Выберите язык "
    )
    await message.answer(start_message, reply_markup=get_language_keyboard())

# Til tanlashni qayta ishlash - foydalanuvchi tilni o'zgartirganda
@dp.callback_query(lambda c: c.data.startswith('lang_'))
async def process_language_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = callback_query.data.split('_')[1]
    
    try:
        # Foydalanuvchi tilini ma'lumotlar bazasida yangilash
        user = await TelegramUser.objects.aget(user_id=user_id)
        language = await Language.objects.aget(code=lang)
        user.language = language
        await user.asave()
        
        # Tilni xotiraga saqlash
        user_languages[user_id] = lang
        
        # Yangi tilda tasdiqlash xabarini yuborish
        if lang == 'uz':
            text = "✅ Til muvaffaqiyatli o'zgartirildi!"
        else:
            text = "✅ Язык успешно изменен!"
        
        # Xabarni yangi klaviatura bilan yangilash
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
        
        # Yangi tilda asosiy menyuni yuborish
        await callback_query.message.answer(
            "Bosh menyu:" if lang == 'uz' else "Главное меню:",
            reply_markup=get_main_keyboard(lang)
        )
        
    except Exception as e:
        logging.error(f"Tilni o'zgartirishda xatolik: {str(e)}")
        if lang == 'uz':
            text = "❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
        else:
            text = "❌ Произошла ошибка. Пожалуйста, попробуйте еще раз."
        await callback_query.message.edit_text(text)
    
    await callback_query.answer()

# Kategoriyalar klaviaturasini yaratish - mahsulot kategoriyalarini ko'rsatish uchun
def get_categories_keyboard(categories, lang_code, show_back=False):
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        # Tilga qarab mos nomni ishlatish
        name = category.name_uz if lang_code == "uz" else category.name_ru
        builder.add(InlineKeyboardButton(
            text=name,
            callback_data=f"category_{category.id}"
        ))
    
    # Orqaga tugmasini faqat show_back=True bo'lganda qo'shish
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
    
    builder.adjust(2)  # Tugmalarni 2 ustunda joylashtirish
    return builder.as_markup()

# Mahsulotlar klaviaturasini yaratish - kategoriyadagi mahsulotlarni ko'rsatish uchun
def get_products_keyboard(products, lang_code):
    builder = InlineKeyboardBuilder()
    
    for product in products:
        # Tilga qarab mos nomni ishlatish
        name = product.name_uz if lang_code == "uz" else product.name_ru
        builder.add(InlineKeyboardButton(
            text=name,
            callback_data=f"product_{product.id}"
        ))
    
    # Orqaga tugmasini qo'shish
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
    
    builder.adjust(2)  # Tugmalarni 2 ustunda joylashtirish
    return builder.as_markup()

# Asosiy menyuni qayta ishlash - foydalanuvchi asosiy menyuga qaytganda
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
    
    # Tilga qarab xabar yuborish
    if language == 'uz':
        text = "Kategoriyalardan birini tanlang:"
    else:
        text = "Выберите категорию:"
    
    await message.answer(text, reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith('category_'))
async def handle_category(callback_query: types.CallbackQuery):
    category_id = int(callback_query.data.split("_")[1])
    
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')

    try:
        # Kategoriya va uning mahsulotlarini sync_to_async yordamida olish
        get_category = sync_to_async(Category.objects.get)
        get_products = sync_to_async(lambda: list(Product.objects.filter(category_id=category_id, is_available=True)))
        
        category = await get_category(id=category_id)
        products = await get_products()

        if not products:
            if lang_code == "uz":
                text = f"{category.name_uz} kategoriyasida hozircha mahsulotlar mavjud emas."
            else:
                text = f"В категории {category.name_ru} пока нет доступных продуктов."
            
            # Xabar rasmlar bilan bo'lsa
            if callback_query.message.photo:
                # Rasmlar bilan xabarlar uchun yangi xabar yuborish
                await callback_query.message.answer(text)
            else:
                # Matnli xabarlar uchun mavjud xabarni o'zgartirish
                await callback_query.message.edit_text(text)
            return

        # Tilga qarab klaviaturani yaratish
        keyboard = get_products_keyboard(products, lang_code)

        # Tilga qarab xabar yuborish
        if lang_code == "uz":
            text = f"{category.name_uz} kategoriyasidagi mahsulotlar:"
        else:
            text = f"Продукты категории {category.name_ru}:"
        
        # Xabar rasmlar bilan bo'lsa
        if callback_query.message.photo:
            # Rasmlar bilan xabarlar uchun yangi xabar yuborish
            await callback_query.message.answer(text, reply_markup=keyboard)
        else:
            # Matnli xabarlar uchun mavjud xabarni o'zgartirish
            await callback_query.message.edit_text(text, reply_markup=keyboard)
            
        await callback_query.answer()
        
    except Exception as e:
        logging.error(f"Kategoriyani qayta ishlashda xatolik: {str(e)}")
        if lang_code == "uz":
            await callback_query.message.edit_text("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        else:
            await callback_query.message.edit_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        await callback_query.answer()

@dp.callback_query(lambda c: c.data in ["back_to_products"])
async def handle_back(callback_query: types.CallbackQuery, bot: Bot):
    category_id = int(1)
    
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')

    try:
        # Kategoriya va uning mahsulotlarini sync_to_async yordamida olish
        get_category = sync_to_async(Category.objects.get)
        get_products = sync_to_async(lambda: list(Product.objects.filter(category_id=category_id, is_available=True)))
        
        category = await get_category(id=category_id)
        products = await get_products()

        if not products:
            if lang_code == "uz":
                text = f"{category.name_uz} kategoriyasida hozircha mahsulotlar mavjud emas."
            else:
                text = f"В категории {category.name_ru} пока нет доступных продуктов."
            
            # Xabar rasmlar bilan bo'lsa
            if callback_query.message.photo:
                # Rasmlar bilan xabarlar uchun yangi xabar yuborish
                await callback_query.message.answer(text)
            else:
                # Matnli xabarlar uchun mavjud xabarni o'zgartirish
                await callback_query.message.edit_text(text)
            return

        # Tilga qarab klaviaturani yaratish
        keyboard = get_products_keyboard(products, lang_code)

        # Tilga qarab xabar yuborish
        if lang_code == "uz":
            text = f"{category.name_uz} kategoriyasidagi mahsulotlar:"
        else:
            text = f"Продукты категории {category.name_ru}:"
        await callback_query.message.delete()
        # Xabar rasmlar bilan bo'lsa
        if callback_query.message.photo:
            # Rasmlar bilan xabarlar uchun yangi xabar yuborish
            await callback_query.message.answer(text, reply_markup=keyboard)
        else:
            # Matnli xabarlar uchun mavjud xabarni o'zgartirish
            await callback_query.message.edit_text(text, reply_markup=keyboard)
            
        await callback_query.answer()
    except Exception as e:
        logging.error(f"Orqaga qaytishda xatolik: {str(e)}")
        if lang_code == "uz":
            error_text = "Xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
        else:
            error_text = "Произошла ошибка. Пожалуйста, попробуйте еще раз."
            
        # Xabar rasmlar bilan bo'lsa
        if callback_query.message.photo:
            # Rasmlar bilan xabarlar uchun yangi xabar yuborish
            await callback_query.message.answer(error_text)
        else:
            # Matnli xabarlar uchun mavjud xabarni o'zgartirish
            await callback_query.message.edit_text(error_text)
            
        await callback_query.answer()

@dp.message(lambda message: message.text in ["🛒 Savat", "🛒 Корзина"])
async def handle_cart(message: types.Message):
    user_id = message.from_user.id
    language = user_languages.get(user_id, 'uz')
    
    # Savat mavjudligini va unda mahsulotlar borligini tekshirish
    if user_id not in user_carts or not user_carts[user_id]:
        if language == 'uz':
            await message.answer("Savat bo'sh")
        else:
            await message.answer("Корзина пуста")
        return
    
    # Jami summani hisoblash va savat mahsulotlarini formatlash
    total = 0
    text = "🛒 Savatingiz:\n\n" if language == 'uz' else "🛒 Ваша корзина:\n\n"
    
    # Bir xil mahsulotlarni guruhlash va ularning jami summasini hisoblash
    for item in user_carts[user_id]:
        product_name = item['name_uz'] if language == 'uz' else item['name_ru']
        item_total = item['price'] * item['quantity']
        total += item_total
        text += f"{product_name} x {item['quantity']} = {item_total:,.2f} so'm\n"
    
    text += f"\nJami: {total:,.2f} so'm"
    
    # Amallar tugmalari bilan klaviaturani yaratish
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
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(message.from_user.id, 'uz')

    # Barcha kategoriyalarni olish
    categories = await sync_to_async(list)(Category.objects.all())

    if not categories:
        if lang_code == "uz":
            await message.answer("Hozircha kategoriyalar mavjud emas.")
        else:
            await message.answer("Пока нет доступных категорий.")
        return

    # Asosiy menyu uchun show_back=False bilan tilga qarab klaviaturani yaratish
    keyboard = get_categories_keyboard(categories, lang_code, show_back=False)

    # Tilga qarab xabar yuborish
    if lang_code == "uz":
        text = "Kategoriyalardan birini tanlang:"
    else:
        text = "Выберите категорию:"

    await message.answer(text, reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith('product_'))
async def handle_product_callback(callback_query: types.CallbackQuery):
    product_id = int(callback_query.data.split("_")[1])
    
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')

    # Mahsulot ma'lumotlarini olish
    product = await sync_to_async(Product.objects.get)(id=product_id)
    
    # Tilga qarab xabarni formatlash
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

    # Savatga qo'shish va orqaga tugmalari bilan klaviaturani yaratish
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

    # Oldingi mahsulotlar ro'yxati xabarini o'chirish
    await callback_query.message.delete()

    # Mahsulot ma'lumotlarini rasmi bilan yuborish
    if product.image and product.image.url:
        try:
            # MEDIA_URL va rasm yo'lini birlashtirib to'liq URL ni olish
            # image_url = f"{settings.DOMAIN}{product.image.url}"
            photo = FSInputFile(f'/home/ziko2/Desktop/fast_food/img/{product.name_uz}.jpg')
            await callback_query.message.answer_photo(
                photo=photo,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception as e:
            # Agar rasm bilan bog'liq xatolik bo'lsa, faqat matnni yuborish
            print(e)
            await callback_query.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await callback_query.message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    await callback_query.answer()

@dp.callback_query(lambda c: c.data in ["back_to_menu", "back_to_categories"])
async def handle_back(callback_query: types.CallbackQuery):
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')

    # Faol kategoriyalarni olish
    categories = await sync_to_async(list)(Category.objects.all())

    # Tilga qarab klaviaturani yaratish
    keyboard = get_categories_keyboard(categories, lang_code)

    # Tilga qarab xabar yuborish
    if lang_code == "uz":
        text = "Kategoriyalardan birini tanlang:"
    else:
        text = "Выберите категорию:"

    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer()

@dp.message(lambda message: message.text in ["🛒 Buyurtma", "🛒 Заказать", "🛒 Order"])
async def handle_order(message: types.Message):
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(message.from_user.id, 'uz')

    # Agar savat mavjud bo'lmasa, yangi savat yaratish
    if message.from_user.id not in user_carts:
        user_carts[message.from_user.id] = []

    # Buyurtma holatini 'phone' ga o'rnatish
    user_order_states[message.from_user.id] = 'phone'

    # Raqamni ulashish tugmasi bilan klaviaturani yaratish
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

    # Raqamni ulashish tugmasi bilan telefon raqamini so'rash
    if lang_code == "uz":
        text = "Iltimos, telefon raqamingizni yuboring:"
    else:
        text = "Пожалуйста, отправьте ваш номер телефона:"

    await message.answer(text, reply_markup=contact_keyboard)

@dp.message(lambda message: message.contact is not None or message.text or message.location)
async def handle_order_info(message: types.Message):
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(message.from_user.id, 'uz')
    user_id = message.from_user.id

    # Foydalanuvchi buyurtma jarayonida ekanligini tekshirish
    if user_id not in user_order_states:
        return

    state = user_order_states[user_id]

    if state == 'phone':
        # Xabar aloqa ma'lumotlarini o'z ichiga olganligini tekshirish
        if message.contact is not None:
            phone = message.contact.phone_number
        else:
            # Qo'lda kiritilgan telefon raqamini tekshirish
            phone = message.text.strip()
            if not phone.isdigit() or len(phone) < 9:
                if lang_code == "uz":
                    await message.answer("Iltimos, to'g'ri telefon raqam kiriting yoki 'Raqamni ulashish' tugmasini bosing!")
                else:
                    await message.answer("Пожалуйста, введите правильный номер телефона или нажмите кнопку 'Поделиться номером'!")
                return

        # Telefon raqamini saqlash va manzilni so'rash
        user_order_states[f"{user_id}_phone"] = phone
        user_order_states[user_id] = 'address'
        
        # Joylashuvni ulashish tugmasi bilan klaviaturani yaratish
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
        # Manzilni saqlash va izoh so'rash
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
        # Buyurtmani yaratish
        try:
            # Foydalanuvchini olish yoki yaratish
            user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
                user_id=user_id,
                defaults={
                    'username': message.from_user.username,
                    'first_name': message.from_user.first_name,
                    'last_name': message.from_user.last_name,
                    'language': await sync_to_async(Language.objects.get)(code=lang_code) if lang_code else None
                }
            )
            
            # Buyurtmani yaratish
            order = await sync_to_async(Order.objects.create)(
                user=user,
                phone_number=user_order_states.get(f"{user_id}_phone", ""),
                address=user_order_states.get(f"{user_id}_address", ""),
                comment=message.text,
                total_price=sum(item['price'] * item['quantity'] for item in user_carts[user_id])
            )

            # Buyurtma elementlarini yaratish
            for item in user_carts[user_id]:
                await sync_to_async(OrderItem.objects.create)(
                    order=order,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    price=item['price']
                )

            # Savat va buyurtma holatini tozalash
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
            logging.error(f"Buyurtma yaratishda xatolik: {str(e)}")
            if lang_code == "uz":
                text = f"Xatolik yuz berdi: {str(e)}. Iltimos, qayta urinib ko'ring."
            else:
                text = f"Произошла ошибка: {str(e)}. Пожалуйста, попробуйте еще раз."
            await message.answer(text)

@dp.message(lambda message: message.text in ["📍 Buyurtma holati", "📍 Статус заказа", "📍 Order Status"])
async def handle_status(message: types.Message):
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(message.from_user.id, 'uz')
    user_id = message.from_user.id

    try:
        # Foydalanuvchining oxirgi buyurtmasini olish
        user = await sync_to_async(TelegramUser.objects.get)(user_id=user_id)
        order = await sync_to_async(Order.objects.filter(user=user).order_by('-created_at').first)()

        if not order:
            if lang_code == "uz":
                text = "Sizda hali buyurtmalar mavjud emas."
            else:
                text = "У вас пока нет заказов."
            await message.answer(text)
            return

        # Holat xabarini formatlash
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
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(message.from_user.id, 'uz')

    # Faol kategoriyalarni olish
    categories = Category.objects.filter(is_available=True).all()

    if not categories:
        if lang_code == "uz":
            await message.answer("Hozircha kategoriyalar mavjud emas.")
        else:
            await message.answer("Пока нет доступных категорий.")
        return

    # Tilga qarab klaviaturani yaratish
    keyboard = get_categories_keyboard(categories, lang_code)

    # Tilga qarab xabar yuborish
    if lang_code == "uz":
        text = "Kategoriyalardan birini tanlang:"
    else:
        text = "Выберите категорию:"

    await message.answer(text, reply_markup=keyboard)

@dp.message()
async def handle_category(message: types.Message):
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(message.from_user.id, 'uz')

    # Foydalanuvchi buyurtma jarayonida ekanligini tekshirish
    if message.from_user.id in user_order_states:
        return

    # Har ikkala tilda kategoriya nomini qidirish
    category = await sync_to_async(Category.objects.filter(
        Q(name_uz=message.text) | Q(name_ru=message.text)
    ).first)()

    if not category:
        if lang_code == "uz":
            await message.answer("Kategoriya topilmadi.")
        else:
            await message.answer("Категория не найдена.")
        return

    # Bu kategoriya uchun mahsulotlarni olish
    products = await sync_to_async(list)(Product.objects.filter(category=category))

    if not products:
        if lang_code == "uz":
            await message.answer("Bu kategoriyada mahsulotlar mavjud emas.")
        else:
            await message.answer("В этой категории нет товаров.")
        return

    # Tilga qarab klaviaturani yaratish
    keyboard = get_products_keyboard(products, lang_code)

    # Tilga qarab xabar yuborish
    if lang_code == "uz":
        text = "Mahsulotlardan birini tanlang:"
    else:
        text = "Выберите товар:"

    await message.answer(text, reply_markup=keyboard)

@dp.message()
async def handle_product(message: types.Message):
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(message.from_user.id, 'uz')

    # Har ikkala tilda mahsulot nomini qidirish
    product = await sync_to_async(Product.objects.filter(
        Q(name_uz=message.text) | Q(name_ru=message.text)
    ).first)()

    if not product:
        if lang_code == "uz":
            await message.answer("Mahsulot topilmadi.")
        else:
            await message.answer("Товар не найден.")
        return

    # Tilga qarab mahsulot ma'lumotlarini olish
    if lang_code == "uz":
        text = f"<b>{product.name_uz}</b>\n\n{product.description_uz}\n\nNarxi: {product.price} so'm"
        print("slkdfjskldfjks")
    else:
        text = f"<b>{product.name_ru}</b>\n\n{product.description_ru}\n\nЦена: {product.price} сум"

    # Savatga qo'shish va orqaga tugmalari bilan klaviaturani yaratish
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

    # Mahsulot ma'lumotlarini rasmi bilan yuborish
    if product.image and product.image.url:
        try:
            # MEDIA_URL va rasm yo'lini birlashtirib to'liq URL ni olish
            # image_url = f"{settings.DOMAIN}{product.image.url}"
            photo = FSInputFile(f'/home/ziko2/Desktop/fast_food/img/{product.name_uz}.jpg')
            await message.answer_photo(
                photo=photo,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception as e:
            # Agar rasm bilan bog'liq xatolik bo'lsa, faqat matnni yuborish
            print(e)
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(lambda c: c.data.startswith('add_to_cart_'))
async def handle_add_to_cart(callback_query: types.CallbackQuery):
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')
    user_id = callback_query.from_user.id

    # Callback ma'lumotlaridan mahsulot ID sini olish
    product_id = int(callback_query.data.split('_')[-1])

    try:
        # Mahsulot ma'lumotlarini olish
        product = await sync_to_async(Product.objects.get)(id=product_id)

        # Agar savat mavjud bo'lmasa, yangi savat yaratish
        if user_id not in user_carts:
            user_carts[user_id] = []

        # Mahsulot allaqachon savatda borligini tekshirish
        for item in user_carts[user_id]:
            if item['product_id'] == product.id:
                item['quantity'] += 1
                break
        else:
            # Agar mahsulot topilmasa, yangi mahsulotni savatga qo'shish
            user_carts[user_id].append({
                'product_id': product.id,
                'name_uz': product.name_uz,
                'name_ru': product.name_ru,
                'price': product.price,
                'quantity': 1
            })

        # Savat klaviaturasini yaratish
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

        # Xabar rasmlar bilan bo'lsa
        if callback_query.message.photo:
            # Rasmlar bilan xabarlar uchun yangi xabar yuborish
            await callback_query.message.answer(text, reply_markup=keyboard)
        else:
            # Matnli xabarlar uchun mavjud xabarni o'zgartirish
            await callback_query.message.edit_text(text, reply_markup=keyboard)
            
        await callback_query.answer()
    except Exception as e:
        logging.error(f"Savatga qo'shishda xatolik: {str(e)}")
        if lang_code == "uz":
            # Rasmlar bilan xabarlar uchun yangi xabar yuborish
            if callback_query.message.photo:
                await callback_query.message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
            else:
                await callback_query.message.edit_text("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        else:
            # Rasmlar bilan xabarlar uchun yangi xabar yuborish
            if callback_query.message.photo:
                await callback_query.message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз.")
            else:
                await callback_query.message.edit_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.")

@dp.callback_query(lambda c: c.data == "view_cart")
async def handle_view_cart(callback_query: types.CallbackQuery):
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')
    user_id = callback_query.from_user.id

    # Savat bo'shligini tekshirish
    if user_id not in user_carts or not user_carts[user_id]:
        if lang_code == "uz":
            text = "Savat bo'sh!"
        else:
            text = "Корзина пуста!"
        await callback_query.message.edit_text(text)
        await callback_query.answer()
        return

    # Jami summani hisoblash
    total = sum(item['price'] * item['quantity'] for item in user_carts[user_id])

    # Savat elementlarini formatlash
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

    # Savat klaviaturasini yaratish
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
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')
    user_id = callback_query.from_user.id

    # Savatni tozalash
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
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')
    user_id = callback_query.from_user.id

    # Savat bo'shligini tekshirish
    if user_id not in user_carts or not user_carts[user_id]:
        if lang_code == "uz":
            text = "Savat bo'sh!"
        else:
            text = "Корзина пуста!"
        await callback_query.message.answer(text)
        await callback_query.answer()
        return

    # Buyurtma holatini 'phone' ga o'rnatish
    user_order_states[user_id] = 'phone'

    # Raqamni ulashish tugmasi bilan klaviaturani yaratish
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

    # Raqamni ulashish tugmasi bilan telefon raqamini so'rash
    if lang_code == "uz":
        text = "Iltimos, telefon raqamingizni yuboring:"
    else:
        text = "Пожалуйста, отправьте ваш номер телефона:"

    await callback_query.message.answer(text, reply_markup=contact_keyboard)
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "back_to_categories")
async def handle_back_to_categories(callback_query: types.CallbackQuery):
    # Foydalanuvchi tilini xotira yoki standart 'uz' dan olish
    lang_code = user_languages.get(callback_query.from_user.id, 'uz')

    try:
        # Barcha kategoriyalarni olish
        categories = await sync_to_async(list)(Category.objects.all())

        if not categories:
            if lang_code == "uz":
                await callback_query.message.edit_text("Hozircha kategoriyalar mavjud emas.")
            else:
                await callback_query.message.edit_text("Пока нет доступных категорий.")
            return

        # Tilga qarab klaviaturani yaratish
        keyboard = get_categories_keyboard(categories, lang_code)

        # Tilga qarab xabar yuborish
        if lang_code == "uz":
            text = "Kategoriyalardan birini tanlang:"
        else:
            text = "Выберите категорию:"

        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer()
    except Exception as e:
        logging.error(f"Kategoriyalarga qaytishda xatolik: {str(e)}")
        if lang_code == "uz":
            await callback_query.message.edit_text("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        else:
            await callback_query.message.edit_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        await callback_query.answer()

async def main():
    logging.info("Bot ishga tushirilmoqda...")
    # Botni ishga tushirishdan oldin muhit o'zgaruvchilarini qayta yuklash
    load_dotenv(override=True)
    # Eng so'nggi bot tokenini olish
    global bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN muhit o'zgaruvchilarida topilmadi. .env faylini tekshiring.")
        return
    # Eng so'nggi token bilan yangi bot instansini yaratish
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)

class Command(BaseCommand):
    help = 'aiogram yordamida Telegram botini ishga tushirish'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Bot serveri ishga tushirilmoqda...'))
        
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Bot to\'xtatildi'))
            sys.exit(0) 