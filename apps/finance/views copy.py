from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Count
from apps.core.permissions.mixins import PermissionRequiredMixin
from apps.core.utils.tenant import get_current_tenant
from .models import FeeStructure, FeeDiscount, Invoice, Payment
from .forms import FeeStructureForm, FeeDiscountForm, InvoiceForm, InvoiceUpdateForm, PaymentForm

class FinanceDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'finance/dashboard.html'
    permission_required = 'finance.view_invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['total_invoices'] = Invoice.objects.filter(tenant=tenant).count()
        context['pending_payments'] = Invoice.objects.filter(tenant=tenant, status__in=['ISSUED', 'PARTIALLY_PAID', 'OVERDUE']).aggregate(Sum('due_amount'))['due_amount__sum'] or 0
        context['total_collected'] = Payment.objects.filter(tenant=tenant, status='COMPLETED').aggregate(Sum('amount'))['amount__sum'] or 0
        context['overdue_invoices'] = Invoice.objects.filter(tenant=tenant, is_overdue=True).count()
        
        return context

# ==================== FEE STRUCTURE ====================

class FeeStructureListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = FeeStructure
    template_name = 'finance/fee_structure_list.html'
    context_object_name = 'fee_structures'
    permission_required = 'finance.view_feestructure'

class FeeStructureCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = FeeStructure
    form_class = FeeStructureForm
    template_name = 'finance/fee_structure_form.html'
    success_url = reverse_lazy('finance:fee_structure_list')
    permission_required = 'finance.add_feestructure'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Fee Structure created successfully.")
        return super().form_valid(form)

class FeeStructureUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = FeeStructure
    form_class = FeeStructureForm
    template_name = 'finance/fee_structure_form.html'
    success_url = reverse_lazy('finance:fee_structure_list')
    permission_required = 'finance.change_feestructure'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Fee Structure updated successfully.")
        return super().form_valid(form)

class FeeStructureDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = FeeStructure
    template_name = 'finance/confirm_delete.html'
    success_url = reverse_lazy('finance:fee_structure_list')
    permission_required = 'finance.delete_feestructure'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Fee Structure deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== FEE DISCOUNT ====================

class FeeDiscountListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = FeeDiscount
    template_name = 'finance/fee_discount_list.html'
    context_object_name = 'discounts'
    permission_required = 'finance.view_feediscount'

class FeeDiscountCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = FeeDiscount
    form_class = FeeDiscountForm
    template_name = 'finance/fee_discount_form.html'
    success_url = reverse_lazy('finance:fee_discount_list')
    permission_required = 'finance.add_feediscount'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Fee Discount created successfully.")
        return super().form_valid(form)

class FeeDiscountUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = FeeDiscount
    form_class = FeeDiscountForm
    template_name = 'finance/fee_discount_form.html'
    success_url = reverse_lazy('finance:fee_discount_list')
    permission_required = 'finance.change_feediscount'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Fee Discount updated successfully.")
        return super().form_valid(form)

class FeeDiscountDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = FeeDiscount
    template_name = 'finance/confirm_delete.html'
    success_url = reverse_lazy('finance:fee_discount_list')
    permission_required = 'finance.delete_feediscount'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Fee Discount deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== INVOICE ====================

class InvoiceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Invoice
    template_name = 'finance/invoice_list.html'
    context_object_name = 'invoices'
    permission_required = 'finance.view_invoice'

class InvoiceDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Invoice
    template_name = 'finance/invoice_detail.html'
    context_object_name = 'invoice'
    permission_required = 'finance.view_invoice'

class InvoiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finance/invoice_form.html'
    success_url = reverse_lazy('finance:invoice_list')
    permission_required = 'finance.add_invoice'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Invoice created successfully.")
        return super().form_valid(form)

class InvoiceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceUpdateForm
    template_name = 'finance/invoice_form.html'
    success_url = reverse_lazy('finance:invoice_list')
    permission_required = 'finance.change_invoice'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Invoice updated successfully.")
        return super().form_valid(form)

class InvoiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'finance/confirm_delete.html'
    success_url = reverse_lazy('finance:invoice_list')
    permission_required = 'finance.delete_invoice'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Invoice deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== PAYMENT ====================

class PaymentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Payment
    template_name = 'finance/payment_list.html'
    context_object_name = 'payments'
    permission_required = 'finance.view_payment'

class PaymentDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Payment
    template_name = 'finance/payment_detail.html'
    context_object_name = 'payment'
    permission_required = 'finance.view_payment'

class PaymentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'finance/payment_form.html'
    success_url = reverse_lazy('finance:payment_list')
    permission_required = 'finance.add_payment'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.received_by = self.request.user
        messages.success(self.request, "Payment recorded successfully.")
        return super().form_valid(form)
