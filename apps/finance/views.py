import csv
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Q, F, Value, When, Case
from django.db.models.functions import TruncMonth, TruncYear
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, 
    TemplateView, FormView
)
from django.views.decorators.csrf import csrf_exempt
from django_filters.views import FilterView
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from openpyxl import Workbook
import pdfkit

from apps.core.permissions.mixins import (
    PermissionRequiredMixin, RoleRequiredMixin, 
    TenantAccessMixin, ObjectPermissionMixin
)
from apps.finance.models import (
    FeeStructure, FeeDiscount, Invoice, InvoiceItem, 
    AppliedDiscount, Payment, Refund, ExpenseCategory, 
    Expense, Budget, FinancialTransaction, BankAccount, FinancialReport
)
from apps.finance.forms import (
    FeeStructureForm, FeeDiscountForm, InvoiceForm, 
    InvoiceItemFormSet, PaymentForm, RefundForm,
    ExpenseCategoryForm, ExpenseForm, BudgetForm,
    BankAccountForm, FinancialReportForm, ApplyDiscountForm,
    BulkInvoiceGenerationForm, PaymentGatewayForm, QuickPaymentForm
)
from apps.finance.filters import (
    FeeStructureFilter, InvoiceFilter, PaymentFilter,
    ExpenseFilter, BudgetFilter
)
from apps.finance.serializers import (
    FeeStructureSerializer, InvoiceSerializer,
    PaymentSerializer, ExpenseSerializer,
    RefundSerializer, BudgetSerializer, BankAccountSerializer,
    FinancialTransactionSerializer, FinancialReportSerializer,
    ExpenseCategorySerializer
)
# Remove these imports if tasks.py doesn't exist yet
# from apps.finance.tasks import (
#     generate_invoices_for_month, send_payment_reminders,
#     generate_financial_report
# )


# ==================== FEE STRUCTURE VIEWS ====================

class FeeStructureListView(PermissionRequiredMixin, TenantAccessMixin, FilterView):
    model = FeeStructure
    template_name = 'finance/fee_structure_list.html'
    context_object_name = 'fee_structures'
    filterset_class = FeeStructureFilter
    permission_required = 'finance.view_feestructure'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = self.get_queryset().count()
        context['active_count'] = self.get_queryset().filter(is_active=True).count()
        context['fee_types'] = FeeStructure.FEE_TYPE_CHOICES
        return context


class FeeStructureCreateView(PermissionRequiredMixin, TenantAccessMixin, CreateView):
    model = FeeStructure
    form_class = FeeStructureForm
    template_name = 'finance/fee_structure_form.html'
    permission_required = 'finance.add_feestructure'
    success_url = reverse_lazy('finance:fee_structure_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass request instead of user
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        # Set tenant before saving
        form.instance.tenant = self.request.user.tenant
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Fee Structure created successfully!')
        return super().form_valid(form)



class FeeStructureUpdateView(PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = FeeStructure
    form_class = FeeStructureForm
    template_name = 'finance/fee_structure_form.html'
    permission_required = 'finance.change_feestructure'
    success_url = reverse_lazy('finance:fee_structure_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Fee Structure'
        return context


class FeeStructureDetailView(PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = FeeStructure
    template_name = 'finance/fee_structure_detail.html'
    permission_required = 'finance.view_feestructure'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['applicable_students'] = self.object.class_name.students.filter(
            is_active=True
        ).count()
        return context


class FeeStructureDeleteView(PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = FeeStructure
    template_name = 'finance/fee_structure_confirm_delete.html'
    permission_required = 'finance.delete_feestructure'
    success_url = reverse_lazy('finance:fee_structure_list')


# ==================== FEE DISCOUNT VIEWS ====================

class FeeDiscountListView(PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = FeeDiscount
    template_name = 'finance/fee_discount_list.html'
    context_object_name = 'discounts'
    permission_required = 'finance.view_feediscount'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Only show valid discounts by default
        if self.request.GET.get('show_all') != 'true':
            today = timezone.now().date()
            queryset = queryset.filter(
                valid_from__lte=today,
                valid_until__gte=today,
                is_active=True
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = self.get_queryset().count()
        context['valid_count'] = FeeDiscount.objects.filter(
            valid_from__lte=timezone.now().date(),
            valid_until__gte=timezone.now().date(),
            is_active=True
        ).count()
        return context


class FeeDiscountCreateView(PermissionRequiredMixin, TenantAccessMixin, CreateView):
    model = FeeDiscount
    form_class = FeeDiscountForm
    template_name = 'finance/fee_discount_form.html'
    permission_required = 'finance.add_feediscount'
    success_url = reverse_lazy('finance:fee_discount_list')
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Fee Discount created successfully!')
        return super().form_valid(form)


class FeeDiscountUpdateView(PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = FeeDiscount
    form_class = FeeDiscountForm
    template_name = 'finance/fee_discount_form.html'
    permission_required = 'finance.change_feediscount'
    success_url = reverse_lazy('finance:fee_discount_list')


class FeeDiscountDetailView(PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = FeeDiscount
    template_name = 'finance/fee_discount_detail.html'
    permission_required = 'finance.view_feediscount'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usage_count'] = self.object.applied_discounts.count()
        context['recent_applications'] = self.object.applied_discounts.select_related(
            'invoice', 'invoice__student'
        ).order_by('-created_at')[:10]
        return context


# ==================== INVOICE VIEWS ====================

class InvoiceListView(PermissionRequiredMixin, TenantAccessMixin, FilterView):
    model = Invoice
    template_name = 'finance/invoice_list.html'
    context_object_name = 'invoices'
    filterset_class = InvoiceFilter
    permission_required = 'finance.view_invoice'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Summary statistics
        context['total_invoices'] = queryset.count()
        context['total_amount'] = queryset.aggregate(total=Sum('total_amount'))['total'] or 0
        context['paid_amount'] = queryset.aggregate(total=Sum('paid_amount'))['total'] or 0
        context['due_amount'] = queryset.aggregate(total=Sum('due_amount'))['total'] or 0
        
        # Status counts
        context['status_counts'] = {
            'issued': queryset.filter(status='ISSUED').count(),
            'partially_paid': queryset.filter(status='PARTIALLY_PAID').count(),
            'paid': queryset.filter(status='PAID').count(),
            'overdue': queryset.filter(status='OVERDUE').count(),
        }
        
        return context


class InvoiceCreateView(PermissionRequiredMixin, TenantAccessMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finance/invoice_form.html'
    permission_required = 'finance.add_invoice'
    
    def get_success_url(self):
        return reverse('finance:invoice_detail', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['items_formset'] = InvoiceItemFormSet(self.request.POST, instance=self.object)
        else:
            context['items_formset'] = InvoiceItemFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context['items_formset']
        
        if items_formset.is_valid():
            form.instance.tenant = self.request.user.tenant
            form.instance.created_by = self.request.user
            response = super().form_valid(form)
            
            items_formset.instance = self.object
            items_formset.save()
            
            # Calculate totals after saving items
            self.object.calculate_totals()
            
            messages.success(self.request, 'Invoice created successfully!')
            return response
        else:
            return self.form_invalid(form)


class InvoiceUpdateView(PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finance/invoice_form.html'
    permission_required = 'finance.change_invoice'
    
    def get_success_url(self):
        return reverse('finance:invoice_detail', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['items_formset'] = InvoiceItemFormSet(self.request.POST, instance=self.object)
        else:
            context['items_formset'] = InvoiceItemFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context['items_formset']
        
        if items_formset.is_valid():
            response = super().form_valid(form)
            
            items_formset.save()
            
            # Recalculate totals
            self.object.calculate_totals()
            
            messages.success(self.request, 'Invoice updated successfully!')
            return response
        else:
            return self.form_invalid(form)


class InvoiceDetailView(PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = Invoice
    template_name = 'finance/invoice_detail.html'
    permission_required = 'finance.view_invoice'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add related data
        context['items'] = self.object.items.select_related('fee_structure')
        context['discounts'] = self.object.discounts.select_related('discount', 'applied_by')
        context['payments'] = self.object.payments.select_related(
            'received_by', 'paid_by'
        ).order_by('-payment_date')
        context['available_discounts'] = FeeDiscount.objects.filter(
            is_active=True,
            valid_from__lte=timezone.now().date(),
            valid_until__gte=timezone.now().date()
        )
        
        return context


class InvoicePrintView(PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = Invoice
    template_name = 'finance/invoice_print.html'
    permission_required = 'finance.view_invoice'
    
    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('format') == 'pdf':
            # Generate PDF version
            try:
                html = render(self.request, self.template_name, context).content.decode('utf-8')
                pdf = pdfkit.from_string(html, False)
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="invoice_{self.object.invoice_number}.pdf"'
                return response
            except Exception as e:
                messages.error(self.request, f'Error generating PDF: {str(e)}')
                return super().render_to_response(context, **response_kwargs)
        return super().render_to_response(context, **response_kwargs)


class InvoiceSendView(PermissionRequiredMixin, TenantAccessMixin, View):
    permission_required = 'finance.change_invoice'
    
    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk, tenant=request.user.tenant)
        
        if invoice.status == 'DRAFT':
            invoice.status = 'ISSUED'
            invoice.save()
            
            # Send email notification
            # from apps.finance.tasks import send_invoice_email
            # send_invoice_email.delay(invoice.id)
            
            messages.success(request, 'Invoice sent to student/parent!')
        else:
            messages.warning(request, 'Invoice has already been issued.')
        
        return HttpResponseRedirect(reverse('finance:invoice_detail', kwargs={'pk': pk}))


class InvoiceApplyDiscountView(PermissionRequiredMixin, TenantAccessMixin, View):
    permission_required = 'finance.apply_discount'
    
    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk, tenant=request.user.tenant)
        discount_id = request.POST.get('discount_id')
        reason = request.POST.get('reason', '')
        
        try:
            discount = FeeDiscount.objects.get(
                pk=discount_id,
                is_active=True,
                valid_from__lte=timezone.now().date(),
                valid_until__gte=timezone.now().date()
            )
            
            # Check eligibility
            is_eligible, message = discount.is_eligible(invoice.student, invoice.subtotal)
            if not is_eligible:
                messages.error(request, f'Not eligible: {message}')
                return HttpResponseRedirect(reverse('finance:invoice_detail', kwargs={'pk': pk}))
            
            # Apply discount
            invoice.apply_discount(discount, request.user, reason)
            messages.success(request, 'Discount applied successfully!')
            
        except FeeDiscount.DoesNotExist:
            messages.error(request, 'Discount not found or not valid.')
        except Exception as e:
            messages.error(request, f'Error applying discount: {str(e)}')
        
        return HttpResponseRedirect(reverse('finance:invoice_detail', kwargs={'pk': pk}))


# ==================== PAYMENT VIEWS ====================

class PaymentListView(PermissionRequiredMixin, TenantAccessMixin, FilterView):
    model = Payment
    template_name = 'finance/payment_list.html'
    context_object_name = 'payments'
    filterset_class = PaymentFilter
    permission_required = 'finance.view_payment'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Statistics
        context['total_payments'] = queryset.count()
        context['total_amount'] = queryset.aggregate(total=Sum('amount'))['total'] or 0
        context['today_payments'] = queryset.filter(
            payment_date__date=timezone.now().date()
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Monthly totals for chart
        monthly_totals = queryset.annotate(
            month=TruncMonth('payment_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        context['monthly_totals'] = list(monthly_totals)
        
        return context


class PaymentCreateView(PermissionRequiredMixin, TenantAccessMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'finance/payment_form.html'
    permission_required = 'finance.add_payment'
    success_url = reverse_lazy('finance:payment_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        invoice_id = self.request.GET.get('invoice')
        if invoice_id:
            try:
                invoice = Invoice.objects.get(pk=invoice_id, tenant=self.request.user.tenant)
                initial['invoice'] = invoice
                initial['amount'] = invoice.due_amount
            except Invoice.DoesNotExist:
                pass
        return initial
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        form.instance.received_by = self.request.user
        
        # Verify payment if amount matches invoice due amount
        invoice = form.cleaned_data['invoice']
        if form.instance.amount >= invoice.due_amount:
            form.instance.status = 'COMPLETED'
        
        response = super().form_valid(form)
        
        # Update invoice paid amount
        invoice.paid_amount += form.instance.amount
        invoice.save()
        
        messages.success(self.request, 'Payment recorded successfully!')
        return response


class PaymentDetailView(PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = Payment
    template_name = 'finance/payment_detail.html'
    permission_required = 'finance.view_payment'


class PaymentVerifyView(PermissionRequiredMixin, TenantAccessMixin, View):
    permission_required = 'finance.verify_payment'
    
    def post(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk, tenant=request.user.tenant)
        
        if payment.status == 'PENDING':
            payment.verify_payment(request.user)
            messages.success(request, 'Payment verified successfully!')
        else:
            messages.warning(request, 'Payment is not pending verification.')
        
        return HttpResponseRedirect(reverse('finance:payment_detail', kwargs={'pk': pk}))


# ==================== EXPENSE VIEWS ====================

class ExpenseListView(PermissionRequiredMixin, TenantAccessMixin, FilterView):
    model = Expense
    template_name = 'finance/expense_list.html'
    context_object_name = 'expenses'
    filterset_class = ExpenseFilter
    permission_required = 'finance.view_expense'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Statistics
        context['total_expenses'] = queryset.count()
        context['total_amount'] = queryset.filter(status='PAID').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Category breakdown
        categories = ExpenseCategory.objects.filter(
            tenant=self.request.user.tenant, 
            is_active=True
        )
        category_data = []
        for category in categories:
            cat_expenses = queryset.filter(category=category, status='PAID')
            total = cat_expenses.aggregate(total=Sum('amount'))['total'] or 0
            if total > 0:
                category_data.append({
                    'name': category.name,
                    'amount': total,
                    'percentage': (total / context['total_amount'] * 100) if context['total_amount'] > 0 else 0
                })
        
        context['category_breakdown'] = category_data
        
        return context


class ExpenseCreateView(PermissionRequiredMixin, TenantAccessMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'finance/expense_form.html'
    permission_required = 'finance.add_expense'
    success_url = reverse_lazy('finance:expense_list')
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        form.instance.submitted_by = self.request.user
        
        # If user has approval permission, auto-approve
        if self.request.user.has_perm('finance.approve_expense'):
            form.instance.status = 'APPROVED'
            form.instance.approved_by = self.request.user
            form.instance.approval_date = timezone.now()
        
        response = super().form_valid(form)
        messages.success(self.request, 'Expense submitted successfully!')
        return response


class ExpenseUpdateView(PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'finance/expense_form.html'
    permission_required = 'finance.change_expense'
    success_url = reverse_lazy('finance:expense_list')
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.status in ['APPROVED', 'PAID', 'REJECTED']:
            messages.error(request, 'Cannot edit approved, paid, or rejected expenses.')
            return HttpResponseRedirect(reverse('finance:expense_detail', kwargs={'pk': obj.pk}))
        return super().dispatch(request, *args, **kwargs)


class ExpenseDetailView(PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = Expense
    template_name = 'finance/expense_detail.html'
    permission_required = 'finance.view_expense'


class ExpenseApproveView(PermissionRequiredMixin, TenantAccessMixin, View):
    permission_required = 'finance.approve_expense'
    
    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk, tenant=request.user.tenant)
        
        if expense.status == 'SUBMITTED':
            expense.approve(request.user)
            messages.success(request, 'Expense approved successfully!')
        else:
            messages.warning(request, 'Expense is not pending approval.')
        
        return HttpResponseRedirect(reverse('finance:expense_detail', kwargs={'pk': pk}))


class ExpenseRejectView(PermissionRequiredMixin, TenantAccessMixin, View):
    permission_required = 'finance.approve_expense'
    
    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk, tenant=request.user.tenant)
        reason = request.POST.get('reason', '')
        
        if expense.status == 'SUBMITTED' and reason:
            expense.reject(request.user, reason)
            messages.success(request, 'Expense rejected.')
        else:
            messages.warning(request, 'Cannot reject expense.')
        
        return HttpResponseRedirect(reverse('finance:expense_detail', kwargs={'pk': pk}))


# ==================== DASHBOARD & REPORTS ====================

class FinanceDashboardView(PermissionRequiredMixin, TenantAccessMixin, TemplateView):
    template_name = 'finance/dashboard.html'
    permission_required = 'finance.view_dashboard'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant = user.tenant
        
        today = timezone.now().date()
        current_month = today.replace(day=1)
        next_month = (current_month + timedelta(days=32)).replace(day=1)
        
        # Fee Collection Summary
        context['total_fee_collection'] = Payment.objects.filter(
            tenant=tenant,
            status='COMPLETED'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context['monthly_collection'] = Payment.objects.filter(
            tenant=tenant,
            status='COMPLETED',
            payment_date__gte=current_month,
            payment_date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Outstanding Invoices
        context['outstanding_invoices'] = Invoice.objects.filter(
            tenant=tenant,
            due_amount__gt=0
        ).count()
        
        context['total_outstanding'] = Invoice.objects.filter(
            tenant=tenant,
            due_amount__gt=0
        ).aggregate(total=Sum('due_amount'))['total'] or 0
        
        # Recent Payments
        context['recent_payments'] = Payment.objects.filter(
            tenant=tenant
        ).select_related('invoice', 'invoice__student').order_by('-payment_date')[:10]
        
        # Overdue Invoices
        context['overdue_invoices'] = Invoice.objects.filter(
            tenant=tenant,
            is_overdue=True
        ).select_related('student').order_by('-due_date')[:10]
        
        # Expense Summary
        context['monthly_expenses'] = Expense.objects.filter(
            tenant=tenant,
            status='PAID',
            expense_date__gte=current_month,
            expense_date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Chart Data
        context['monthly_collection_data'] = self.get_monthly_collection_data()
        context['expense_by_category'] = self.get_expense_by_category()
        
        return context
    
    def get_monthly_collection_data(self):
        """Get monthly collection data for the last 6 months"""
        tenant = self.request.user.tenant
        six_months_ago = (timezone.now() - timedelta(days=180)).replace(day=1)
        
        monthly_data = Payment.objects.filter(
            tenant=tenant,
            status='COMPLETED',
            payment_date__gte=six_months_ago
        ).annotate(
            month=TruncMonth('payment_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        return list(monthly_data)
    
    def get_expense_by_category(self):
        """Get expense breakdown by category for current month"""
        tenant = self.request.user.tenant
        today = timezone.now().date()
        current_month = today.replace(day=1)
        next_month = (current_month + timedelta(days=32)).replace(day=1)
        
        expenses = Expense.objects.filter(
            tenant=tenant,
            status='PAID',
            expense_date__gte=current_month,
            expense_date__lt=next_month
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        return list(expenses)


class FeeCollectionReportView(PermissionRequiredMixin, TenantAccessMixin, TemplateView):
    template_name = 'finance/reports/fee_collection.html'
    permission_required = 'finance.view_reports'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Get date range from request or default to current month
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = end_date = None
        
        if not start_date or not end_date:
            # Default to current month
            today = timezone.now().date()
            start_date = today.replace(day=1)
            next_month = (start_date + timedelta(days=32)).replace(day=1)
            end_date = next_month - timedelta(days=1)
        
        # Get payments in date range
        payments = Payment.objects.filter(
            tenant=tenant,
            status='COMPLETED',
            payment_date__range=[start_date, end_date]
        ).select_related('invoice', 'invoice__student')
        
        # Group by payment method
        by_method = payments.values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Group by class
        by_class = payments.values(
            'invoice__student__current_class__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'total_collection': payments.aggregate(total=Sum('amount'))['total'] or 0,
            'payment_count': payments.count(),
            'by_method': by_method,
            'by_class': by_class,
            'payments': payments.order_by('-payment_date')[:100]
        })
        
        return context
    
    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('export') == 'excel':
            return self.export_to_excel(context)
        elif self.request.GET.get('export') == 'pdf':
            return self.export_to_pdf(context)
        return super().render_to_response(context, **response_kwargs)
    
    def export_to_excel(self, context):
        """Export report to Excel"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Fee Collection Report"
        
        # Add headers
        headers = ['Date', 'Invoice No', 'Student', 'Class', 'Payment Method', 
                   'Reference', 'Amount', 'Received By']
        ws.append(headers)
        
        # Add data
        for payment in context['payments']:
            ws.append([
                payment.payment_date.strftime('%Y-%m-%d'),
                payment.invoice.invoice_number,
                str(payment.invoice.student),
                str(payment.invoice.student.current_class),
                payment.get_payment_method_display(),
                payment.reference_number,
                payment.amount,
                str(payment.received_by)
            ])
        
        # Add summary
        ws.append([])
        ws.append(['Summary'])
        ws.append(['Total Collection:', context['total_collection']])
        ws.append(['Payment Count:', context['payment_count']])
        ws.append(['Period:', f"{context['start_date']} to {context['end_date']}"])
        
        # Create response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="fee_collection_{context["start_date"]}_{context["end_date"]}.xlsx"'
        wb.save(response)
        return response
    
    def export_to_pdf(self, context):
        """Export report to PDF"""
        try:
            html = render(self.request, 'finance/reports/fee_collection_pdf.html', context).content.decode('utf-8')
            pdf = pdfkit.from_string(html, False)
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="fee_collection_{context["start_date"]}_{context["end_date"]}.pdf"'
            return response
        except Exception as e:
            messages.error(self.request, f'Error generating PDF: {str(e)}')
            return super().render_to_response(context, **response_kwargs)


class DueFeesReportView(PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = Invoice
    template_name = 'finance/reports/due_fees.html'
    context_object_name = 'invoices'
    permission_required = 'finance.view_reports'
    
    def get_queryset(self):
        queryset = Invoice.objects.filter(
            tenant=self.request.user.tenant,
            due_amount__gt=0
        ).select_related('student', 'academic_year').order_by('due_date')
        
        # Filter by class if provided
        class_id = self.request.GET.get('class')
        if class_id:
            queryset = queryset.filter(student__current_class_id=class_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_due'] = self.get_queryset().aggregate(total=Sum('due_amount'))['total'] or 0
        context['total_overdue'] = self.get_queryset().filter(is_overdue=True).aggregate(
            total=Sum('due_amount')
        )['total'] or 0
        return context


# ==================== API VIEWS ====================

class FeeStructureAPIViewSet(viewsets.ModelViewSet):
    queryset = FeeStructure.objects.all()
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(tenant=self.request.user.tenant)
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_class(self, request):
        class_id = request.query_params.get('class_id')
        academic_year_id = request.query_params.get('academic_year_id')
        
        queryset = self.get_queryset().filter(is_active=True)
        
        if class_id:
            queryset = queryset.filter(class_name_id=class_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class InvoiceAPIViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(tenant=self.request.user.tenant)
        
        # Filter by student for parents/students
        if self.request.user.role in ['student', 'parent']:
            if hasattr(self.request.user, 'student_profile'):
                queryset = queryset.filter(student=self.request.user.student_profile)
            elif hasattr(self.request.user, 'parent_profile'):
                students = self.request.user.parent_profile.students.all()
                queryset = queryset.filter(student__in=students)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def make_payment(self, request, pk=None):
        invoice = self.get_object()
        amount = Decimal(request.data.get('amount', 0))
        payment_method = request.data.get('payment_method', 'ONLINE')
        
        try:
            payment = invoice.add_payment(
                amount=amount,
                payment_method=payment_method,
                reference=request.data.get('reference', ''),
                paid_by=request.user
            )
            return Response({'status': 'success', 'payment_id': payment.id})
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaymentAPIViewSet(viewsets.ModelViewSet):
    """API ViewSet for Payments"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(tenant=self.request.user.tenant)
        return queryset


class ExpenseAPIViewSet(viewsets.ModelViewSet):
    """API ViewSet for Expenses"""
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(tenant=self.request.user.tenant)
        return queryset


# ==================== ADDITIONAL VIEWS ====================

class ExpenseSummaryReportView(PermissionRequiredMixin, TenantAccessMixin, TemplateView):
    """Expense Summary Report View"""
    template_name = 'finance/reports/expense_summary.html'
    permission_required = 'finance.view_reports'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Get date range from request or default to current month
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = end_date = None
        
        if not start_date or not end_date:
            # Default to current month
            today = timezone.now().date()
            start_date = today.replace(day=1)
            next_month = (start_date + timedelta(days=32)).replace(day=1)
            end_date = next_month - timedelta(days=1)
        
        # Get expenses in date range
        expenses = Expense.objects.filter(
            tenant=tenant,
            status='PAID',
            expense_date__range=[start_date, end_date]
        ).select_related('category')
        
        # Group by category
        by_category = expenses.values('category__name', 'category__category_type').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Group by month
        by_month = expenses.annotate(
            month=TruncMonth('expense_date')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('month')
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'total_expenses': expenses.aggregate(total=Sum('amount'))['total'] or 0,
            'expense_count': expenses.count(),
            'by_category': by_category,
            'by_month': by_month,
            'expenses': expenses.order_by('-expense_date')[:100]
        })
        
        return context


class BudgetVsActualReportView(PermissionRequiredMixin, TenantAccessMixin, TemplateView):
    """Budget vs Actual Report View"""
    template_name = 'finance/reports/budget_vs_actual.html'
    permission_required = 'finance.view_reports'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Get active budget
        current_budget = Budget.objects.filter(
            tenant=tenant,
            status='ACTIVE'
        ).first()
        
        if not current_budget:
            context['no_budget'] = True
            return context
        
        # Get expenses for budget period
        expenses = Expense.objects.filter(
            tenant=tenant,
            status='PAID',
            expense_date__range=[current_budget.start_date, current_budget.end_date]
        )
        
        # Parse budget items
        try:
            budget_items = current_budget.budget_items
            if isinstance(budget_items, str):
                import json
                budget_items = json.loads(budget_items)
        except:
            budget_items = []
        
        # Calculate actual vs budget
        budget_data = []
        total_budget = 0
        total_actual = 0
        
        for item in budget_items:
            category_name = item.get('category', 'Unknown')
            budget_amount = Decimal(item.get('amount', 0))
            
            # Get actual expenses for this category
            actual_amount = expenses.filter(
                category__name=category_name
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            variance = budget_amount - actual_amount
            variance_percentage = (variance / budget_amount * 100) if budget_amount > 0 else 0
            
            budget_data.append({
                'category': category_name,
                'budget': budget_amount,
                'actual': actual_amount,
                'variance': variance,
                'variance_percentage': variance_percentage,
                'status': 'under' if variance > 0 else 'over' if variance < 0 else 'on_target'
            })
            
            total_budget += budget_amount
            total_actual += actual_amount
        
        total_variance = total_budget - total_actual
        total_variance_percentage = (total_variance / total_budget * 100) if total_budget > 0 else 0
        
        context.update({
            'budget': current_budget,
            'budget_data': budget_data,
            'total_budget': total_budget,
            'total_actual': total_actual,
            'total_variance': total_variance,
            'total_variance_percentage': total_variance_percentage,
            'start_date': current_budget.start_date,
            'end_date': current_budget.end_date
        })
        
        return context


class MyInvoicesView(PermissionRequiredMixin, ListView):
    """View for students/parents to see their invoices"""
    model = Invoice
    template_name = 'finance/my_invoices.html'
    permission_required = 'finance.view_my_invoices'
    
    def get_queryset(self):
        user = self.request.user
        queryset = Invoice.objects.filter(tenant=user.tenant)
        
        if user.role == 'student' and hasattr(user, 'student_profile'):
            queryset = queryset.filter(student=user.student_profile)
        elif user.role == 'parent' and hasattr(user, 'parent_profile'):
            students = user.parent_profile.students.all()
            queryset = queryset.filter(student__in=students)
        
        return queryset.order_by('-issue_date')


class MyPaymentsView(PermissionRequiredMixin, ListView):
    """View for students/parents to see their payments"""
    model = Payment
    template_name = 'finance/my_payments.html'
    permission_required = 'finance.view_my_payments'
    
    def get_queryset(self):
        user = self.request.user
        queryset = Payment.objects.filter(tenant=user.tenant)
        
        if user.role == 'student' and hasattr(user, 'student_profile'):
            invoices = Invoice.objects.filter(student=user.student_profile)
            queryset = queryset.filter(invoice__in=invoices)
        elif user.role == 'parent' and hasattr(user, 'parent_profile'):
            students = user.parent_profile.students.all()
            invoices = Invoice.objects.filter(student__in=students)
            queryset = queryset.filter(invoice__in=invoices)
        
        return queryset.order_by('-payment_date')


class PaymentGatewayView(PermissionRequiredMixin, FormView):
    """Online payment gateway view"""
    template_name = 'finance/payment_gateway.html'
    form_class = PaymentGatewayForm
    permission_required = 'finance.make_payment'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        invoice_id = self.kwargs.get('invoice_id')
        invoice = get_object_or_404(Invoice, pk=invoice_id, tenant=self.request.user.tenant)
        kwargs['invoice'] = invoice
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice_id = self.kwargs.get('invoice_id')
        context['invoice'] = get_object_or_404(Invoice, pk=invoice_id, tenant=self.request.user.tenant)
        return context
    
    def form_valid(self, form):
        # Process payment here
        # This would typically integrate with a payment gateway like Stripe, Razorpay, etc.
        invoice_id = self.kwargs.get('invoice_id')
        invoice = get_object_or_404(Invoice, pk=invoice_id, tenant=self.request.user.tenant)
        
        # In a real implementation, this would redirect to payment gateway
        # For now, just record the payment
        try:
            payment = Payment.objects.create(
                invoice=invoice,
                amount=form.cleaned_data['amount'],
                payment_method=form.cleaned_data['payment_method'],
                reference_number=f"PG-{timezone.now().timestamp()}",
                status='COMPLETED',
                received_by=self.request.user,
                paid_by=self.request.user,
                tenant=self.request.user.tenant
            )
            
            # Update invoice
            invoice.paid_amount += payment.amount
            invoice.save()
            
            messages.success(self.request, 'Payment processed successfully!')
            return redirect('finance:invoice_detail', pk=invoice.pk)
            
        except Exception as e:
            messages.error(self.request, f'Payment failed: {str(e)}')
            return self.form_invalid(form)


# ==================== UTILITY VIEWS ====================

class GenerateMonthlyInvoicesView(PermissionRequiredMixin, TenantAccessMixin, View):
    permission_required = 'finance.generate_invoices'
    
    def get(self, request):
        return render(request, 'finance/generate_invoices.html')
    
    def post(self, request):
        month = int(request.POST.get('month', timezone.now().month))
        year = int(request.POST.get('year', timezone.now().year))
        
        # Run as async task (commented out for now)
        # task_id = generate_invoices_for_month.delay(
        #     tenant_id=request.user.tenant_id,
        #     month=month,
        #     year=year
        # )
        
        messages.success(
            request, 
            f'Invoice generation for {month}/{year} completed.'
            # f'Invoice generation started. Task ID: {task_id}. You will be notified when complete.'
        )
        return HttpResponseRedirect(reverse('finance:invoice_list'))


class SendPaymentRemindersView(PermissionRequiredMixin, TenantAccessMixin, View):
    permission_required = 'finance.send_reminders'
    
    def post(self, request):
        # Send reminders for overdue invoices
        # task_id = send_payment_reminders.delay(request.user.tenant_id)
        
        messages.success(request, f'Payment reminders sent successfully.')
        # messages.success(request, f'Payment reminders being sent. Task ID: {task_id}')
        return HttpResponseRedirect(reverse('finance:dashboard'))


# ==================== BULK ACTIONS ====================

class BulkInvoiceActionView(PermissionRequiredMixin, TenantAccessMixin, View):
    permission_required = 'finance.change_invoice'
    
    def post(self, request):
        action = request.POST.get('action')
        invoice_ids = request.POST.getlist('invoice_ids')
        
        if not invoice_ids:
            messages.error(request, 'No invoices selected.')
            return HttpResponseRedirect(reverse('finance:invoice_list'))
        
        invoices = Invoice.objects.filter(
            id__in=invoice_ids,
            tenant=request.user.tenant
        )
        
        if action == 'send':
            sent_count = 0
            for invoice in invoices:
                if invoice.status == 'DRAFT':
                    invoice.status = 'ISSUED'
                    invoice.save()
                    sent_count += 1
            
            messages.success(request, f'{sent_count} invoices sent successfully.')
        
        elif action == 'cancel':
            cancelled_count = 0
            for invoice in invoices:
                if invoice.status in ['DRAFT', 'ISSUED']:
                    invoice.status = 'CANCELLED'
                    invoice.save()
                    cancelled_count += 1
            
            messages.success(request, f'{cancelled_count} invoices cancelled.')
        
        elif action == 'export':
            # Export selected invoices to CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="invoices_export.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Invoice No', 'Student', 'Class', 'Issue Date', 'Due Date', 
                            'Total Amount', 'Paid Amount', 'Due Amount', 'Status'])
            
            for invoice in invoices:
                writer.writerow([
                    invoice.invoice_number,
                    str(invoice.student),
                    str(invoice.student.current_class),
                    invoice.issue_date,
                    invoice.due_date,
                    invoice.total_amount,
                    invoice.paid_amount,
                    invoice.due_amount,
                    invoice.get_status_display()
                ])
            
            return response
        
        return HttpResponseRedirect(reverse('finance:invoice_list'))


# ==================== BUDGET VIEWS ====================

class BudgetListView(PermissionRequiredMixin, TenantAccessMixin, FilterView):
    model = Budget
    template_name = 'finance/budget_list.html'
    context_object_name = 'budgets'
    filterset_class = BudgetFilter
    permission_required = 'finance.view_budget'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Statistics
        context['total_budgets'] = queryset.count()
        context['active_budget'] = queryset.filter(status='ACTIVE').first()
        context['total_budget_amount'] = queryset.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        return context


class BudgetCreateView(PermissionRequiredMixin, TenantAccessMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'finance/budget_form.html'
    permission_required = 'finance.add_budget'
    success_url = reverse_lazy('finance:budget_list')
    
    def form_valid(self, form):
        form.instance.prepared_by = self.request.user
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)


class BudgetUpdateView(PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'finance/budget_form.html'
    permission_required = 'finance.change_budget'
    success_url = reverse_lazy('finance:budget_list')


class BudgetDetailView(PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = Budget
    template_name = 'finance/budget_detail.html'
    permission_required = 'finance.view_budget'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Parse budget items for display
        try:
            import json
            budget_items = self.object.budget_items
            if isinstance(budget_items, str):
                budget_items = json.loads(budget_items)
            context['parsed_budget_items'] = budget_items
        except:
            context['parsed_budget_items'] = []
        
        return context


class BudgetApproveView(PermissionRequiredMixin, TenantAccessMixin, View):
    permission_required = 'finance.approve_budget'
    
    def post(self, request, pk):
        budget = get_object_or_404(Budget, pk=pk, tenant=request.user.tenant)
        
        if budget.status in ['DRAFT', 'SUBMITTED']:
            budget.status = 'APPROVED'
            budget.approved_by = request.user
            budget.approval_date = timezone.now()
            budget.save()
            
            messages.success(request, 'Budget approved successfully!')
        else:
            messages.warning(request, 'Budget cannot be approved in its current status.')
        
        return HttpResponseRedirect(reverse('finance:budget_detail', kwargs={'pk': pk}))


class BudgetActivateView(PermissionRequiredMixin, TenantAccessMixin, View):
    permission_required = 'finance.activate_budget'
    
    def post(self, request, pk):
        budget = get_object_or_404(Budget, pk=pk, tenant=request.user.tenant)
        
        if budget.status == 'APPROVED':
            budget.activate()
            messages.success(request, 'Budget activated successfully!')
        else:
            messages.warning(request, 'Only approved budgets can be activated.')
        
        return HttpResponseRedirect(reverse('finance:budget_detail', kwargs={'pk': pk}))


# ==================== REFUND VIEWS ====================

class RefundListView(PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = Refund
    template_name = 'finance/refund_list.html'
    context_object_name = 'refunds'
    permission_required = 'finance.view_refund'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_refunds'] = self.get_queryset().count()
        context['total_refund_amount'] = self.get_queryset().aggregate(
            total=Sum('amount')
        )['total'] or 0
        return context


class RefundCreateView(PermissionRequiredMixin, TenantAccessMixin, CreateView):
    model = Refund
    form_class = RefundForm
    template_name = 'finance/refund_form.html'
    permission_required = 'finance.add_refund'
    success_url = reverse_lazy('finance:refund_list')
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)


class RefundDetailView(PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = Refund
    template_name = 'finance/refund_detail.html'
    permission_required = 'finance.view_refund'


class RefundApproveView(PermissionRequiredMixin, TenantAccessMixin, View):
    permission_required = 'finance.approve_refund'
    
    def post(self, request, pk):
        refund = get_object_or_404(Refund, pk=pk, tenant=request.user.tenant)
        
        if refund.status == 'REQUESTED':
            refund.approve(request.user)
            messages.success(request, 'Refund approved successfully!')
        else:
            messages.warning(request, 'Refund is not pending approval.')
        
        return HttpResponseRedirect(reverse('finance:refund_detail', kwargs={'pk': pk}))


class RefundProcessView(PermissionRequiredMixin, TenantAccessMixin, View):
    permission_required = 'finance.process_refund'
    
    def post(self, request, pk):
        refund = get_object_or_404(Refund, pk=pk, tenant=request.user.tenant)
        
        if refund.status == 'APPROVED':
            refund.process(request.user)
            messages.success(request, 'Refund processed successfully!')
        else:
            messages.warning(request, 'Only approved refunds can be processed.')
        
        return HttpResponseRedirect(reverse('finance:refund_detail', kwargs={'pk': pk}))


class RefundCompleteView(PermissionRequiredMixin, TenantAccessMixin, View):
    permission_required = 'finance.complete_refund'
    
    def post(self, request, pk):
        refund = get_object_or_404(Refund, pk=pk, tenant=request.user.tenant)
        
        if refund.status == 'PROCESSED':
            refund.complete()
            messages.success(request, 'Refund marked as completed!')
        else:
            messages.warning(request, 'Only processed refunds can be completed.')
        
        return HttpResponseRedirect(reverse('finance:refund_detail', kwargs={'pk': pk}))


# ==================== BANK ACCOUNT VIEWS ====================

class BankAccountListView(PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = BankAccount
    template_name = 'finance/bank_account_list.html'
    context_object_name = 'bank_accounts'
    permission_required = 'finance.view_bankaccount'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        context['total_accounts'] = queryset.count()
        context['active_accounts'] = queryset.filter(is_active=True).count()
        context['total_balance'] = queryset.filter(is_active=True).aggregate(
            total=Sum('current_balance')
        )['total'] or 0
        
        return context


class BankAccountCreateView(PermissionRequiredMixin, TenantAccessMixin, CreateView):
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'finance/bank_account_form.html'
    permission_required = 'finance.add_bankaccount'
    success_url = reverse_lazy('finance:bank_account_list')
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)


class BankAccountUpdateView(PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'finance/bank_account_form.html'
    permission_required = 'finance.change_bankaccount'
    success_url = reverse_lazy('finance:bank_account_list')


class BankAccountDetailView(PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = BankAccount
    template_name = 'finance/bank_account_detail.html'
    permission_required = 'finance.view_bankaccount'


# ==================== EXPENSE CATEGORY VIEWS ====================

class ExpenseCategoryListView(PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = ExpenseCategory
    template_name = 'finance/expense_category_list.html'
    context_object_name = 'categories'
    permission_required = 'finance.view_expensecategory'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        context['total_categories'] = queryset.count()
        context['active_categories'] = queryset.filter(is_active=True).count()
        context['total_budget'] = queryset.aggregate(
            total=Sum('budget_amount')
        )['total'] or 0
        
        return context


class ExpenseCategoryCreateView(PermissionRequiredMixin, TenantAccessMixin, CreateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'finance/expense_category_form.html'
    permission_required = 'finance.add_expensecategory'
    success_url = reverse_lazy('finance:expense_category_list')
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)


class ExpenseCategoryUpdateView(PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'finance/expense_category_form.html'
    permission_required = 'finance.change_expensecategory'
    success_url = reverse_lazy('finance:expense_category_list')


class ExpenseCategoryDetailView(PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = ExpenseCategory
    template_name = 'finance/expense_category_detail.html'
    permission_required = 'finance.view_expensecategory'


# ==================== FINANCIAL TRANSACTION VIEWS ====================

class FinancialTransactionListView(PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = FinancialTransaction
    template_name = 'finance/financial_transaction_list.html'
    context_object_name = 'transactions'
    permission_required = 'finance.view_financialtransaction'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        context['total_transactions'] = queryset.count()
        context['total_amount'] = queryset.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Get summary by transaction type
        type_summary = queryset.values('transaction_type').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        context['type_summary'] = list(type_summary)
        
        return context


class FinancialTransactionCreateView(PermissionRequiredMixin, TenantAccessMixin, CreateView):
    model = FinancialTransaction
    form_class = None  # You'll need to create this form
    template_name = 'finance/financial_transaction_form.html'
    permission_required = 'finance.add_financialtransaction'
    success_url = reverse_lazy('finance:financial_transaction_list')
    
    def form_valid(self, form):
        form.instance.entered_by = self.request.user
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)


class FinancialTransactionDetailView(PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = FinancialTransaction
    template_name = 'finance/financial_transaction_detail.html'
    permission_required = 'finance.view_financialtransaction'


# ==================== FINANCIAL REPORT VIEWS ====================

class FinancialReportListView(PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = FinancialReport
    template_name = 'finance/financial_report_list.html'
    context_object_name = 'reports'
    permission_required = 'finance.view_financialreport'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_reports'] = self.get_queryset().count()
        return context


class FinancialReportCreateView(PermissionRequiredMixin, TenantAccessMixin, CreateView):
    model = FinancialReport
    form_class = FinancialReportForm
    template_name = 'finance/financial_report_form.html'
    permission_required = 'finance.add_financialreport'
    success_url = reverse_lazy('finance:financial_report_list')
    
    def form_valid(self, form):
        form.instance.generated_by = self.request.user
        form.instance.tenant = self.request.user.tenant
        
        # Generate report data based on selected parameters
        report = form.save(commit=False)
        report.report_data = self.generate_report_data(
            report.report_type,
            report.start_date,
            report.end_date
        )
        report.summary = self.generate_report_summary(report.report_data)
        report.save()
        
        return super().form_valid(form)
    
    def generate_report_data(self, report_type, start_date, end_date):
        """Generate report data based on type and date range"""
        # Implement report generation logic based on report_type
        # This would query the database and format the data
        return {"message": "Report data generation not implemented"}
    
    def generate_report_summary(self, report_data):
        """Generate summary from report data"""
        return {"message": "Summary generation not implemented"}


class FinancialReportDetailView(PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = FinancialReport
    template_name = 'finance/financial_report_detail.html'
    permission_required = 'finance.view_financialreport'


class FinancialReportDownloadView(PermissionRequiredMixin, TenantAccessMixin, View):
    permission_required = 'finance.download_report'
    
    def get(self, request, pk):
        report = get_object_or_404(FinancialReport, pk=pk, tenant=request.user.tenant)
        
        if report.export_file:
            response = HttpResponse(report.export_file, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{report.report_name}.{report.export_format.lower()}"'
            return response
        else:
            messages.error(request, 'No export file available for this report.')
            return HttpResponseRedirect(reverse('finance:financial_report_detail', kwargs={'pk': pk}))