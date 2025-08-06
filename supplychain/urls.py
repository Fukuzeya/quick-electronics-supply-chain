from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'supply_chain'

urlpatterns = [
    # Home and Dashboard
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.supplier_register, name='register'),
    
    # Supplier URLs
    path('supplier/register/', views.supplier_register, name='supplier_register'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    
    # Product URLs
    path('products/', views.product_list, name='product_list'),
    path('products/<uuid:product_id>/', views.product_detail, name='product_detail'),
    path('products/add/', views.add_product, name='add_product'),
    
    # Order URLs
    path('orders/', views.order_list, name='order_list'),
    path('orders/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('orders/place/<uuid:product_id>/', views.place_order, name='place_order'),
    path('orders/<uuid:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    
    # Inventory URLs
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/<uuid:product_id>/update/', views.update_inventory, name='update_inventory'),
    
    # API URLs for real-time updates
    path('api/orders/<uuid:order_id>/tracking/', views.api_order_tracking, name='api_order_tracking'),
    path('api/inventory/status/', views.api_inventory_status, name='api_inventory_status'),
]
