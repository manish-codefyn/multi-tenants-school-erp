from django.contrib import admin
from .models import (
    Category, Supplier, Item, StockMovement,
    PurchaseOrder, PurchaseOrderItem
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'parent_category', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'supplier_type', 'contact_person', 'email', 'phone', 'is_active')
    list_filter = ('supplier_type', 'is_active')
    search_fields = ('name', 'code', 'contact_person')

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'current_stock', 'unit', 'cost_price', 'selling_price', 'is_active')
    list_filter = ('category', 'is_active', 'is_consumable')
    search_fields = ('name', 'code', 'barcode')

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('item', 'movement_type', 'quantity', 'movement_date', 'performed_by')
    list_filter = ('movement_type', 'movement_date')
    search_fields = ('item__name', 'reference')
    date_hierarchy = 'movement_date'

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'supplier', 'order_date', 'total_amount', 'status')
    list_filter = ('status', 'order_date')
    search_fields = ('po_number', 'supplier__name')
    inlines = [PurchaseOrderItemInline]
    date_hierarchy = 'order_date'
