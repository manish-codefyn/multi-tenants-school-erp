from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Count
from apps.core.permissions.mixins import PermissionRequiredMixin
from apps.core.utils.tenant import get_current_tenant
from .models import Category, Supplier, Item, StockMovement, PurchaseOrder

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
        
        return context

# ==================== CATEGORY ====================

class CategoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Category
    template_name = 'inventory/category_list.html'
    context_object_name = 'categories'
    permission_required = 'inventory.view_category'

class CategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Category
    fields = ['name', 'code', 'description', 'parent_category', 'is_consumable', 
              'requires_serial_number', 'requires_maintenance', 'low_stock_threshold', 
              'reorder_quantity', 'is_active']
    template_name = 'inventory/category_form.html'
    success_url = reverse_lazy('inventory:category_list')
    permission_required = 'inventory.add_category'

    def form_valid(self, form):
        messages.success(self.request, "Category created successfully.")
        return super().form_valid(form)

class CategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Category
    fields = ['name', 'code', 'description', 'parent_category', 'is_consumable', 
              'requires_serial_number', 'requires_maintenance', 'low_stock_threshold', 
              'reorder_quantity', 'is_active']
    template_name = 'inventory/category_form.html'
    success_url = reverse_lazy('inventory:category_list')
    permission_required = 'inventory.change_category'

    def form_valid(self, form):
        messages.success(self.request, "Category updated successfully.")
        return super().form_valid(form)

class CategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Category
    template_name = 'inventory/confirm_delete.html'
    success_url = reverse_lazy('inventory:category_list')
    permission_required = 'inventory.delete_category'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Category deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== SUPPLIER ====================

class SupplierListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Supplier
    template_name = 'inventory/supplier_list.html'
    context_object_name = 'suppliers'
    permission_required = 'inventory.view_supplier'

class SupplierCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Supplier
    fields = ['name', 'code', 'supplier_type', 'contact_person', 'email', 'phone', 
              'address', 'city', 'state', 'pincode', 'gst_number', 'is_active']
    template_name = 'inventory/supplier_form.html'
    success_url = reverse_lazy('inventory:supplier_list')
    permission_required = 'inventory.add_supplier'

    def form_valid(self, form):
        messages.success(self.request, "Supplier created successfully.")
        return super().form_valid(form)

class SupplierUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Supplier
    fields = ['name', 'code', 'supplier_type', 'contact_person', 'email', 'phone', 
              'address', 'city', 'state', 'pincode', 'gst_number', 'is_active']
    template_name = 'inventory/supplier_form.html'
    success_url = reverse_lazy('inventory:supplier_list')
    permission_required = 'inventory.change_supplier'

    def form_valid(self, form):
        messages.success(self.request, "Supplier updated successfully.")
        return super().form_valid(form)

class SupplierDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Supplier
    template_name = 'inventory/confirm_delete.html'
    success_url = reverse_lazy('inventory:supplier_list')
    permission_required = 'inventory.delete_supplier'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Supplier deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== ITEM ====================

class ItemListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Item
    template_name = 'inventory/item_list.html'
    context_object_name = 'items'
    permission_required = 'inventory.view_item'

class ItemDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Item
    template_name = 'inventory/item_detail.html'
    context_object_name = 'item'
    permission_required = 'inventory.view_item'

class ItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Item
    fields = ['name', 'code', 'barcode', 'description', 'category', 'brand', 'unit', 
              'current_stock', 'minimum_stock', 'low_stock_threshold', 'reorder_quantity', 
              'cost_price', 'selling_price', 'storage_location', 'is_active']
    template_name = 'inventory/item_form.html'
    success_url = reverse_lazy('inventory:item_list')
    permission_required = 'inventory.add_item'

    def form_valid(self, form):
        messages.success(self.request, "Item created successfully.")
        return super().form_valid(form)

class ItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Item
    fields = ['name', 'code', 'barcode', 'description', 'category', 'brand', 'unit', 
              'current_stock', 'minimum_stock', 'low_stock_threshold', 'reorder_quantity', 
              'cost_price', 'selling_price', 'storage_location', 'is_active']
    template_name = 'inventory/item_form.html'
    success_url = reverse_lazy('inventory:item_list')
    permission_required = 'inventory.change_item'

    def form_valid(self, form):
        messages.success(self.request, "Item updated successfully.")
        return super().form_valid(form)

class ItemDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Item
    template_name = 'inventory/confirm_delete.html'
    success_url = reverse_lazy('inventory:item_list')
    permission_required = 'inventory.delete_item'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Item deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== STOCK MOVEMENT ====================

class StockMovementListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = StockMovement
    template_name = 'inventory/stock_movement_list.html'
    context_object_name = 'movements'
    permission_required = 'inventory.view_stockmovement'

class StockMovementCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = StockMovement
    fields = ['item', 'movement_type', 'quantity', 'unit_price', 'reference', 'notes']
    template_name = 'inventory/stock_movement_form.html'
    success_url = reverse_lazy('inventory:stock_movement_list')
    permission_required = 'inventory.add_stockmovement'

    def form_valid(self, form):
        form.instance.performed_by = self.request.user
        messages.success(self.request, "Stock movement recorded successfully.")
        return super().form_valid(form)
