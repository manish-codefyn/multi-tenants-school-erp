from django import forms
from apps.core.forms import TenantAwareModelForm
from .models import Category, Supplier, Item, StockMovement, PurchaseOrder

class CategoryForm(TenantAwareModelForm):
    class Meta:
        model = Category
        fields = ['name', 'code', 'description', 'parent_category', 'is_consumable', 
                  'requires_serial_number', 'requires_maintenance', 'low_stock_threshold', 
                  'reorder_quantity', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class SupplierForm(TenantAwareModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'code', 'supplier_type', 'contact_person', 'email', 'phone', 
                  'mobile', 'address', 'city', 'state', 'pincode', 'gst_number', 
                  'pan_number', 'website', 'bank_name', 'account_number', 'ifsc_code', 
                  'is_active', 'notes']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class ItemForm(TenantAwareModelForm):
    class Meta:
        model = Item
        fields = ['name', 'code', 'barcode', 'description', 'category', 'brand', 'model', 
                  'size', 'color', 'unit', 'current_stock', 'minimum_stock', 
                  'low_stock_threshold', 'reorder_quantity', 'cost_price', 'selling_price', 
                  'storage_location', 'shelf_number', 'is_consumable', 'is_serialized', 
                  'is_active', 'is_discountable', 'hsn_code', 'tax_rate', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class StockMovementForm(TenantAwareModelForm):
    class Meta:
        model = StockMovement
        fields = ['item', 'movement_type', 'quantity', 'unit_price', 'reference', 
                  'from_location', 'to_location', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class PurchaseOrderForm(TenantAwareModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'order_date', 'expected_delivery_date', 'payment_terms', 
                  'delivery_terms', 'notes', 'status']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_terms': forms.Textarea(attrs={'rows': 3}),
            'delivery_terms': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
