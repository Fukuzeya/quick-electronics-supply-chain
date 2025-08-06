from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal

from .models import (
    Supplier, Product, Order, OrderItem, TrackingEvent, 
    Inventory, Category, SupplierPerformance
)
from .forms import (
    SupplierRegistrationForm, ProductForm, OrderForm, 
    TrackingEventForm, InventoryForm
)

def home(request):
    """Home page with overview statistics"""
    context = {
        'total_suppliers': Supplier.objects.filter(status='approved').count(),
        'total_products': Product.objects.filter(status='active').count(),
        'total_orders_today': Order.objects.filter(created_at__date=timezone.now().date()).count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
    }
    return render(request, 'supply_chain/home.html', context)

@login_required
def dashboard(request):
    """Main dashboard based on user role"""
    try:
        supplier = request.user.supplier
        return supplier_dashboard(request)
    except:
        return customer_dashboard(request)

@login_required
def customer_dashboard(request):
    """Customer dashboard with order history and product browsing"""
    recent_orders = Order.objects.filter(customer=request.user)[:5]
    active_orders = Order.objects.filter(
        customer=request.user, 
        status__in=['pending', 'confirmed', 'processing', 'shipped']
    )
    
    context = {
        'recent_orders': recent_orders,
        'active_orders': active_orders,
        'total_orders': Order.objects.filter(customer=request.user).count(),
        'user_type': 'customer'
    }
    return render(request, 'supply_chain/dashboard.html', context)

@login_required
def supplier_dashboard(request):
    """Supplier dashboard with performance metrics"""
    try:
        supplier = request.user.supplier
    except:
        messages.error(request, 'You are not registered as a supplier.')
        return redirect('supplier_register')
    
    # Get supplier statistics
    total_products = supplier.products.count()
    active_products = supplier.products.filter(status='active').count()
    total_orders = Order.objects.filter(supplier=supplier).count()
    pending_orders = Order.objects.filter(supplier=supplier, status='pending').count()
    
    # Recent orders
    recent_orders = Order.objects.filter(supplier=supplier)[:5]
    
    # Low stock products
    low_stock_products = []
    for product in supplier.products.filter(status='active'):
        try:
            if product.inventory.needs_reorder:
                low_stock_products.append(product)
        except:
            pass
    
    context = {
        'supplier': supplier,
        'total_products': total_products,
        'active_products': active_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products[:5],
        'user_type': 'supplier'
    }
    return render(request, 'supply_chain/dashboard.html', context)

# Supplier Registration Views
def supplier_register(request):
    """Supplier registration form"""
    if request.method == 'POST':
        user_form = UserCreationForm(request.POST)
        supplier_form = SupplierRegistrationForm(request.POST)
        
        if user_form.is_valid() and supplier_form.is_valid():
            user = user_form.save()
            supplier = supplier_form.save(commit=False)
            supplier.user = user
            supplier.save()
            
            messages.success(request, 'Supplier registration submitted successfully! Please wait for approval.')
            return redirect('login')
    else:
        user_form = UserCreationForm()
        supplier_form = SupplierRegistrationForm()
    
    return render(request, 'supply_chain/supplier_register.html', {
        'user_form': user_form,
        'supplier_form': supplier_form
    })

@login_required
def supplier_list(request):
    """List all approved suppliers"""
    suppliers = Supplier.objects.filter(status='approved')
    search_query = request.GET.get('search', '')
    
    if search_query:
        suppliers = suppliers.filter(
            Q(company_name__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(city__icontains=search_query)
        )
    
    paginator = Paginator(suppliers, 12)
    page_number = request.GET.get('page')
    suppliers_page = paginator.get_page(page_number)
    
    return render(request, 'supply_chain/supplier_list.html', {
        'suppliers': suppliers_page,
        'search_query': search_query
    })

# Product Views
@login_required
def product_list(request):
    """List all active products"""
    products = Product.objects.filter(status='active').select_related('supplier', 'category')
    
    # Filters
    category_id = request.GET.get('category')
    supplier_id = request.GET.get('supplier')
    search_query = request.GET.get('search', '')
    
    if category_id:
        products = products.filter(category_id=category_id)
    if supplier_id:
        products = products.filter(supplier_id=supplier_id)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    
    # Get filter options
    categories = Category.objects.all()
    suppliers = Supplier.objects.filter(status='approved')
    
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)
    
    return render(request, 'supply_chain/product_list.html', {
        'products': products_page,
        'categories': categories,
        'suppliers': suppliers,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_supplier': supplier_id
    })

@login_required
def product_detail(request, product_id):
    """Product detail view"""
    product = get_object_or_404(Product, id=product_id, status='active')
    return render(request, 'supply_chain/product_detail.html', {'product': product})

@login_required
def add_product(request):
    """Add new product (suppliers only)"""
    try:
        supplier = request.user.supplier
        if supplier.status != 'approved':
            messages.error(request, 'Your supplier account is not approved yet.')
            return redirect('dashboard')
    except:
        messages.error(request, 'You must be a registered supplier to add products.')
        return redirect('supplier_register')
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.supplier = supplier
            product.save()
            
            # Create inventory record
            Inventory.objects.create(
                product=product,
                current_stock=product.stock_quantity
            )
            
            messages.success(request, 'Product added successfully!')
            return redirect('dashboard')
    else:
        form = ProductForm()
    
    return render(request, 'supply_chain/add_product.html', {'form': form})

# Order Views
@login_required
def place_order(request, product_id):
    """Place an order for a product"""
    product = get_object_or_404(Product, id=product_id, status='active')
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity < product.minimum_order_quantity:
            messages.error(request, f'Minimum order quantity is {product.minimum_order_quantity}')
            return redirect('product_detail', product_id=product_id)
        
        if quantity > product.stock_quantity:
            messages.error(request, 'Not enough stock available')
            return redirect('product_detail', product_id=product_id)
        
        # Create order
        order = Order.objects.create(
            customer=request.user,
            supplier=product.supplier,
            shipping_address=request.POST.get('shipping_address', ''),
            notes=request.POST.get('notes', '')
        )
        
        # Create order item
        unit_price = product.unit_price
        total_price = unit_price * quantity
        
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price
        )
        
        # Update order total
        order.total_amount = total_price
        order.save()
        
        # Update inventory
        try:
            inventory = product.inventory
            inventory.reserved_stock += quantity
            inventory.save()
        except:
            pass
        
        # Create initial tracking event
        TrackingEvent.objects.create(
            order=order,
            event_type='order_placed',
            title='Order Placed',
            description=f'Order placed for {quantity} units of {product.name}',
            created_by=request.user
        )
        
        messages.success(request, f'Order #{order.order_number} placed successfully!')
        return redirect('order_detail', order_id=order.id)
    
    return render(request, 'supply_chain/place_order.html', {'product': product})

@login_required
def order_list(request):
    """List user's orders"""
    if hasattr(request.user, 'supplier'):
        # Supplier view - show orders for their products
        orders = Order.objects.filter(supplier=request.user.supplier)
    else:
        # Customer view - show their orders
        orders = Order.objects.filter(customer=request.user)
    
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    orders = orders.order_by('-created_at')
    
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    
    return render(request, 'supply_chain/order_list.html', {
        'orders': orders_page,
        'status_filter': status_filter,
        'order_statuses': Order.ORDER_STATUS_CHOICES
    })

@login_required
def order_detail(request, order_id):
    """Order detail with tracking information"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check permissions
    if not (order.customer == request.user or 
            (hasattr(request.user, 'supplier') and order.supplier == request.user.supplier)):
        messages.error(request, 'You do not have permission to view this order.')
        return redirect('order_list')
    
    tracking_events = order.tracking_events.all()
    
    return render(request, 'supply_chain/order_detail.html', {
        'order': order,
        'tracking_events': tracking_events
    })

@login_required
def update_order_status(request, order_id):
    """Update order status and add tracking event (suppliers only)"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user is the supplier for this order
    if not (hasattr(request.user, 'supplier') and order.supplier == request.user.supplier):
        messages.error(request, 'You do not have permission to update this order.')
        return redirect('order_detail', order_id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        event_type = request.POST.get('event_type')
        title = request.POST.get('title')
        description = request.POST.get('description')
        location = request.POST.get('location', '')
        
        # Update order status
        order.status = new_status
        order.save()
        
        # Create tracking event
        TrackingEvent.objects.create(
            order=order,
            event_type=event_type,
            title=title,
            description=description,
            location=location,
            created_by=request.user
        )
        
        messages.success(request, 'Order status updated successfully!')
        return redirect('order_detail', order_id=order_id)
    
    return render(request, 'supply_chain/update_order_status.html', {
        'order': order,
        'order_statuses': Order.ORDER_STATUS_CHOICES,
        'event_types': TrackingEvent.EVENT_TYPES
    })

# Inventory Management Views
@login_required
def inventory_list(request):
    """Inventory management (suppliers only)"""
    try:
        supplier = request.user.supplier
    except:
        messages.error(request, 'You must be a supplier to access inventory.')
        return redirect('dashboard')
    
    products = supplier.products.filter(status='active').prefetch_related('inventory')
    
    # Filter options
    stock_filter = request.GET.get('stock_status')
    if stock_filter == 'low':
        products = [p for p in products if hasattr(p, 'inventory') and p.inventory.needs_reorder]
    elif stock_filter == 'out':
        products = [p for p in products if hasattr(p, 'inventory') and p.inventory.available_stock <= 0]
    
    return render(request, 'supply_chain/inventory_list.html', {
        'products': products,
        'stock_filter': stock_filter
    })

@login_required
def update_inventory(request, product_id):
    """Update product inventory"""
    product = get_object_or_404(Product, id=product_id)
    
    # Check permissions
    if not (hasattr(request.user, 'supplier') and product.supplier == request.user.supplier):
        messages.error(request, 'You do not have permission to update this inventory.')
        return redirect('inventory_list')
    
    inventory, created = Inventory.objects.get_or_create(
        product=product,
        defaults={'current_stock': product.stock_quantity}
    )
    
    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=inventory)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventory updated successfully!')
            return redirect('inventory_list')
    else:
        form = InventoryForm(instance=inventory)
    
    return render(request, 'supply_chain/update_inventory.html', {
        'form': form,
        'product': product,
        'inventory': inventory
    })

# API Views for Real-time Updates
@csrf_exempt
def api_order_tracking(request, order_id):
    """API endpoint for real-time order tracking"""
    if request.method == 'GET':
        order = get_object_or_404(Order, id=order_id)
        tracking_events = order.tracking_events.all()
        
        events_data = []
        for event in tracking_events:
            events_data.append({
                'event_type': event.event_type,
                'title': event.title,
                'description': event.description,
                'location': event.location,
                'timestamp': event.timestamp.isoformat(),
            })
        
        return JsonResponse({
            'order_number': order.order_number,
            'status': order.status,
            'tracking_events': events_data
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def api_inventory_status(request):
    """API endpoint for real-time inventory status"""
    if request.method == 'GET':
        try:
            supplier = request.user.supplier
            products = supplier.products.filter(status='active').prefetch_related('inventory')
            
            inventory_data = []
            for product in products:
                try:
                    inventory = product.inventory
                    inventory_data.append({
                        'product_id': str(product.id),
                        'product_name': product.name,
                        'sku': product.sku,
                        'current_stock': inventory.current_stock,
                        'available_stock': inventory.available_stock,
                        'reserved_stock': inventory.reserved_stock,
                        'stock_status': inventory.stock_status,
                        'needs_reorder': inventory.needs_reorder,
                        'reorder_point': inventory.reorder_point
                    })
                except:
                    pass
            
            return JsonResponse({'inventory': inventory_data})
        except:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
