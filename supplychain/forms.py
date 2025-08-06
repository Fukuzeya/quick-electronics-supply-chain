from django import forms
from django.contrib.auth.models import User
from .models import (
    Supplier, Product, Order, OrderItem, TrackingEvent, 
    Inventory, Category
)

class SupplierRegistrationForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'company_name', 'registration_number', 'contact_person',
            'email', 'phone', 'address', 'country', 'city', 'postal_code'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company name'
            }),
            'registration_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Business registration number'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact person name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Business email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Business address'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postal code'
            }),
        }

class ProductForm(forms.ModelForm):
    specifications = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter product specifications in JSON format or plain text'
        }),
        required=False,
        help_text='Product specifications (optional)'
    )
    
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'sku', 'description', 'specifications',
            'unit_price', 'minimum_order_quantity', 'stock_quantity'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product name'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Stock Keeping Unit (SKU)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Product description'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'minimum_order_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            }),
        }
    
    def clean_specifications(self):
        specs = self.cleaned_data.get('specifications', '')
        if specs:
            try:
                import json
                # Try to parse as JSON
                return json.loads(specs)
            except json.JSONDecodeError:
                # If not valid JSON, store as plain text
                return {'description': specs}
        return {}

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['shipping_address', 'notes']
        widgets = {
            'shipping_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter complete shipping address',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes (optional)'
            }),
        }

class TrackingEventForm(forms.ModelForm):
    class Meta:
        model = TrackingEvent
        fields = ['event_type', 'title', 'description', 'location']
        widgets = {
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Event title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Event description'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Location (optional)'
            }),
        }

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = [
            'current_stock', 'reserved_stock', 'minimum_stock_level',
            'maximum_stock_level', 'reorder_point'
        ]
        widgets = {
            'current_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'reserved_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'minimum_stock_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '10'
            }),
            'maximum_stock_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1000'
            }),
            'reorder_point': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '20'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        current_stock = cleaned_data.get('current_stock', 0)
        reserved_stock = cleaned_data.get('reserved_stock', 0)
        minimum_level = cleaned_data.get('minimum_stock_level', 0)
        maximum_level = cleaned_data.get('maximum_stock_level', 0)
        reorder_point = cleaned_data.get('reorder_point', 0)
        
        if reserved_stock > current_stock:
            raise forms.ValidationError('Reserved stock cannot exceed current stock.')
        
        if minimum_level >= maximum_level:
            raise forms.ValidationError('Minimum stock level must be less than maximum stock level.')
        
        if reorder_point > maximum_level:
            raise forms.ValidationError('Reorder point should not exceed maximum stock level.')
        
        return cleaned_data

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Category description (optional)'
            }),
        }

class OrderSearchForm(forms.Form):
    order_number = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by order number'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Order.ORDER_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

class ProductSearchForm(forms.Form):
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search products...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(status='approved'),
        required=False,
        empty_label='All Suppliers',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    min_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min price',
            'step': '0.01'
        })
    )
    max_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max price',
            'step': '0.01'
        })
    )

class BulkOrderForm(forms.Form):
    """Form for placing orders with multiple products"""
    products = forms.CharField(widget=forms.HiddenInput())
    shipping_address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter complete shipping address',
            'required': True
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Additional notes (optional)'
        })
    )
    
    def clean_products(self):
        products_data = self.cleaned_data.get('products')
        try:
            import json
            products = json.loads(products_data)
            if not isinstance(products, list) or not products:
                raise forms.ValidationError('No products selected.')
            return products
        except (json.JSONDecodeError, TypeError):
            raise forms.ValidationError('Invalid product data.')