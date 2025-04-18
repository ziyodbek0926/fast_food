import os
import django
from django.contrib.auth.models import User

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.settings')
django.setup()

from core.models import Language, Category, Product, TelegramUser

def create_languages():
    languages = [
        {'code': 'uz', 'name': 'O\'zbekcha'},
        {'code': 'ru', 'name': 'Русский'},
    ]
    for lang in languages:
        Language.objects.get_or_create(**lang)

def create_categories():
    categories = [
        {
            'name_uz': 'Burgerlar',
            'name_ru': 'Бургеры',
        },
        {
            'name_uz': 'Pitsalar',
            'name_ru': 'Пиццы',
        },
        {
            'name_uz': 'Ichimliklar',
            'name_ru': 'Напитки',
        },
    ]
    for category in categories:
        Category.objects.get_or_create(**category)

def create_products():
    categories = Category.objects.all()
    
    products = [
        {
            'category': categories[0],  # Burgerlar
            'name_uz': 'Cheeseburger',
            'name_ru': 'Чизбургер',
            'description_uz': 'Mol go\'shti, pishloq, pomidor, salat bargi va maxsus sous',
            'description_ru': 'Говядина, сыр, помидор, лист салата и специальный соус',
            'price': 25000,
        },
        {
            'category': categories[0],  # Burgerlar
            'name_uz': 'Chicken Burger',
            'name_ru': 'Чикен Бургер',
            'description_uz': 'Tovuq go\'shti, pishloq, pomidor, salat bargi va maxsus sous',
            'description_ru': 'Куриное мясо, сыр, помидор, лист салата и специальный соус',
            'price': 22000,
        },
        {
            'category': categories[1],  # Pitsalar
            'name_uz': 'Margarita',
            'name_ru': 'Маргарита',
            'description_uz': 'Pishloq, pomidor sousi, zaytun moyi',
            'description_ru': 'Сыр, томатный соус, оливковое масло',
            'price': 45000,
        },
        {
            'category': categories[1],  # Pitsalar
            'name_uz': 'Pepperoni',
            'name_ru': 'Пепперони',
            'description_uz': 'Pishloq, pomidor sousi, pepperoni kolbasa',
            'description_ru': 'Сыр, томатный соус, колбаса пепперони',
            'price': 50000,
        },
        {
            'category': categories[2],  # Ichimliklar
            'name_uz': 'Coca-Cola',
            'name_ru': 'Кока-Кола',
            'description_uz': '0.5L',
            'description_ru': '0.5L',
            'price': 8000,
        },
        {
            'category': categories[2],  # Ichimliklar
            'name_uz': 'Fanta',
            'name_ru': 'Фанта',
            'description_uz': '0.5L',
            'description_ru': '0.5L',
            'price': 8000,
        },
    ]
    
    for product in products:
        Product.objects.get_or_create(**product)

def create_admin_user():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

if __name__ == '__main__':
    print("Creating languages...")
    create_languages()
    
    print("Creating categories...")
    create_categories()
    
    print("Creating products...")
    create_products()
    
    print("Creating admin user...")
    create_admin_user()
    
    print("Database initialization completed successfully!") 