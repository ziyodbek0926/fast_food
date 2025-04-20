from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, Sum, F
from django.utils import timezone
from datetime import timedelta
import pandas as pd
from reportlab.pdfgen import canvas
from io import BytesIO

from .models import TelegramUser, Order, Product, Category, PromoCode

# Bosh sahifa - admin panel asosiy ko'rinishi
@login_required
def dashboard(request):
    # Statistika ma'lumotlarini olish
    total_users = TelegramUser.objects.count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(total=Sum('total_price'))['total'] or 0
    
    # So'nggi buyurtmalarni olish
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
    
    # Mashhur mahsulotlarni olish
    popular_products = Product.objects.annotate(
        order_count=Count('orderitem')
    ).order_by('-order_count')[:5]

    context = {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'popular_products': popular_products,
    }
    return render(request, 'dashboard.html', context)

# Foydalanuvchilar ro'yxati - barcha foydalanuvchilarni ko'rsatish
@login_required
def user_list(request):
    users = TelegramUser.objects.all()
    return render(request, 'users/list.html', {'users': users})

# Foydalanuvchi tafsilotlari - bitta foydalanuvchi haqida batafsil ma'lumot
@login_required
def user_detail(request, user_id):
    user = get_object_or_404(TelegramUser, id=user_id)
    orders = Order.objects.filter(user=user)
    return render(request, 'users/detail.html', {'user': user, 'orders': orders})

# Buyurtmalar ro'yxati - barcha buyurtmalarni ko'rsatish
@login_required
def order_list(request):
    orders = Order.objects.select_related('user').all()
    return render(request, 'orders/list.html', {'orders': orders})

# Buyurtma tafsilotlari - bitta buyurtma haqida batafsil ma'lumot
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/detail.html', {'order': order})

# Buyurtma holatini yangilash - buyurtma holatini o'zgartirish
@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()
        messages.success(request, 'Buyurtma holati muvaffaqiyatli yangilandi')
        return redirect('order_detail', order_id=order_id)
    return render(request, 'orders/update_status.html', {'order': order})

# Kategoriyalar ro'yxati - barcha kategoriyalarni ko'rsatish
@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'categories/list.html', {'categories': categories})

# Kategoriya yaratish - yangi kategoriya qo'shish
@login_required
def category_create(request):
    if request.method == 'POST':
        name_uz = request.POST.get('name_uz')
        name_ru = request.POST.get('name_ru')
        description_uz = request.POST.get('description_uz')
        description_ru = request.POST.get('description_ru')
        is_active = request.POST.get('is_active') == 'on'
        
        category = Category.objects.create(
            name_uz=name_uz,
            name_ru=name_ru,
            description_uz=description_uz,
            description_ru=description_ru,
            is_active=is_active
        )
        
        if 'image' in request.FILES:
            category.image = request.FILES['image']
            category.save()
            
        messages.success(request, 'Kategoriya muvaffaqiyatli yaratildi')
        return redirect('category_list')
        
    return render(request, 'categories/create.html')

# Kategoriyani yangilash - mavjud kategoriyani o'zgartirish
@login_required
def category_update(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category.name_uz = request.POST.get('name_uz')
        category.name_ru = request.POST.get('name_ru')
        category.description_uz = request.POST.get('description_uz')
        category.description_ru = request.POST.get('description_ru')
        category.is_active = request.POST.get('is_active') == 'on'
        
        if 'image' in request.FILES:
            category.image = request.FILES['image']
            
        category.save()
        messages.success(request, 'Kategoriya muvaffaqiyatli yangilandi')
        return redirect('category_detail', category_id=category.id)
    
    return render(request, 'categories/update.html', {'category': category})

# Kategoriyani o'chirish - kategoriyani o'chirish
@login_required
def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Kategoriya muvaffaqiyatli o\'chirildi')
        return redirect('category_list')
    return render(request, 'categories/delete.html', {'category': category})

# Kategoriya tafsilotlari - bitta kategoriya haqida batafsil ma'lumot
@login_required
def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    
    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'categories/detail.html', context)

# Mahsulotlar ro'yxati - barcha mahsulotlarni ko'rsatish
@login_required
def product_list(request):
    products = Product.objects.select_related('category').all()
    return render(request, 'products/list.html', {'products': products})

# Mahsulot yaratish - yangi mahsulot qo'shish
@login_required
def product_create(request):
    categories = Category.objects.all()
    
    if request.method == 'POST':
        name_uz = request.POST.get('name_uz')
        name_ru = request.POST.get('name_ru')
        description_uz = request.POST.get('description_uz')
        description_ru = request.POST.get('description_ru')
        price = request.POST.get('price')
        category_id = request.POST.get('category')
        is_available = request.POST.get('is_available') == 'on'
        
        product = Product.objects.create(
            name_uz=name_uz,
            name_ru=name_ru,
            description_uz=description_uz,
            description_ru=description_ru,
            price=price,
            category_id=category_id,
            is_available=is_available
        )
        
        if 'image' in request.FILES:
            product.image = request.FILES['image']
            product.save()
            
        messages.success(request, 'Mahsulot muvaffaqiyatli yaratildi')
        return redirect('product_list')
        
    context = {
        'categories': categories,
    }
    return render(request, 'products/create.html', context)

# Mahsulotni yangilash - mavjud mahsulotni o'zgartirish
@login_required
def product_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    
    if request.method == 'POST':
        product.name_uz = request.POST.get('name_uz')
        product.name_ru = request.POST.get('name_ru')
        product.description_uz = request.POST.get('description_uz')
        product.description_ru = request.POST.get('description_ru')
        product.price = request.POST.get('price')
        product.category_id = request.POST.get('category')
        product.is_available = request.POST.get('is_available') == 'on'
        
        if 'image' in request.FILES:
            product.image = request.FILES['image']
            
        product.save()
        messages.success(request, 'Mahsulot muvaffaqiyatli yangilandi')
        return redirect('product_detail', product_id=product.id)
        
    context = {
        'product': product,
        'categories': categories,
    }
    return render(request, 'products/update.html', context)

# Mahsulotni o'chirish - mahsulotni o'chirish
@login_required
def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Mahsulot muvaffaqiyatli o\'chirildi')
        return redirect('product_list')
    return render(request, 'products/delete.html', {'product': product})

# Mahsulot tafsilotlari - bitta mahsulot haqida batafsil ma'lumot
@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    orders = Order.objects.filter(items__product=product).distinct()
    
    # Har bir buyurtma uchun mahsulot elementlarini olish
    order_items = {}
    for order in orders:
        items = order.items.filter(product=product)
        order_items[order.id] = items
    
    context = {
        'product': product,
        'orders': orders,
        'order_items': order_items,
    }
    return render(request, 'products/detail.html', context)

# Promo kodlar ro'yxati - barcha promo kodlarni ko'rsatish
@login_required
def promo_code_list(request):
    promo_codes = PromoCode.objects.all()
    return render(request, 'promo_codes/list.html', {'promo_codes': promo_codes})

# Promo kod yaratish - yangi promo kod qo'shish
@login_required
def promo_code_create(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        discount_percent = request.POST.get('discount_percent')
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')
        is_active = request.POST.get('is_active') == 'on'
        
        promo_code = PromoCode.objects.create(
            code=code,
            discount_percent=discount_percent,
            valid_from=valid_from,
            valid_to=valid_to,
            is_active=is_active
        )
        
        messages.success(request, 'Promo kod muvaffaqiyatli yaratildi')
        return redirect('promo_code_list')
        
    return render(request, 'promo_codes/create.html')

# Promo kodni yangilash - mavjud promo kodni o'zgartirish
@login_required
def promo_code_update(request, promo_id):
    promo_code = get_object_or_404(PromoCode, id=promo_id)
    if request.method == 'POST':
        promo_code.code = request.POST.get('code')
        promo_code.discount_percent = request.POST.get('discount_percent')
        promo_code.valid_from = request.POST.get('valid_from')
        promo_code.valid_to = request.POST.get('valid_to')
        promo_code.is_active = request.POST.get('is_active') == 'on'
        promo_code.save()
        messages.success(request, 'Promo kod muvaffaqiyatli yangilandi')
        return redirect('promo_code_detail', promo_id=promo_code.id)
    return render(request, 'promo_codes/update.html', {'promo_code': promo_code})

# Promo kodni o'chirish - promo kodni o'chirish
@login_required
def promo_code_delete(request, promo_id):
    promo_code = get_object_or_404(PromoCode, id=promo_id)
    if request.method == 'POST':
        promo_code.delete()
        messages.success(request, 'Promo kod muvaffaqiyatli o\'chirildi')
        return redirect('promo_code_list')
    return render(request, 'promo_codes/delete.html', {'promo_code': promo_code})

# Promo kod tafsilotlari - bitta promo kod haqida batafsil ma'lumot
@login_required
def promo_code_detail(request, promo_id):
    promo_code = get_object_or_404(PromoCode, id=promo_id)
    return render(request, 'promo_codes/detail.html', {
        'promo_code': promo_code
    })

# Hisobotlar - statistika va tahlil ma'lumotlarini ko'rsatish
@login_required
def reports(request):
    # Sana parametrlarini olish
    date = request.GET.get('date')
    month = request.GET.get('month')
    
    # Kontekstni ishga tushirish
    context = {
        'date': date,
        'month': month,
    }
    
    # Kunlik statistika
    if date:
        try:
            date_obj = timezone.datetime.strptime(date, '%Y-%m-%d').date()
            daily_orders = Order.objects.filter(created_at__date=date_obj)
            
            daily_stats = {
                'orders_count': daily_orders.count(),
                'total_amount': daily_orders.aggregate(total=Sum('total_price'))['total'] or 0,
            }
            if daily_stats['orders_count'] > 0:
                daily_stats['average_order'] = daily_stats['total_amount'] / daily_stats['orders_count']
            else:
                daily_stats['average_order'] = 0
                
            context['daily_stats'] = daily_stats
        except ValueError:
            pass
    
    # Oylik statistika
    if month:
        try:
            year, month = map(int, month.split('-'))
            monthly_orders = Order.objects.filter(
                created_at__year=year,
                created_at__month=month
            )
            
            monthly_stats = {
                'orders_count': monthly_orders.count(),
                'total_amount': monthly_orders.aggregate(total=Sum('total_price'))['total'] or 0,
            }
            if monthly_stats['orders_count'] > 0:
                monthly_stats['average_order'] = monthly_stats['total_amount'] / monthly_stats['orders_count']
            else:
                monthly_stats['average_order'] = 0
                
            context['monthly_stats'] = monthly_stats
        except ValueError:
            pass
    
    # Mashhur mahsulotlar
    popular_products = Product.objects.annotate(
        orders_count=Count('orderitem'),
        total_amount=Sum(F('orderitem__price') * F('orderitem__quantity'))
    ).order_by('-orders_count')[:10]
    
    context['popular_products'] = popular_products
    
    return render(request, 'reports/index.html', context)

# Hisobotlarni yuklab olish - Excel formatida hisobotlarni yuklab olish
@login_required
def export_reports(request):
    # Sana oralig'ini olish
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Buyurtma ma'lumotlarini olish
    orders = Order.objects.filter(created_at__range=(start_date, end_date))
    
    # DataFrame yaratish
    data = []
    for order in orders:
        data.append({
            'Order ID': order.id,
            'User': order.user.username,
            'Total Price': order.total_price,
            'Status': order.status,
            'Created At': order.created_at,
        })
    
    df = pd.DataFrame(data)
    
    # Excel faylini yaratish
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Orders', index=False)
    
    # Javobni yaratish
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=orders_report.xlsx'
    return response
