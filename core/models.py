from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# Til modeli - botda qo'llab-quvvatlanadigan tillarni saqlash uchun
class Language(models.Model):
    # Til kodi (masalan: 'uz', 'ru')
    code = models.CharField(max_length=2, unique=True)
    # Til nomi
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

# Kategoriya modeli - mahsulotlar toifalarini saqlash uchun
class Category(models.Model):
    # Kategoriya nomi o'zbek tilida
    name_uz = models.CharField(max_length=255)
    # Kategoriya nomi rus tilida
    name_ru = models.CharField(max_length=255)
    # Kategoriya tavsifi o'zbek tilida
    description_uz = models.TextField(blank=True, default='')
    # Kategoriya tavsifi rus tilida
    description_ru = models.TextField(blank=True, default='')
    # Kategoriya rasmi
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    # Kategoriya faol yoki faol emasligi
    is_active = models.BooleanField(default=True)
    # Yaratilgan vaqti
    created_at = models.DateTimeField(auto_now_add=True)
    # Yangilangan vaqti
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name_uz

# Mahsulot modeli - barcha mahsulotlarni saqlash uchun
class Product(models.Model):
    # Mahsulot qaysi kategoriyaga tegishli ekanligi
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    # Mahsulot nomi o'zbek tilida
    name_uz = models.CharField(max_length=255)
    # Mahsulot nomi rus tilida
    name_ru = models.CharField(max_length=255)
    # Mahsulot tavsifi o'zbek tilida
    description_uz = models.TextField(blank=True, default='')
    # Mahsulot tavsifi rus tilida
    description_ru = models.TextField(blank=True, default='')
    # Mahsulot narxi
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # Mahsulot rasmi
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    # Mahsulot mavjud yoki mavjud emasligi
    is_available = models.BooleanField(default=True)
    # Yaratilgan vaqti
    created_at = models.DateTimeField(auto_now_add=True)
    # Yangilangan vaqti
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name_uz

# Telegram foydalanuvchisi modeli - bot foydalanuvchilarini saqlash uchun
class TelegramUser(models.Model):
    # Telegram foydalanuvchi ID si
    user_id = models.BigIntegerField(unique=True)
    # Telegram foydalanuvchi nomi
    username = models.CharField(max_length=255, null=True, blank=True)
    # Foydalanuvchi ismi
    first_name = models.CharField(max_length=255, null=True, blank=True)
    # Foydalanuvchi familiyasi
    last_name = models.CharField(max_length=255, null=True, blank=True)
    # Foydalanuvchi tanlagan tili
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    # Yaratilgan vaqti
    created_at = models.DateTimeField(auto_now_add=True)
    # Yangilangan vaqti
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (@{self.username})"

# Buyurtma modeli - foydalanuvchilar buyurtmalarini saqlash uchun
class Order(models.Model):
    # Buyurtma holatlari
    STATUS_CHOICES = (
        ('new', _('New')),
        ('confirmed', _('Confirmed')),
        ('preparing', _('Preparing')),
        ('ready', _('Ready')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
    )

    # Buyurtma bergan foydalanuvchi
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='orders')
    # Buyurtma holati
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    # Buyurtma umumiy narxi
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Foydalanuvchi telefon raqami
    phone_number = models.CharField(max_length=20, default='')
    # Yetkazib berish manzili
    address = models.TextField(default='')
    # Buyurtma izohi
    comment = models.TextField(blank=True, default='')
    # Yaratilgan vaqti
    created_at = models.DateTimeField(auto_now_add=True)
    # Yangilangan vaqti
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user}"

# Buyurtma elementi modeli - buyurtmadagi har bir mahsulotni saqlash uchun
class OrderItem(models.Model):
    # Qaysi buyurtmaga tegishli ekanligi
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    # Qaysi mahsulot ekanligi
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    # Mahsulot soni
    quantity = models.PositiveIntegerField(default=1)
    # Mahsulot narxi
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # Yaratilgan vaqti
    created_at = models.DateTimeField(auto_now_add=True)
    # Yangilangan vaqti
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product} x {self.quantity}"

    # Mahsulot umumiy narxini hisoblash
    def get_total(self):
        return self.price * self.quantity

# Promo kod modeli - chegirmalar uchun
class PromoCode(models.Model):
    # Promo kod
    code = models.CharField(max_length=20, unique=True)
    # Chegirma foizi
    discount_percent = models.PositiveIntegerField()
    # Kod amal qilish boshlanish vaqti
    valid_from = models.DateTimeField()
    # Kod amal qilish tugash vaqti
    valid_to = models.DateTimeField()
    # Kod faol yoki faol emasligi
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

# Savat elementi modeli - foydalanuvchi savatidagi mahsulotlarni saqlash uchun
class CartItem(models.Model):
    # Foydalanuvchi
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    # Mahsulot
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    # Mahsulot soni
    quantity = models.PositiveIntegerField(default=1)
    # Yaratilgan vaqti
    created_at = models.DateTimeField(auto_now_add=True)
    # Yangilangan vaqti
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    # Mahsulot umumiy narxini hisoblash
    def get_total(self):
        return self.quantity * self.product.price
