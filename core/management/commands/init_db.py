# Ma'lumotlar bazasini ishga tushirish buyrug'i
# Bu buyruq dastlabki ma'lumotlarni yaratish uchun ishlatiladi
from django.core.management.base import BaseCommand
from core.models import Language, Category, Product

class Command(BaseCommand):
    help = 'Ma\'lumotlar bazasini dastlabki ma\'lumotlar bilan to\'ldirish'

    def handle(self, *args, **options):
        # Dastlabki tillarni yaratish
        self.stdout.write('Dastlabki tillarni yaratish...')
        languages = [
            {'code': 'uz', 'name': 'O\'zbek tili'},
            {'code': 'ru', 'name': 'Rus tili'},
        ]
        for lang in languages:
            Language.objects.get_or_create(**lang)
        self.stdout.write(self.style.SUCCESS('Tillar muvaffaqiyatli yaratildi'))

        # Dastlabki kategoriyalarni yaratish
        self.stdout.write('Dastlabki kategoriyalarni yaratish...')
        categories = [
            {
                'name_uz': 'Fast Food',
                'name_ru': 'Фаст Фуд',
                'description_uz': 'Tezkor ovqatlar',
                'description_ru': 'Быстрая еда',
                'is_active': True
            },
            {
                'name_uz': 'Ichimliklar',
                'name_ru': 'Напитки',
                'description_uz': 'Sovuq va issiq ichimliklar',
                'description_ru': 'Холодные и горячие напитки',
                'is_active': True
            },
            {
                'name_uz': 'Desertlar',
                'name_ru': 'Десерты',
                'description_uz': 'Shirinliklar',
                'description_ru': 'Сладости',
                'is_active': True
            }
        ]
        for cat in categories:
            Category.objects.get_or_create(**cat)
        self.stdout.write(self.style.SUCCESS('Kategoriyalar muvaffaqiyatli yaratildi'))

        # Dastlabki mahsulotlarni yaratish
        self.stdout.write('Dastlabki mahsulotlarni yaratish...')
        fast_food = Category.objects.get(name_uz='Fast Food')
        drinks = Category.objects.get(name_uz='Ichimliklar')
        desserts = Category.objects.get(name_uz='Desertlar')

        products = [
            {
                'category': fast_food,
                'name_uz': 'Lavash',
                'name_ru': 'Лаваш',
                'description_uz': 'Go\'shtli lavash',
                'description_ru': 'Лаваш с мясом',
                'price': 25000,
                'is_available': True
            },
            {
                'category': fast_food,
                'name_uz': 'Burger',
                'name_ru': 'Бургер',
                'description_uz': 'Klassik burger',
                'description_ru': 'Классический бургер',
                'price': 30000,
                'is_available': True
            },
            {
                'category': drinks,
                'name_uz': 'Coca-Cola',
                'name_ru': 'Кока-Кола',
                'description_uz': '0.5L',
                'description_ru': '0.5Л',
                'price': 8000,
                'is_available': True
            },
            {
                'category': drinks,
                'name_uz': 'Fanta',
                'name_ru': 'Фанта',
                'description_uz': '0.5L',
                'description_ru': '0.5Л',
                'price': 8000,
                'is_available': True
            },
            {
                'category': desserts,
                'name_uz': 'Pirojnoe',
                'name_ru': 'Пирожное',
                'description_uz': 'Shokoladli pirojnoe',
                'description_ru': 'Шоколадное пирожное',
                'price': 15000,
                'is_available': True
            }
        ]
        for prod in products:
            Product.objects.get_or_create(**prod)
        self.stdout.write(self.style.SUCCESS('Mahsulotlar muvaffaqiyatli yaratildi'))

        self.stdout.write(self.style.SUCCESS('Barcha dastlabki ma\'lumotlar muvaffaqiyatli yaratildi')) 