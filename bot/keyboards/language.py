from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Til tanlash klaviaturasini yaratish
def get_language_keyboard():
    # O'zbek va rus tillari uchun tugmalar yaratish
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
        ]
    ])
    return keyboard 