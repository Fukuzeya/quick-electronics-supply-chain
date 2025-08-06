from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Supplier, Product, Order, OrderItem, TrackingEvent,
    Inventory, Category, SupplierPerformance
)

# Customize admin site headers
admin.site.site_header = "Quick Electronics Supply Chain Administration"
admin.site.site_title = "Quick Electronics Admin"
admin.site.index_title = "Welcome to Quick Electronics Administration"

class SupplierInline(admin.StackedInline):
    model = Supplier
    can_delete = False
    verbose_name_plural = 'Supplier Information'
    fields = (
        'company_name', 'registration_number', 'contact_person',
        'email', 'phone', 'status', 'rating'
    )
    readonly_fields = ('rating',)

class CustomUserAdmin(BaseUserAdmin):
    inlines = (SupplierInline,)
    
    def get_inlines(self, request, obj):
        if obj and hasattr(obj, 'supplier'):
            return self.inlines
        return []

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        'company_name', 'contact_person', 'email', 'city', 'country',
        'status', 'rating_display', 'products_count', 'created_at'
    )
    list_filter = ('status', 'country', 'city', 'created_at', 'rating')
    search_fields = (
        'company_name', 'contact_person', 'email', 'registration_number'
    )
    readonly_fields = ('id', 'created_at', 'updated_at', 'blockchain_address')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'company_name', 'registration_number', 'contact_person')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address', 'city', 'country', 'postal_code')
        }),
        ('Business Information', {
            'fields': ('status', 'rating', 'blockchain_address')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['approve_suppliers', 'suspend_suppliers']
    
    def rating_display(self, obj):
        stars = '★' * int(obj.rating) + '☆' * (5 - int(obj.rating))
        return format_html(
            '<span style="color: #ffc107;">{}</span> ({:.1f})',
            stars, obj.rating
        )
    rating_display.short_description = 'Rating'
    
    def products_count(self, obj):
        count = obj.products.count()
        url = reverse('admin:supply_chain_product_changelist') + f'?supplier__id__exact={obj.id}'
        return format_html('<a href="{}">{} products</a>', url, count)
    products_count.short_description = 'Products'
    
    def approve_suppliers(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} suppliers approved successfully.')
    approve_suppliers.short_description = 'Approve selected suppliers'
    
    def suspend_suppliers(self, request, queryset):
        updated = queryset.update(status='suspended')
        self.message_user(request, f'{updated} suppliers suspended.')
    suspend_suppliers.short_description = 'Suspend selected suppliers'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'products_count', 'created_at')
    search_fields = ('name', 'description')
    
    def products_count(self, obj):
        count = obj.product_set.count()
        url = reverse('admin:supply_chain_product_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{} products</a>', url, count)
    products_count.short_description = 'Products'

class InventoryInline(admin.StackedInline):
    model = Inventory
    fields = (
        'current_stock', 'reserved_stock', 'minimum_stock_level',
        'maximum_stock_level', 'reorder_point', 'last_restocked'
    )
    readonly_fields = ('last_restocked',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'sku', 'supplier', 'category', 'unit_price',
        'stock_status', 'status', 'created_at'
    )
    list_filter = ('status', 'category', 'supplier', 'created_at')
    search_fields = ('name', 'sku', 'description', 'supplier__company_name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'blockchain_hash')
    inlines = [InventoryInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('supplier', 'category', 'name', 'sku', 'description')
        }),
        ('Specifications & Pricing', {
            'fields': ('specifications', 'unit_price', 'minimum_order_quantity', 'stock_quantity')
        }),
        ('Status & Blockchain', {
            'fields': ('status', 'blockchain_hash')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def stock_status(self, obj):
        try:
            inventory = obj.inventory
            if inventory.available_stock <= 0:
                color = 'red'
                status = 'Out of Stock'
            elif inventory.needs_reorder:
                color = 'orange'
                status = 'Low Stock'
            else:
                color = 'green'
                status = 'In Stock'
            return format_html(
                '<span style="color: {};">{} ({})</span>',
                color, status, inventory.available_stock
            )
        except:
            return format_html('<span style="color: gray;">No inventory data</span>')
    stock_status.short_description = 'Stock Status'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ('product', 'quantity', 'unit_price', 'total_price')
    readonly_fields = ('total_price',)
    extra = 0

class TrackingEventInline(admin.TabularInline):
    model = TrackingEvent
    fields = ('event_type', 'title', 'description', 'location', 'timestamp')
    readonly_fields = ('timestamp',)
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'customer', 'supplier', 'status',
        'payment_status', 'total_amount', 'created_at'
    )
    list_filter = ('status', 'payment_status', 'created_at', 'supplier')
    search_fields = ('order_number', 'customer__username', 'supplier__company_name')
    readonly_fields = ('id', 'order_number', 'created_at', 'updated_at', 'blockchain_transaction_hash')
    inlines = [OrderItemInline, TrackingEventInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer', 'supplier', 'status', 'payment_status')
        }),
        ('Financial Information', {
            'fields': ('total_amount',)
        }),
        ('Delivery Information', {
            'fields': ('shipping_address', 'expected_delivery_date', 'notes')
        }),
        ('Blockchain & System', {
            'fields': ('blockchain_transaction_hash', 'id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_as_confirmed', 'mark_as_shipped']
    
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} orders marked as confirmed.')
    mark_as_confirmed.short_description = 'Mark selected orders as confirmed'
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'{updated} orders marked as shipped.')
    mark_as_shipped.short_description = 'Mark selected orders as shipped'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_price', 'total_price')
    list_filter = ('order__status', 'product__category')
    search_fields = ('order__order_number', 'product__name', 'product__sku')
    readonly_fields = ('total_price',)

@admin.register(TrackingEvent)
class TrackingEventAdmin(admin.ModelAdmin):
    list_display = (
        'order', 'event_type', 'title', 'location', 'timestamp', 'created_by'
    )
    list_filter = ('event_type', 'timestamp', 'order__status')
    search_fields = ('order__order_number', 'title', 'description', 'location')
    readonly_fields = ('id', 'timestamp', 'blockchain_hash')
    fieldsets = (
        ('Event Information', {
            'fields': ('order', 'event_type', 'title', 'description', 'location', 'created_by')
        }),
        ('System Information', {
            'fields': ('id', 'timestamp', 'blockchain_hash'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'current_stock', 'reserved_stock', 'available_stock',
        'stock_status_display', 'reorder_needed', 'last_restocked'
    )
    list_filter = ('last_restocked', 'product__supplier', 'product__category')
    search_fields = ('product__name', 'product__sku', 'product__supplier__company_name')
    readonly_fields = ('updated_at',)
    
    def stock_status_display(self, obj):
        status = obj.stock_status
        colors = {
            'in_stock': 'green',
            'low_stock': 'orange',
            'out_of_stock': 'red'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(status, 'gray'),
            status.replace('_', ' ').title()
        )
    stock_status_display.short_description = 'Stock Status'
    
    def reorder_needed(self, obj):
        if obj.needs_reorder:
            return format_html('<span style="color: red;">⚠️ YES</span>')
        return format_html('<span style="color: green;">✅ NO</span>')
    reorder_needed.short_description = 'Reorder Needed'

@admin.register(SupplierPerformance)
class SupplierPerformanceAdmin(admin.ModelAdmin):
    list_display = (
        'supplier', 'total_orders', 'completion_rate_display',
        'on_time_delivery_rate', 'quality_rating', 'last_updated'
    )
    list_filter = ('last_updated', 'quality_rating')
    search_fields = ('supplier__company_name',)
    readonly_fields = ('last_updated',)
    
    def completion_rate_display(self, obj):
        rate = obj.completion_rate
        color = 'green' if rate >= 90 else 'orange' if rate >= 70 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, rate
        )
    completion_rate_display.short_description = 'Completion Rate'

# Custom admin views for dashboard-like functionality
class AdminDashboard:
    """Custom admin dashboard with key metrics"""
    
    def __init__(self):
        self.changelist_view = self.changelist_view
    
    def changelist_view(self, request):
        # This would be implemented to show dashboard metrics
        pass

# Register custom admin actions
def export_as_csv(modeladmin, request, queryset):
    """Export selected objects as CSV"""
    import csv
    from django.http import HttpResponse
    
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={meta}.csv'
    writer = csv.writer(response)
    
    writer.writerow(field_names)
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])
    
    return response

export_as_csv.short_description = "Export selected items as CSV"

# Add the export action to all admin classes
admin.site.add_action(export_as_csv)
