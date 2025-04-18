from django.urls import path
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from . import views

def redirect_to_dashboard(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

urlpatterns = [
    # Root URL
    path('', redirect_to_dashboard, name='root'),

    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Users
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),

    # Orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),

    # Menu
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
    path('categories/<int:category_id>/update/', views.category_update, name='category_update'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),

    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('products/<int:product_id>/update/', views.product_update, name='product_update'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),

    # Promo Codes
    path('promo-codes/', views.promo_code_list, name='promo_code_list'),
    path('promo-codes/create/', views.promo_code_create, name='promo_code_create'),
    path('promo-codes/<int:promo_id>/', views.promo_code_detail, name='promo_code_detail'),
    path('promo-codes/<int:promo_id>/update/', views.promo_code_update, name='promo_code_update'),
    path('promo-codes/<int:promo_id>/delete/', views.promo_code_delete, name='promo_code_delete'),

    # Reports
    path('reports/', views.reports, name='reports'),
    path('reports/export/', views.export_reports, name='export_reports'),
] 