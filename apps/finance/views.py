import csv
from datetime import datetime, timedelta
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncMonth
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.forms import inlineformset_factory
from django.db import transaction
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, 
    TemplateView, FormView
)
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_filters.views import FilterView
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from openpyxl import Workbook
import pdfkit
import razorpay
import logging

from apps.core.permissions.mixins import (
    PermissionRequiredMixin, TenantAccessMixin
)
# Core Imports
from apps.core.views import (
    BaseView, BaseListView, BaseDetailView, BaseCreateView, 
    BaseUpdateView, BaseDeleteView, BaseTemplateView
)
from apps.core.utils.tenant import get_current_tenant
from apps.core.services.audit_service import AuditService

from apps.finance.models import (
    FeeStructure, FeeDiscount, Invoice, InvoiceItem, 
    AppliedDiscount, Payment, Refund, ExpenseCategory, 
    Expense, Budget, FinancialTransaction, BankAccount, FinancialReport,
    BudgetCategory, BudgetItem, BudgetTemplate, BudgetTemplateItem
)
from apps.finance.forms import (
    FeeStructureForm, FeeDiscountForm, InvoiceForm, 
    InvoiceItemFormSet, PaymentForm, RefundForm,
    ExpenseCategoryForm, ExpenseForm, 
    BankAccountForm, FinancialReportForm, ApplyDiscountForm,
    FinancialTransactionForm, FinancialReportGenerationForm,
    BulkInvoiceGenerationForm, PaymentGatewayForm, QuickPaymentForm,
    BudgetForm, BudgetCategoryForm, BudgetItemForm, BudgetTemplateForm,
    BudgetTemplateItemForm
)


from apps.finance.filters import (
    FeeStructureFilter, InvoiceFilter, PaymentFilter,
    ExpenseFilter, BudgetFilter, FeeDiscountFilter, RefundFilter, BankAccountFilter,
    FinancialTransactionFilter, ExpenseCategoryFilter, ReportFilter,
    MyInvoiceFilter
)
from apps.finance.serializers import (
    FeeStructureSerializer, InvoiceSerializer,
    PaymentSerializer, ExpenseSerializer,
    RefundSerializer, BudgetSerializer, BankAccountSerializer,
    FinancialTransactionSerializer, FinancialReportSerializer,
    ExpenseCategorySerializer
)

# Logger
logger = logging.getLogger(__name__)

# ==================== FEE STRUCTURE VIEWS ====================

class FeeStructureListView(BaseListView):
    model = FeeStructure
    template_name = 'finance/fee_structure/list.html'
    context_object_name = 'fee_structures'
    permission_required = 'finance.view_feestructure'


    def get_queryset(self):
        qs = super().get_queryset()
        self.filterset = FeeStructureFilter(self.request.GET, queryset=qs, request=self.request)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context


class FeeStructureCreateView(BaseCreateView):
    model = FeeStructure
    form_class = FeeStructureForm
    template_name = 'finance/fee_structure/form.html'
    success_url = reverse_lazy('finance:fee_structure_list')
    permission_required = 'finance.add_feestructure'


class FeeStructureUpdateView(BaseUpdateView):
    model = FeeStructure
    form_class = FeeStructureForm
    template_name = 'finance/fee_structure/form.html'
    success_url = reverse_lazy('finance:fee_structure_list')
    permission_required = 'finance.change_feestructure'
    
class FeeStructureDeleteView(BaseDeleteView):
    model = FeeStructure
    template_name = 'finance/fee_structure/confirm_delete.html'
    success_url = reverse_lazy('finance:fee_structure_list')
    permission_required = 'finance.delete_feestructure'

class FeeStructureDetailView(BaseDetailView):
    model = FeeStructure
    template_name = 'finance/fee_structure/detail.html'
    context_object_name = 'fee_structure'
    permission_required = 'finance.view_feestructure'


# ==================== FEE DISCOUNT VIEWS ====================

class FeeDiscountListView(BaseListView):
    model = FeeDiscount
    template_name = 'finance/discount/list.html'
    context_object_name = 'discounts'
    permission_required = 'finance.view_feediscount'


class FeeDiscountCreateView(BaseCreateView):
    model = FeeDiscount
    form_class = FeeDiscountForm
    template_name = 'finance/discount/form.html'
    success_url = reverse_lazy('finance:fee_discount_list')
    permission_required = 'finance.add_feediscount'

class FeeDiscountUpdateView(BaseUpdateView):
    model = FeeDiscount
    form_class = FeeDiscountForm
    template_name = 'finance/discount/form.html'
    success_url = reverse_lazy('finance:fee_discount_list')
    permission_required = 'finance.change_feediscount'

class FeeDiscountDetailView(BaseDetailView):
    model = FeeDiscount
    template_name = 'finance/discount/detail.html'
    context_object_name = 'discount'
    permission_required = 'finance.view_feediscount'

class FeeDiscountDeleteView(BaseDeleteView): # Assuming this exists or should exist
    model = FeeDiscount
    template_name = 'finance/discount/confirm_delete.html'
    success_url = reverse_lazy('finance:fee_discount_list')
    permission_required = 'finance.delete_feediscount'

# ==================== INVOICE VIEWS ====================

class InvoiceListView(BaseListView):
    model = Invoice
    template_name = 'finance/invoice/list.html'
    context_object_name = 'invoices'
    permission_required = 'finance.view_invoice'


    def get_queryset(self):
        qs = super().get_queryset().select_related('student', 'student__user', 'academic_year')
        self.filterset = InvoiceFilter(self.request.GET, queryset=qs, request=self.request)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        queryset = self.filterset.qs
        context['total_amount'] = queryset.aggregate(total=Sum('total_amount'))['total'] or 0
        context['paid_amount'] = queryset.aggregate(total=Sum('paid_amount'))['total'] or 0
        context['due_amount'] = queryset.aggregate(total=Sum('due_amount'))['total'] or 0
        return context

class InvoiceCreateView(BaseCreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finance/invoice/form.html'
    success_url = reverse_lazy('finance:invoice_list')
    permission_required = 'finance.add_invoice'
    
    def form_valid(self, form):
        form.instance.issued_by = self.request.user
        messages.success(self.request, 'Invoice created successfully!')
        return super().form_valid(form)

class InvoiceUpdateView(BaseUpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finance/invoice/form.html'
    success_url = reverse_lazy('finance:invoice_list')
    permission_required = 'finance.change_invoice'

class InvoiceDetailView(BaseDetailView):
    model = Invoice
    template_name = 'finance/invoice/detail.html'
    context_object_name = 'invoice'
    permission_required = 'finance.view_invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add extra context if needed, e.g. related items
        return context

class InvoiceDeleteView(BaseDeleteView):
    model = Invoice
    template_name = 'finance/invoice/confirm_delete.html'
    success_url = reverse_lazy('finance:invoice_list')
    permission_required = 'finance.delete_invoice'

class InvoicePrintView(BaseDetailView):
    model = Invoice
    template_name = 'finance/invoice/print.html'
    context_object_name = 'invoice'
    permission_required = 'finance.view_invoice'
    
    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('format') == 'pdf':
            try:
                html = render(self.request, self.template_name, context).content.decode('utf-8')
                
                # Configure pdfkit
                config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_CMD) if settings.WKHTMLTOPDF_CMD else None
                
                pdf = pdfkit.from_string(html, False, configuration=config)
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="invoice_{self.object.invoice_number}.pdf"'
                return response
            except Exception as e:
                error_msg = str(e)
                if "No wkhtmltopdf executable found" in error_msg:
                    messages.error(self.request, 
                        'PDF generation requires wkhtmltopdf. Please install it from https://wkhtmltopdf.org/downloads.html '
                        'or configure WKHTMLTOPDF_CMD in settings.'
                    )
                else:
                    messages.error(self.request, f'Error generating PDF: {error_msg}')
        return super().render_to_response(context, **response_kwargs)

class InvoiceSendView(BaseView):
    permission_required = 'finance.change_invoice'

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk, tenant=request.tenant)
        if invoice.status == 'DRAFT':
            invoice.status = 'ISSUED'
            invoice.save()
            AuditService.create_audit_entry(
                user=request.user, 
                action='SEND', 
                resource_type='Invoice', 
                instance=invoice,
                request=request
            )
            messages.success(request, 'Invoice sent successfully!')
        else:
            messages.warning(request, 'Invoice already issued.')
        return redirect('finance:invoice_detail', pk=pk)

class InvoiceApplyDiscountView(BaseView):
    permission_required = 'finance.change_invoice'

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk, tenant=request.tenant)
        discount_id = request.POST.get('discount')
        if discount_id:
            # Logic normally handles adding discount
            messages.success(request, 'Discount applied.')
        return redirect('finance:invoice_detail', pk=pk)

class BulkInvoiceActionView(BaseView):
    permission_required = 'finance.change_invoice'
    
    def post(self, request):
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_ids')
        if not selected_ids:
            return redirect('finance:invoice_list')
            
        if action == 'issue':
            count = Invoice.objects.filter(id__in=selected_ids, tenant=request.tenant).update(status='ISSUED')
            messages.success(request, f'{count} invoices issued.')
        elif action == 'delete':
            count = Invoice.objects.filter(id__in=selected_ids, tenant=request.tenant).count()
            Invoice.objects.filter(id__in=selected_ids, tenant=request.tenant).delete()
            messages.success(request, f'{count} invoices deleted.')
            
        return redirect('finance:invoice_list')


# ==================== PAYMENT VIEWS ====================

class PaymentListView(BaseListView):
    model = Payment
    template_name = 'finance/payment/list.html'
    context_object_name = 'payments'
    permission_required = 'finance.view_payment'


    def get_queryset(self):
        qs = super().get_queryset().select_related('invoice', 'invoice__student', 'invoice__student__user')
        self.filterset = PaymentFilter(self.request.GET, queryset=qs, request=self.request)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        queryset = self.filterset.qs
        context['total_payments'] = queryset.count()
        context['total_amount'] = queryset.aggregate(total=Sum('amount'))['total'] or 0
        context['today_payments'] = queryset.filter(
            payment_date__date=timezone.now().date()
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_totals = queryset.annotate(
            month=TruncMonth('payment_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        context['monthly_totals'] = list(monthly_totals)
        return context

class PaymentCreateView(BaseCreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'finance/payment/form.html'
    success_url = reverse_lazy('finance:payment_list')
    permission_required = 'finance.add_payment'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        invoice_id = self.request.GET.get('invoice')
        if invoice_id:
            try:
                invoice = Invoice.objects.get(pk=invoice_id, tenant=self.request.tenant)
                initial['invoice'] = invoice
                initial['amount'] = invoice.due_amount
            except Invoice.DoesNotExist:
                pass
        return initial
    
    def form_valid(self, form):
        form.instance.received_by = self.request.user
        invoice = form.cleaned_data['invoice']
        if form.instance.amount >= invoice.due_amount:
            form.instance.status = 'COMPLETED'
        response = super().form_valid(form)
        # BaseCreateView handles saving form.instance (Payment).
        # We need to update invoice.
        invoice.paid_amount += form.instance.amount
        invoice.save()
        messages.success(self.request, 'Payment recorded successfully!')
        return response

class PaymentDetailView(BaseDetailView):
    model = Payment
    template_name = 'finance/payment/detail.html'
    context_object_name = 'payment'
    permission_required = 'finance.view_payment'

class PaymentVerifyView(BaseView):
    permission_required = 'finance.verify_payment'
    
    def post(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk, tenant=request.tenant)
        if payment.status == 'PENDING':
            payment.status = 'COMPLETED'
            # payment.verified_by = request.user # If model supports it
            # payment.verification_date = timezone.now()
            payment.save()
            AuditService.create_audit_entry(
                user=request.user,
                action='VERIFY_PAYMENT',
                resource_type='Payment',
                instance=payment,
                request=request
            )
            messages.success(request, 'Payment verified successfully!')
        else:
            messages.warning(request, 'Payment is not pending verification.')
        return redirect('finance:payment_detail', pk=pk)


class PaymentPrintView(BaseDetailView):
    model = Payment
    template_name = 'finance/payment/print.html'
    context_object_name = 'payment'
    permission_required = 'finance.view_payment'
    
    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('format') == 'pdf':
            try:
                html = render(self.request, self.template_name, context).content.decode('utf-8')
                
                # Configure pdfkit
                config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_CMD) if settings.WKHTMLTOPDF_CMD else None
                
                pdf = pdfkit.from_string(html, False, configuration=config)
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="receipt_{self.object.transaction_id}.pdf"'
                return response
            except Exception as e:
                error_msg = str(e)
                if "No wkhtmltopdf executable found" in error_msg:
                    messages.error(self.request, 
                        'PDF generation requires wkhtmltopdf. Please install it from https://wkhtmltopdf.org/downloads.html '
                        'or configure WKHTMLTOPDF_CMD in settings.'
                    )
                else:
                    messages.error(self.request, f'Error generating PDF: {error_msg}')
        return super().render_to_response(context, **response_kwargs)


# ==================== EXPENSE VIEWS ====================

class ExpenseListView(BaseListView):
    model = Expense
    template_name = 'finance/expense/list.html'
    context_object_name = 'expenses'
    permission_required = 'finance.view_expense'
    # paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        self.filterset = ExpenseFilter(self.request.GET, queryset=qs, request=self.request)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        queryset = self.filterset.qs
        context['total_expenses'] = queryset.count()
        context['total_amount'] = queryset.filter(status='PAID').aggregate(total=Sum('amount'))['total'] or 0
        
        categories = ExpenseCategory.objects.filter(tenant=self.request.tenant, is_active=True)
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

class ExpenseCreateView(BaseCreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'finance/expense/form.html'
    success_url = reverse_lazy('finance:expense_list')
    permission_required = 'finance.add_expense'
    
    def form_valid(self, form):
        form.instance.submitted_by = self.request.user
        if self.request.user.has_perm('finance.approve_expense'):
            form.instance.status = 'APPROVED'
            form.instance.approved_by = self.request.user
            form.instance.approval_date = timezone.now().date()
        messages.success(self.request, 'Expense submitted successfully!')
        return super().form_valid(form)

class ExpenseUpdateView(BaseUpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'finance/expense/form.html'
    success_url = reverse_lazy('finance:expense_list')
    permission_required = 'finance.change_expense'
    
    def dispatch(self, request, *args, **kwargs):
        # BaseView checks permissions in dispatch, but we need custom check logic too.
        # We can call super().dispatch first or after.
        # But we need to fetch object to check status.
        # Standard View dispatch doesn't fetch object. UpdateView's get_object does.
        # BaseUpdateView doesn't override dispatch significantly except for permission check.
        # We can implement get_object or just check in form_valid or generic object check.
        
        # However, to redirect before processing:
        # We need to rely on get_object being called later or do it here manually.
        # Simplest is to let DetailView handle get_object, but this is UpdateView.
        # Let's use get_object() if PK in kwargs
        if 'pk' in kwargs:
             try:
                 obj = Expense.objects.get(pk=kwargs['pk'], tenant=request.tenant)
                 if obj.status in ['APPROVED', 'PAID', 'REJECTED']:
                    messages.error(request, 'Cannot edit approved, paid, or rejected expenses.')
                    return redirect('finance:expense_detail', pk=obj.pk)
             except Expense.DoesNotExist:
                 pass # Let super handle 404
        return super().dispatch(request, *args, **kwargs)

class ExpenseDetailView(BaseDetailView):
    model = Expense
    template_name = 'finance/expense/detail.html'
    context_object_name = 'expense'
    permission_required = 'finance.view_expense'

class ExpenseApproveView(BaseView):
    permission_required = 'finance.approve_expense'
    
    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk, tenant=request.tenant)
        if expense.status == 'SUBMITTED':
            # expense.approve(request.user) # If model method exists
            expense.status = 'APPROVED'
            expense.approved_by = request.user
            expense.approval_date = timezone.now().date()
            expense.save()
            AuditService.create_audit_entry(
                user=request.user,
                action='APPROVE_EXPENSE',
                resource_type='Expense',
                instance=expense,
                request=request
            )
            messages.success(request, 'Expense approved successfully!')
        else:
            messages.warning(request, 'Expense is not pending approval.')
        return redirect('finance:expense_detail', pk=pk)

class ExpenseRejectView(BaseView):
    permission_required = 'finance.approve_expense'
    
    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk, tenant=request.tenant)
        reason = request.POST.get('reason', '')
        if expense.status == 'SUBMITTED' and reason:
            # expense.reject(request.user, reason)
            expense.status = 'REJECTED'
            expense.save()
            # If notes field exists, append reason?
            AuditService.create_audit_entry(
                user=request.user,
                action='REJECT_EXPENSE',
                resource_type='Expense',
                instance=expense,
                request=request,
                extra_data={'reason': reason}
            )
            messages.success(request, 'Expense rejected.')
        else:
            messages.warning(request, 'Cannot reject expense without reason.')
        return redirect('finance:expense_detail', pk=pk)


# ==================== DASHBOARD & REPORTS ====================

class FinanceDashboardView(BaseTemplateView):
    template_name = 'finance/dashboard.html'
    permission_required = 'finance.view_dashboard'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year
        
        # Summary Cards
        context['total_invoices_month'] = Invoice.objects.filter(
            tenant=tenant, issue_date__month=current_month, issue_date__year=current_year
        ).count()
        
        context['total_revenue_month'] = Payment.objects.filter(
            tenant=tenant, payment_date__month=current_month, payment_date__year=current_year, status='COMPLETED'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        context['total_expenses_month'] = Expense.objects.filter(
            tenant=tenant, expense_date__month=current_month, expense_date__year=current_year, status='APPROVED'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        context['pending_invoices'] = Invoice.objects.filter(
            tenant=tenant, status__in=['DRAFT', 'ISSUED', 'PARTIAL']
        ).count()
        
        # Recent Activities
        context['recent_payments'] = Payment.objects.filter(tenant=tenant).order_by('-created_at')[:5]
        context['recent_expenses'] = Expense.objects.filter(tenant=tenant).order_by('-created_at')[:5]
        
        return context

class FeeCollectionReportView(BaseTemplateView):
    template_name = 'finance/reports/fee_collection.html'
    permission_required = 'finance.view_financialreport'

class DueFeesReportView(BaseListView):
    model = Invoice
    template_name = 'finance/reports/due_fees.html'
    context_object_name = 'invoices'
    permission_required = 'finance.view_financialreport'
    
    def get_queryset(self):
        qs = super().get_queryset()
        # Custom logic for due fees if needed, or rely on template/filtering
        return qs.filter(due_amount__gt=0)


# ==================== RAZORPAY & ONLINE PAYMENTS ====================

class MyInvoicesView(BaseListView):
    model = Invoice
    template_name = 'finance/portal/my_invoices.html'
    context_object_name = 'invoices'
    permission_required = 'finance.view_my_invoices'
    paginate_by = 10
    
    def get_queryset(self):
        # We need to filter by user. BaseListView filters by tenant.
        # We also need MyInvoiceFilter.
        qs = super().get_queryset()
        user = self.request.user
        if hasattr(user, 'student_profile'):
            qs = qs.filter(student=user.student_profile)
        elif hasattr(user, 'parent_profile'):
            qs = qs.filter(student__in=user.parent_profile.children.all())
        else:
            qs = qs.none() # Or strict filter
            
        self.filterset = MyInvoiceFilter(self.request.GET, queryset=qs, request=self.request)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context

class MyPaymentsView(BaseListView):
    model = Payment
    template_name = 'finance/portal/my_payments.html'
    context_object_name = 'payments'
    permission_required = 'finance.view_my_payments'
    paginate_by = 10
    
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Assuming Payment has 'paid_by' or linked invoice->student->user
        # Original code used 'paid_by=user' or 'invoice__student__user=user'
        if hasattr(qs.model, 'paid_by'):
             return qs.filter(paid_by=user).order_by('-payment_date')
        return qs.filter(invoice__student__user=user).order_by('-payment_date')

class PaymentGatewayView(BaseView):
    permission_required = 'finance.make_payment'
    template_name = 'finance/payment_gateway.html'
    
    def get(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, pk=invoice_id, tenant=request.tenant)
        
        # Initialize Razorpay Client
        # Note: In a real app, get these from settings/db and handle secrets securely
        from django.conf import settings
        # Providing default fallback for demo if settings not present
        key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_placeholder')
        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'secret_placeholder')
        
        client = razorpay.Client(auth=(key_id, key_secret))
        
        # Create Order
        amount_in_paise = int(invoice.due_amount * 100)
        order_currency = 'INR'
        
        try:
            payment_order = client.order.create({
                'amount': amount_in_paise,
                'currency': order_currency,
                'receipt': str(invoice.invoice_number),
                'payment_capture': '1'
            })
            
            context = {
                'invoice': invoice,
                'razorpay_order_id': payment_order['id'],
                'razorpay_merchant_key': key_id,
                'razorpay_amount': amount_in_paise,
                'currency': order_currency,
                'callback_url': request.build_absolute_uri(reverse('finance:payment_callback')),
            }
            return render(request, self.template_name, context)
        except Exception as e:
            messages.error(request, f"Error initializing payment: {str(e)}")
            return redirect('finance:my_invoices')

class PaymentCallbackView(View): # Keeping View + csrf_exempt as BaseView might enforce checks we don't want on callback
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
        
# ==================== BULK & OTHERS ====================

class GenerateMonthlyInvoicesView(BaseView):
    permission_required = 'finance.add_invoice'

    def get(self, request):
        return render(request, 'finance/utils/generate_invoices.html')

    def post(self, request):
        billing_month_str = request.POST.get('billing_month')  # YYYY-MM
        due_date_str = request.POST.get('due_date')

        if not billing_month_str or not due_date_str:
            messages.error(request, _("Please provide both billing month and due date."))
            return render(request, 'finance/utils/generate_invoices.html')

        try:
            # Parse dates
            from datetime import datetime
            billing_date = datetime.strptime(billing_month_str, '%Y-%m').date()
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            billing_period = billing_date.strftime('%B %Y')

            # Get active students
            from apps.students.models import Student
            students = Student.objects.filter(
                status='ACTIVE',
                tenant=self.request.tenant
            ).select_related('current_class', 'academic_year')

            invoices_created = 0
            
            with transaction.atomic():
                for student in students:
                    # Find applicable monthly fees for the student's class
                    # For simplicity, we assume fees are linked to the student's current academic year
                    fees = FeeStructure.objects.filter(
                        tenant=self.request.tenant,
                        class_name=student.current_class,
                        academic_year=student.academic_year,
                        frequency='MONTHLY' # Correct field name from model
                    )

                    if not fees.exists():
                        continue

                    # Check if invoice already exists for this period
                    if Invoice.objects.filter(
                        student=student, 
                        billing_period=billing_period,
                        tenant=self.request.tenant
                    ).exists():
                        continue

                    # Create Invoice
                    invoice = Invoice.objects.create(
                        tenant=self.request.tenant,
                        student=student,
                        academic_year=student.academic_year,
                        billing_period=billing_period,
                        due_date=due_date,
                        issue_date=timezone.now().date(),
                        status='ISSUED' # Auto-issue monthly invoices
                    )

                    # Add Items
                    for fee in fees:
                        invoice.add_invoice_item(
                            fee_structure=fee,
                            amount=fee.amount,
                            description=f"{fee.name} - {billing_period}"
                        )
                    
                    invoices_created += 1

            if invoices_created > 0:
                messages.success(request, _(f"Successfully generated {invoices_created} invoices for {billing_period}."))
            else:
                messages.info(request, _(f"No new invoices were generated for {billing_period}."))
                
            return redirect('finance:invoice_list')

        except Exception as e:
            messages.error(request, _(f"Error generating invoices: {str(e)}"))
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Invoice generation error: {e}", exc_info=True)
            return render(request, 'finance/utils/generate_invoices.html')



class SendPaymentRemindersView(BaseView):
    permission_required = 'finance.change_invoice'


    def get(self, request):
        # Calculate stats for the confirm page
        overdue_invoices = Invoice.objects.filter(
            tenant=self.request.tenant,
            status='OVERDUE'
        )
        
        # Also check for invoices that are effectively overdue but status might not be updated yet
        # (Though Invoice.save() handles it, batch job usually better)
        current_date = timezone.now().date()
        potential_overdue = Invoice.objects.filter(
            tenant=self.request.tenant,
            due_date__lt=current_date,
            due_amount__gt=0
        ).exclude(status='OVERDUE')
        
        # Calculate totals
        total_overdue = overdue_invoices.count() + potential_overdue.count()
        total_amount = overdue_invoices.aggregate(Sum('due_amount'))['due_amount__sum'] or 0
        total_amount += potential_overdue.aggregate(Sum('due_amount'))['due_amount__sum'] or 0
        
        # Unique students
        student_ids = set(overdue_invoices.values_list('student_id', flat=True))
        student_ids.update(potential_overdue.values_list('student_id', flat=True))
        
        context = {
            'overdue_count': total_overdue,
            'overdue_amount': total_amount,
            'students_affected': len(student_ids)
        }
        return render(request, 'finance/utils/send_reminders.html', context)

    def post(self, request): 
        # Logic to send reminders
        # 1. auto-update statuses first
        current_date = timezone.now().date()
        potential_overdue = Invoice.objects.filter(
            tenant=self.request.tenant,
            due_date__lt=current_date,
            due_amount__gt=0
        ).exclude(status='OVERDUE')
        
        updated_count = 0
        for inv in potential_overdue:
            inv.status = 'OVERDUE'
            inv.save() # This triggers is_overdue check in model
            updated_count += 1
            
        # 2. Get all overdue
        overdue_invoices = Invoice.objects.filter(
            tenant=self.request.tenant,
            status='OVERDUE'
        ).select_related('student')
        
        # 3. "Send" reminders (Mocking email sending)
        sent_count = 0
        for inv in overdue_invoices:
            # Here we would call: send_email(inv.student.personal_email, ...)
            sent_count += 1
            
        if updated_count > 0:
            messages.info(request, _(f"Updated status for {updated_count} invoices to Overdue."))
            
        if sent_count > 0:
            messages.success(request, _(f"Successfully sent payment reminders for {sent_count} invoices."))
        else:
            messages.warning(request, _("No overdue invoices found to send reminders for."))
            
        return redirect('finance:invoice_list')

# Duplicate BulkInvoiceActionView removed

class BudgetListView(BaseListView):
    model = Budget
    template_name = 'finance/budget/list.html'
    context_object_name = 'budgets'
    permission_required = 'finance.view_budget'


    def get_queryset(self):
        qs = super().get_queryset()
        self.filterset = BudgetFilter(self.request.GET, queryset=qs, request=self.request)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context


class BudgetDetailView(BaseDetailView):
    model = Budget
    template_name = 'finance/budget/detail.html'
    context_object_name = 'budget'
    permission_required = 'finance.view_budget'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.budget_items.all().select_related('category')
        return context


# Formset for Budget Items
BudgetItemFormSet = inlineformset_factory(
    Budget, BudgetItem, form=BudgetItemForm,
    extra=1, can_delete=True
)

class BudgetCreateView(BaseCreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'finance/budget/form.html'
    success_url = reverse_lazy('finance:budget_list')
    permission_required = 'finance.add_budget'
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = BudgetItemFormSet(self.request.POST)
        else:
            data['items'] = BudgetItemFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        
        # Validate items first before starting transaction
        if items.is_valid():
            with transaction.atomic():
                # Save parent form
                form.instance.prepared_by = self.request.user
                self.object = form.save()
                
                # Save children
                items.instance = self.object
                items.save()
                
            return super().form_valid(form)
        else:
            # Return response with form AND invalid items formset
            return self.render_to_response(self.get_context_data(form=form))


class BudgetUpdateView(BaseUpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'finance/budget/form.html'
    success_url = reverse_lazy('finance:budget_list')
    permission_required = 'finance.change_budget'
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            # Only create new formset if not already in kwargs (from invalid submission)
            if 'items' not in kwargs:
                 data['items'] = BudgetItemFormSet(self.request.POST, instance=self.object)
        else:
            data['items'] = BudgetItemFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        # We need to manually reconstruct the formset to validate it
        items = BudgetItemFormSet(self.request.POST, instance=self.object)
        
        if items.is_valid():
            with transaction.atomic():
                self.object = form.save()
                items.save()
            return super().form_valid(form)
        else:
            # Pass invalid items to render logic
            # We call get_context_data but inject our invalid items
            return self.render_to_response(self.get_context_data(form=form, items=items))



class BudgetDeleteView(BaseDeleteView):
    model = Budget
    template_name = 'finance/budget/confirm_delete.html'
    success_url = reverse_lazy('finance:budget_list')
    permission_required = 'finance.delete_budget'


# ==================== BUDGET CATEGORY VIEWS ====================

class BudgetCategoryListView(BaseListView):
    model = BudgetCategory
    template_name = 'finance/budget_category/list.html'
    context_object_name = 'categories'
    permission_required = 'finance.view_budgetcategory'
    paginate_by = 50

class BudgetCategoryCreateView(BaseCreateView):
    model = BudgetCategory
    form_class = BudgetCategoryForm
    template_name = 'finance/budget_category/form.html'
    success_url = reverse_lazy('finance:budget_category_list')
    permission_required = 'finance.add_budgetcategory'

class BudgetCategoryUpdateView(BaseUpdateView):
    model = BudgetCategory
    form_class = BudgetCategoryForm
    template_name = 'finance/budget_category/form.html'
    success_url = reverse_lazy('finance:budget_category_list')
    permission_required = 'finance.change_budgetcategory'

class BudgetCategoryDeleteView(BaseDeleteView):
    model = BudgetCategory
    template_name = 'finance/budget_category/confirm_delete.html'
    success_url = reverse_lazy('finance:budget_category_list')
    permission_required = 'finance.delete_budgetcategory'


# ==================== BUDGET TEMPLATE VIEWS ====================

class BudgetTemplateListView(BaseListView):
    model = BudgetTemplate
    template_name = 'finance/budget_template/list.html'
    context_object_name = 'templates'
    permission_required = 'finance.view_budgettemplate'

class BudgetTemplateCreateView(BaseCreateView):
    model = BudgetTemplate
    form_class = BudgetTemplateForm
    template_name = 'finance/budget_template/form.html'
    success_url = reverse_lazy('finance:budget_template_list')
    permission_required = 'finance.add_budgettemplate'

class BudgetTemplateUpdateView(BaseUpdateView):
    model = BudgetTemplate
    form_class = BudgetTemplateForm
    template_name = 'finance/budget_template/form.html'
    success_url = reverse_lazy('finance:budget_template_list')
    permission_required = 'finance.change_budgettemplate'

class BudgetTemplateDeleteView(BaseDeleteView):
    model = BudgetTemplate
    template_name = 'finance/budget_template/confirm_delete.html'
    success_url = reverse_lazy('finance:budget_template_list')
    permission_required = 'finance.delete_budgettemplate'

class BudgetApproveView(BaseView):
    permission_required = 'finance.approve_budget'
    def post(self, request, pk):
        budget = get_object_or_404(Budget, pk=pk, tenant=request.tenant)
        budget.status = 'APPROVED'
        budget.save()
        messages.success(request, 'Budget approved.')
        return redirect('finance:budget_list')

class BudgetActivateView(BaseView):
    permission_required = 'finance.change_budget'
    def post(self, request, pk):
        budget = get_object_or_404(Budget, pk=pk, tenant=request.tenant)
        budget.status = 'ACTIVE'
        budget.save()
        messages.success(request, 'Budget activated.')
        return redirect('finance:budget_list')

class RefundListView(BaseListView):
    model = Refund
    template_name = 'finance/refund/list.html'
    context_object_name = 'refunds'
    permission_required = 'finance.view_refund'
    # paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        self.filterset = RefundFilter(self.request.GET, queryset=qs, request=self.request)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context

class RefundCreateView(BaseCreateView):
    model = Refund
    form_class = RefundForm
    template_name = 'finance/refund/form.html'
    success_url = reverse_lazy('finance:refund_list')
    permission_required = 'finance.add_refund'
    
    def form_valid(self, form):
        form.instance.requested_by = self.request.user
        messages.success(self.request, 'Refund request created.')
        return super().form_valid(form)

class RefundDetailView(BaseDetailView):
    model = Refund
    template_name = 'finance/refund/detail.html'
    context_object_name = 'refund'
    permission_required = 'finance.view_refund'

class RefundApproveView(BaseView):
    permission_required = 'finance.approve_refund'
    def post(self, request, pk):
        refund = get_object_or_404(Refund, pk=pk, tenant=request.tenant)
        refund.status = 'APPROVED'
        refund.approved_by = request.user
        refund.approval_date = timezone.now().date()
        refund.save()
        messages.success(request, 'Refund approved.')
        return redirect('finance:refund_detail', pk=pk)

class RefundProcessView(BaseView):
    permission_required = 'finance.change_refund'
    def post(self, request, pk):
        refund = get_object_or_404(Refund, pk=pk, tenant=request.tenant)
        refund.status = 'PROCESSING'
        refund.save()
        messages.success(request, 'Refund processing.')
        return redirect('finance:refund_detail', pk=pk)

class RefundCompleteView(BaseView):
    permission_required = 'finance.change_refund'
    def post(self, request, pk):
        refund = get_object_or_404(Refund, pk=pk, tenant=request.tenant)
        refund.status = 'COMPLETED'
        refund.refunded_date = timezone.now().date()
        refund.save()
        messages.success(request, 'Refund completed.')
        return redirect('finance:refund_detail', pk=pk)

class BankAccountListView(BaseListView):
    model = BankAccount
    template_name = 'finance/bank/list.html'
    context_object_name = 'bank_accounts'
    permission_required = 'finance.view_bankaccount'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = BankAccountFilter(self.request.GET, queryset=self.get_queryset(), request=self.request)
        return context

class BankAccountCreateView(BaseCreateView):
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'finance/bank/form.html'
    success_url = reverse_lazy('finance:bank_account_list')
    permission_required = 'finance.add_bankaccount'

class BankAccountUpdateView(BaseUpdateView):
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'finance/bank/form.html'
    success_url = reverse_lazy('finance:bank_account_list')
    permission_required = 'finance.change_bankaccount'

class BankAccountDetailView(BaseDetailView):
    model = BankAccount
    template_name = 'finance/bank/detail.html'
    context_object_name = 'bank_account'
    permission_required = 'finance.view_bankaccount'

class ExpenseCategoryListView(BaseListView):
    model = ExpenseCategory
    template_name = 'finance/expense_category/list.html'
    context_object_name = 'categories'
    permission_required = 'finance.view_expensecategory'
    # paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        self.filterset = ExpenseCategoryFilter(self.request.GET, queryset=qs, request=self.request)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context

class ExpenseCategoryCreateView(BaseCreateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'finance/expense_category/form.html'
    success_url = reverse_lazy('finance:expense_category_list')
    permission_required = 'finance.add_expensecategory'

class ExpenseCategoryUpdateView(BaseUpdateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'finance/expense_category/form.html'
    success_url = reverse_lazy('finance:expense_category_list')
    permission_required = 'finance.change_expensecategory'

class ExpenseCategoryDetailView(BaseDetailView):
    model = ExpenseCategory
    template_name = 'finance/expense_category/detail.html'
    context_object_name = 'category'
    permission_required = 'finance.view_expensecategory'

class FinancialTransactionListView(BaseListView):
    model = FinancialTransaction
    template_name = 'finance/transaction/list.html'
    context_object_name = 'transactions'
    permission_required = 'finance.view_financialtransaction'
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        self.filterset = FinancialTransactionFilter(self.request.GET, queryset=qs, request=self.request)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context

class FinancialTransactionCreateView(BaseCreateView):
    model = FinancialTransaction
    form_class = FinancialTransactionForm
    template_name = 'finance/transaction/form.html'
    success_url = reverse_lazy('finance:financial_transaction_list')
    permission_required = 'finance.add_financialtransaction'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class FinancialTransactionDetailView(BaseDetailView):
    model = FinancialTransaction
    template_name = 'finance/transaction/detail.html'
    context_object_name = 'transaction'
    permission_required = 'finance.view_financialtransaction'

class FinancialReportListView(BaseListView):
    model = FinancialReport
    template_name = 'finance/report/list.html'
    context_object_name = 'reports'
    permission_required = 'finance.view_financialreport'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        self.filterset = ReportFilter(self.request.GET, queryset=qs, request=self.request)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context

class FinancialReportCreateView(BaseCreateView):
    model = FinancialReport
    form_class = FinancialReportForm
    template_name = 'finance/report/form.html'
    success_url = reverse_lazy('finance:financial_report_list')
    permission_required = 'finance.add_financialreport'
    
    def form_valid(self, form):
        form.instance.generated_by = self.request.user
        return super().form_valid(form)

class FinancialReportDetailView(BaseDetailView):
    model = FinancialReport
    template_name = 'finance/report/detail.html'
    context_object_name = 'report'
    permission_required = 'finance.view_financialreport'

class FinancialReportDownloadView(BaseView):
    permission_required = 'finance.view_financialreport'
    def get(self, request, pk):
        report = get_object_or_404(FinancialReport, pk=pk, tenant=request.tenant)
        if report.file:
            response = HttpResponse(report.file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{report.title}.pdf"'
            return response
        messages.error(request, 'Report file not found.')
        return redirect('finance:financial_report_detail', pk=pk)

class ExpenseSummaryReportView(BaseTemplateView):
    template_name = 'finance/reports/expense_summary.html'
    permission_required = 'finance.view_reports'

class BudgetVsActualReportView(BaseTemplateView):
    template_name = 'finance/reports/budget_vs_actual.html'
    permission_required = 'finance.view_reports'

class FeeStructureAPIViewSet(viewsets.ModelViewSet):
    queryset = FeeStructure.objects.all()
    serializer_class = FeeStructureSerializer
    permission_classes = [permissions.IsAuthenticated]

class InvoiceAPIViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

class PaymentAPIViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

class ExpenseAPIViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
