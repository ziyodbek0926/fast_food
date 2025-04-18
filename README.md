# Fast Food Telegram Bot

Bu loyiha Telegram orqali fast food buyurtma qilish uchun bot va uning admin panelini o'z ichiga oladi.

## Texnologiyalar

- Python 3.10+
- Django 5.0
- PostgreSQL
- Aiogram 3.x
- Bootstrap 5
- Font Awesome

## O'rnatish

1. Loyihani klonlang:
```bash
git clone https://github.com/yourusername/fast_food.git
cd fast_food
```

2. Virtual muhit yarating va faollashtiring:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Kerakli paketlarni o'rnating:
```bash
pip install -r requirements.txt
```

4. `.env` faylini yarating va quyidagi o'zgaruvchilarni to'ldiring:
```env
DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=postgres://user:password@localhost:5432/fast_food
TELEGRAM_BOT_TOKEN=your_bot_token
```

5. Ma'lumotlar bazasini yarating va migratsiyalarni qo'llang:
```bash
python manage.py migrate
```

6. Superuser yarating:
```bash
python manage.py createsuperuser
```

7. Botni ishga tushiring:
```bash
python manage.py runbot
```

8. Django serverini ishga tushiring:
```bash
python manage.py runserver
```

## Loyiha tuzilishi

```
fast_food/
├── core/                    # Asosiy Django ilovasi
│   ├── migrations/          # Ma'lumotlar bazasi migratsiyalari
│   ├── templates/           # HTML shablonlar
│   │   ├── categories/      # Kategoriyalar shablonlari
│   │   ├── orders/          # Buyurtmalar shablonlari
│   │   ├── products/        # Mahsulotlar shablonlari
│   │   ├── promo_codes/     # Promo kodlar shablonlari
│   │   └── reports/         # Hisobotlar shablonlari
│   ├── management/          # Bot boshqaruv buyruqlari
│   │   └── commands/        # Django buyruqlari
│   ├── models.py            # Ma'lumotlar bazasi modellari
│   ├── views.py             # Django view funksiyalari
│   └── urls.py              # URL konfiguratsiyasi
├── media/                   # Media fayllar
├── static/                  # Statik fayllar
├── templates/               # Asosiy HTML shablonlar
├── .env                     # Muhit o'zgaruvchilari
├── .gitignore               # Git ignore fayli
├── manage.py                # Django boshqaruv skripti
├── requirements.txt         # Loyihda ishlatilgan kutubxonalar
└── README.md                # Loyiha hujjati
```

## Admin panel

Admin paneliga kirish uchun:
- URL: `http://localhost:8000/admin/`
- Foydalanuvchi nomi: superuser nomi
- Parol: superuser paroli

## Bot funksiyalari

- Til tanlash (O'zbek/Rus)
- Kategoriyalar va mahsulotlar ro'yxati
- Savatga qo'shish
- Buyurtma berish
- Promo kodlar
- Buyurtma holatini kuzatish

## Admin panel funksiyalari

- Foydalanuvchilar boshqaruvi
- Buyurtmalar boshqaruvi
- Kategoriyalar boshqaruvi
- Mahsulotlar boshqaruvi
- Promo kodlar boshqaruvi
- Hisobotlar

## Muallif

- Ism: Ziyodbek
- Email: abdusattorovziyodbek07@gmail.com
- GitHub: [ziyodbek0926]

## Litsenziya

Bu loyiha MIT litsenziyasi ostida tarqatilgan. Batafsil ma'lumot uchun `LICENSE` faylini ko'ring. 