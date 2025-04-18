from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import Category, Product, Order, OrderItem, Language, TelegramUser
import random
from faker import Faker
from datetime import timedelta

fake = Faker()

class Command(BaseCommand):
    help = 'Generates test data for the database'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=5, help='Number of users to create')
        parser.add_argument('--categories', type=int, default=3, help='Number of categories to create')
        parser.add_argument('--products', type=int, default=10, help='Number of products to create')
        parser.add_argument('--orders', type=int, default=15, help='Number of orders to create')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to generate test data...'))

        # Create languages
        languages = []
        language_data = [
            {'code': 'uz', 'name': 'O\'zbekcha'},
            {'code': 'ru', 'name': 'Русский'}
        ]
        for lang in language_data:
            language, created = Language.objects.get_or_create(
                code=lang['code'],
                defaults={'name': lang['name']}
            )
            languages.append(language)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created language: {language.name}'))

        # Create telegram users
        users = []
        for _ in range(options['users']):
            user = TelegramUser.objects.create(
                user_id=random.randint(10000000, 99999999),
                username=fake.user_name(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                language=random.choice(languages),
                is_active=True
            )
            users.append(user)
            self.stdout.write(self.style.SUCCESS(f'Created telegram user: {user.username}'))

        # Create categories
        categories = []
        category_names = [
            {'uz': 'Burgerlar', 'ru': 'Бургеры'},
            {'uz': 'Pitsalar', 'ru': 'Пиццы'},
            {'uz': 'Ichimliklar', 'ru': 'Напитки'},
            {'uz': 'Shirinliklar', 'ru': 'Десерты'},
            {'uz': 'Garnirlar', 'ru': 'Гарниры'}
        ]
        for name in category_names[:options['categories']]:
            category = Category.objects.create(
                name_uz=name['uz'],
                name_ru=name['ru'],
                image='categories/default.jpg'
            )
            categories.append(category)
            self.stdout.write(self.style.SUCCESS(f'Created category: {category.name_uz}'))

        # Create products
        products = []
        product_names = [
            {'uz': 'Gamburger', 'ru': 'Гамбургер'},
            {'uz': 'Chizburger', 'ru': 'Чизбургер'},
            {'uz': 'Margarita pitsa', 'ru': 'Пицца Маргарита'},
            {'uz': 'Pepperoni pitsa', 'ru': 'Пицца Пепперони'},
            {'uz': 'Kola', 'ru': 'Кола'},
            {'uz': 'Fanta', 'ru': 'Фанта'},
            {'uz': 'Kartoshka fri', 'ru': 'Картофель фри'},
            {'uz': 'Nagets', 'ru': 'Наггетсы'}
        ]
        for _ in range(options['products']):
            name = random.choice(product_names)
            product = Product.objects.create(
                name_uz=name['uz'],
                name_ru=name['ru'],
                description_uz=fake.text(),
                description_ru=fake.text(),
                price=random.randint(10000, 50000),
                category=random.choice(categories),
                image='products/default.jpg',
                is_available=random.choice([True, False])
            )
            products.append(product)
            self.stdout.write(self.style.SUCCESS(f'Created product: {product.name_uz}'))

        # Create orders
        order_statuses = ['pending', 'processing', 'delivering', 'delivered', 'cancelled']
        for _ in range(options['orders']):
            order = Order.objects.create(
                user=random.choice(users),
                total_price=0,
                status=random.choice(order_statuses),
                created_at=timezone.now() - timedelta(days=random.randint(0, 30))
            )

            # Create order items
            num_items = random.randint(1, 5)
            total_price = 0
            for _ in range(num_items):
                product = random.choice(products)
                quantity = random.randint(1, 3)
                price = product.price * quantity
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price
                )
                total_price += price

            order.total_price = total_price
            order.save()
            self.stdout.write(self.style.SUCCESS(f'Created order #{order.id}'))

        self.stdout.write(self.style.SUCCESS('Successfully generated test data!')) 