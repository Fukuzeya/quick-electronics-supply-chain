from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

class Supplier(models.Model):
    SUPPLIER_STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('suspended', 'Suspended'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, unique=True)
    contact_person = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=SUPPLIER_STATUS_CHOICES, default='pending')
    blockchain_address = models.CharField(max_length=255, blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, 
                               validators=[MinValueValidator(0), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.company_name
    
    class Meta:
        ordering = ['-created_at']

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Product(models.Model):
    PRODUCT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discontinued', 'Discontinued'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    specifications = models.JSONField(default=dict, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_quantity = models.PositiveIntegerField(default=1)
    stock_quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=PRODUCT_STATUS_CHOICES, default='active')
    blockchain_hash = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.supplier.company_name}"
    
    @property
    def is_in_stock(self):
        return self.stock_quantity > 0
    
    class Meta:
        ordering = ['-created_at']

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    shipping_address = models.TextField()
    notes = models.TextField(blank=True)
    blockchain_transaction_hash = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expected_delivery_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            import datetime
            today = datetime.date.today()
            self.order_number = f"ORD-{today.strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

class TrackingEvent(models.Model):
    EVENT_TYPES = [
        ('order_placed', 'Order Placed'),
        ('order_confirmed', 'Order Confirmed'),
        ('in_production', 'In Production'),
        ('quality_check', 'Quality Check'),
        ('packaged', 'Packaged'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('exception', 'Exception/Delay'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    blockchain_hash = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.order.order_number} - {self.title}"
    
    class Meta:
        ordering = ['-timestamp']

class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')
    current_stock = models.PositiveIntegerField(default=0)
    reserved_stock = models.PositiveIntegerField(default=0)
    minimum_stock_level = models.PositiveIntegerField(default=10)
    maximum_stock_level = models.PositiveIntegerField(default=1000)
    reorder_point = models.PositiveIntegerField(default=20)
    last_restocked = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def available_stock(self):
        return self.current_stock - self.reserved_stock
    
    @property
    def needs_reorder(self):
        return self.available_stock <= self.reorder_point
    
    @property
    def stock_status(self):
        if self.available_stock <= 0:
            return 'out_of_stock'
        elif self.needs_reorder:
            return 'low_stock'
        else:
            return 'in_stock'
    
    def __str__(self):
        return f"{self.product.name} - Stock: {self.available_stock}"
    
    class Meta:
        verbose_name_plural = "Inventories"

class SupplierPerformance(models.Model):
    supplier = models.OneToOneField(Supplier, on_delete=models.CASCADE, related_name='performance')
    total_orders = models.PositiveIntegerField(default=0)
    completed_orders = models.PositiveIntegerField(default=0)
    cancelled_orders = models.PositiveIntegerField(default=0)
    average_delivery_time = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # in days
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # percentage
    quality_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)
    
    @property
    def completion_rate(self):
        if self.total_orders > 0:
            return (self.completed_orders / self.total_orders) * 100
        return 0
    
    def __str__(self):
        return f"{self.supplier.company_name} - Performance"
