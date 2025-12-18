from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.db.models import Count, Sum, F
from django.db import models
from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from apps.core.utils.tenant import get_current_tenant
from .models import Category, Supplier, Item, StockMovement, PurchaseOrder
from .forms import CategoryForm, SupplierForm, ItemForm, StockMovementForm, PurchaseOrderForm

class InventoryDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'inventory/dashboard.html'
    permission_required = 'inventory.view_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['total_items'] = Item.objects.filter(tenant=tenant, is_active=True).count()
        context['low_stock_items'] = Item.objects.filter(tenant=tenant, is_active=True, current_stock__lte=models.F('low_stock_threshold')).count()
        context['total_suppliers'] = Supplier.objects.filter(tenant=tenant, is_active=True).count()
        context['total_categories'] = Category.objects.filter(tenant=tenant, is_active=True).count()
        context['pending_orders'] = PurchaseOrder.objects.filter(tenant=tenant, status__in=['DRAFT', 'PENDING_APPROVAL']).count()
        
        # Recent
        context['recent_movements'] = StockMovement.objects.filter(tenant=tenant).select_related('item').order_by('-movement_date')[:5]
        
        return context

# ==================== CATEGORY ====================

class CategoryListView(BaseListView):
    model = Category
    template_name = 'inventory/category_list.html'
    context_object_name = 'categories'
    permission_required = 'inventory.view_category'
    search_fields = ['name', 'code']
    filter_fields = ['is_active', 'parent_category']

class CategoryCreateView(BaseCreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'inventory/category_form.html'
    permission_required = 'inventory.add_category'
    success_url = reverse_lazy('inventory:category_list')

class CategoryUpdateView(BaseUpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'inventory/category_form.html'
    permission_required = 'inventory.change_category'
    success_url = reverse_lazy('inventory:category_list')

class CategoryDeleteView(BaseDeleteView):
    model = Category
    template_name = 'inventory/confirm_delete.html'
    permission_required = 'inventory.delete_category'
    success_url = reverse_lazy('inventory:category_list')

# ==================== SUPPLIER ====================

class SupplierListView(BaseListView):
    model = Supplier
    template_name = 'inventory/supplier_list.html'
    context_object_name = 'suppliers'
    permission_required = 'inventory.view_supplier'
    search_fields = ['name', 'code', 'email', 'phone']
    filter_fields = ['supplier_type', 'is_active']

class SupplierCreateView(BaseCreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_form.html'
    permission_required = 'inventory.add_supplier'
    success_url = reverse_lazy('inventory:supplier_list')

class SupplierUpdateView(BaseUpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_form.html'
    permission_required = 'inventory.change_supplier'
    success_url = reverse_lazy('inventory:supplier_list')

class SupplierDeleteView(BaseDeleteView):
    model = Supplier
    template_name = 'inventory/confirm_delete.html'
    permission_required = 'inventory.delete_supplier'
    success_url = reverse_lazy('inventory:supplier_list')

# ==================== ITEM ====================

class ItemListView(BaseListView):
    model = Item
    template_name = 'inventory/item_list.html'
    context_object_name = 'items'
    permission_required = 'inventory.view_item'
    search_fields = ['name', 'code', 'barcode']
    filter_fields = ['category', 'brand', 'is_active']

class ItemCreateView(BaseCreateView):
    model = Item
    form_class = ItemForm
    template_name = 'inventory/item_form.html'
    permission_required = 'inventory.add_item'
    success_url = reverse_lazy('inventory:item_list')

class ItemUpdateView(BaseUpdateView):
    model = Item
    form_class = ItemForm
    template_name = 'inventory/item_form.html'
    permission_required = 'inventory.change_item'
    success_url = reverse_lazy('inventory:item_list')

class ItemDeleteView(BaseDeleteView):
    model = Item
    template_name = 'inventory/confirm_delete.html'
    permission_required = 'inventory.delete_item'
    success_url = reverse_lazy('inventory:item_list')

# ==================== STOCK MOVEMENT ====================

class StockMovementListView(BaseListView):
    model = StockMovement
    template_name = 'inventory/stock_movement_list.html'
    context_object_name = 'movements'
    permission_required = 'inventory.view_stockmovement'
    search_fields = ['item__name', 'reference']
    filter_fields = ['movement_type']

class StockMovementCreateView(BaseCreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/stock_movement_form.html'
    permission_required = 'inventory.add_stockmovement'
    success_url = reverse_lazy('inventory:stock_movement_list')

    def form_valid(self, form):
        form.instance.performed_by = self.request.user
        return super().form_valid(form)

# ==================== PURCHASE ORDER ====================

class PurchaseOrderListView(BaseListView):
    model = PurchaseOrder
    template_name = 'inventory/purchase_order_list.html'
    context_object_name = 'orders'
    permission_required = 'inventory.view_purchaseorder'
    search_fields = ['po_number', 'supplier__name']
    filter_fields = ['status']

class PurchaseOrderCreateView(BaseCreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'inventory/purchase_order_form.html'
    permission_required = 'inventory.add_purchaseorder'
    success_url = reverse_lazy('inventory:purchase_order_list')

    def form_valid(self, form):
        form.instance.requested_by = self.request.user
        return super().form_valid(form)

class PurchaseOrderUpdateView(BaseUpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'inventory/purchase_order_form.html'
    permission_required = 'inventory.change_purchaseorder'
    success_url = reverse_lazy('inventory:purchase_order_list')

class PurchaseOrderDeleteView(BaseDeleteView):
    model = PurchaseOrder
    template_name = 'inventory/confirm_delete.html'
    permission_required = 'inventory.delete_purchaseorder'
    success_url = reverse_lazy('inventory:purchase_order_list')
