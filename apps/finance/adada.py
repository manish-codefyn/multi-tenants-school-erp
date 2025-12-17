from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
import json

from .models import (
    FeeStructure, FeeDiscount, Invoice, InvoiceItem,
    Payment, Refund, ExpenseCategory, Expense, 
    Budget, BankAccount, FinancialReport, AppliedDiscount,FinancialTransaction
)

from apps.core.forms import BaseForm,TenantAwareModelForm

class FeeStructureForm(TenantAwareModelForm):
    class Meta:
        model = FeeStructure
        fields = [
            'name', 'academic_year', 'class_name', 'fee_type',
            'frequency', 'amount', 'due_day', 'late_fee_applicable',
            'late_fee_amount', 'late_fee_after_days', 'discount_allowed',
            'max_discount_percentage', 'is_active'
        ]
        widgets = {
            'due_day': forms.NumberInput(attrs={'min': 1, 'max': 31}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Check for duplicate fee structure
        tenant = self.tenant if self.tenant else None
        if self.instance.pk is None and tenant:  # New instance
            if FeeStructure.objects.filter(
                academic_year=cleaned_data.get('academic_year'),
                class_name=cleaned_data.get('class_name'),
                fee_type=cleaned_data.get('fee_type'),
                frequency=cleaned_data.get('frequency'),
                tenant=tenant
            ).exists():
                raise ValidationError(
                    "A fee structure with these details already exists."
                )
        
        return cleaned_data


class FeeDiscountForm(TenantAwareModelForm):
    class Meta:
        model = FeeDiscount
        fields = [
            'name', 'code', 'description', 'discount_type', 'value',
            'applicable_to', 'applicable_classes', 'applicable_categories',
            'min_percentage_required', 'max_discount_amount',
            'max_usage_per_student', 'total_usage_limit',
            'valid_from', 'valid_until', 'required_documents', 'is_active'
        ]
        widgets = {
            'valid_from': forms.DateInput(attrs={'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
            'applicable_categories': forms.Textarea(attrs={'rows': 3}),
            'required_documents': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.user.is_superuser:
            self.fields['applicable_classes'].queryset = self.fields['applicable_classes'].queryset.filter(
                tenant=self.user.tenant
            )
    
    def clean_applicable_categories(self):
        data = self.cleaned_data.get('applicable_categories', '[]')
        try:
            if data:
                json.loads(data)
        except json.JSONDecodeError:
            raise ValidationError("Please enter valid JSON format for categories")
        return data
    
    def clean_required_documents(self):
        data = self.cleaned_data.get('required_documents', '[]')
        try:
            if data:
                json.loads(data)
        except json.JSONDecodeError:
            raise ValidationError("Please enter valid JSON format for required documents")
        return data
    
    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_until = cleaned_data.get('valid_until')
        discount_type = cleaned_data.get('discount_type')
        value = cleaned_data.get('value')
        
        if valid_from and valid_until:
            if valid_until < valid_from:
                raise ValidationError({
                    'valid_until': 'Valid until date must be after valid from date.'
                })
        
        if discount_type == 'PERCENTAGE' and value:
            if value > 100:
                raise ValidationError({
                    'value': 'Percentage discount cannot exceed 100%.'
                })
        
        return cleaned_data


class InvoiceForm(TenantAwareModelForm):
    class Meta:
        model = Invoice
        fields = [
            'student', 'academic_year', 'billing_period',
            'issue_date', 'due_date', 'payment_terms', 'notes'
        ]
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_terms': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter students by current user's tenant
        if self.user and not self.user.is_superuser:
            self.fields['student'].queryset = self.fields['student'].queryset.filter(
                tenant=self.user.tenant,
                is_active=True
            )
            self.fields['academic_year'].queryset = self.fields['academic_year'].queryset.filter(
                tenant=self.user.tenant
            )
    
    def clean(self):
        cleaned_data = super().clean()
        due_date = cleaned_data.get('due_date')
        issue_date = cleaned_data.get('issue_date')
        
        if due_date and issue_date:
            if due_date < issue_date:
                raise ValidationError({
                    'due_date': 'Due date cannot be before issue date.'
                })
        
        return cleaned_data


class InvoiceItemForm(TenantAwareModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['fee_structure', 'amount', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter fee structures by tenant
        if hasattr(self, 'instance') and hasattr(self.instance, 'invoice'):
            self.fields['fee_structure'].queryset = FeeStructure.objects.filter(
                tenant=self.instance.invoice.tenant,
                is_active=True
            )


InvoiceItemFormSet = forms.inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=1,
    can_delete=True
)


class PaymentForm(TenantAwareModelForm):
    class Meta:
        model = Payment
        fields = [
            'invoice', 'amount', 'payment_date', 'payment_method',
            'reference_number', 'bank_name', 'branch_name',
            'cheque_dd_number', 'cheque_dd_date', 'transaction_id',
            'gateway_name', 'notes'
        ]
        widgets = {
            'payment_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'cheque_dd_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.user.is_superuser:
            # Only show invoices from user's tenant
            self.fields['invoice'].queryset = self.fields['invoice'].queryset.filter(
                tenant=self.user.tenant,
                due_amount__gt=0
            ).select_related('student')
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        invoice = self.cleaned_data.get('invoice')
        
        if invoice and amount:
            if amount <= 0:
                raise ValidationError('Payment amount must be greater than 0.')
            
            if amount > invoice.due_amount:
                raise ValidationError(
                    f'Payment amount cannot exceed due amount (₹{invoice.due_amount}).'
                )
        
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        cheque_dd_date = cleaned_data.get('cheque_dd_date')
        
        if payment_method in ['CHEQUE', 'DD'] and not cheque_dd_date:
            raise ValidationError({
                'cheque_dd_date': 'Cheque/DD date is required for this payment method.'
            })
        
        return cleaned_data


class RefundForm(TenantAwareModelForm):
    class Meta:
        model = Refund
        fields = [
            'payment', 'amount', 'reason', 'refund_bank_account',
            'refund_bank_name', 'refund_ifsc_code'
        ]
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.user.is_superuser:
            # Only show payments from user's tenant
            self.fields['payment'].queryset = self.fields['payment'].queryset.filter(
                tenant=self.user.tenant,
                status='COMPLETED'
            ).select_related('invoice')
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        payment = self.cleaned_data.get('payment')
        
        if payment and amount:
            if amount <= 0:
                raise ValidationError('Refund amount must be greater than 0.')
            
            if amount > payment.amount:
                raise ValidationError(
                    f'Refund amount cannot exceed payment amount (₹{payment.amount}).'
                )
            
            # Check if refund amount exceeds available amount (considering previous refunds)
            total_refunded = Refund.objects.filter(
                payment=payment,
                status__in=['APPROVED', 'PROCESSED', 'COMPLETED']
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            available_for_refund = payment.amount - total_refunded
            
            if amount > available_for_refund:
                raise ValidationError(
                    f'Maximum refund available is ₹{available_for_refund}.'
                )
        
        return amount


class ExpenseCategoryForm(TenantAwareModelForm):
    class Meta:
        model = ExpenseCategory
        fields = [
            'name', 'code', 'category_type', 'description',
            'parent_category', 'budget_amount', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.user.is_superuser:
            self.fields['parent_category'].queryset = self.fields['parent_category'].queryset.filter(
                tenant=self.user.tenant
            )
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code and self.user and ExpenseCategory.objects.filter(
            code=code,
            tenant=self.user.tenant
        ).exclude(pk=self.instance.pk).exists():
            raise ValidationError('An expense category with this code already exists.')
        return code


class ExpenseForm(TenantAwareModelForm):
    class Meta:
        model = Expense
        fields = [
            'category', 'title', 'description', 'amount',
            'expense_date', 'vendor_name', 'vendor_contact',
            'bill_number', 'bill_date', 'payment_method',
            'reference_number', 'supporting_documents'
        ]
        widgets = {
            'expense_date': forms.DateInput(attrs={'type': 'date'}),
            'bill_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'supporting_documents': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.user.is_superuser:
            self.fields['category'].queryset = self.fields['category'].queryset.filter(
                tenant=self.user.tenant,
                is_active=True
            )
    
    def clean_supporting_documents(self):
        data = self.cleaned_data.get('supporting_documents', '[]')
        try:
            if data:
                json.loads(data)
        except json.JSONDecodeError:
            raise ValidationError("Please enter valid JSON format for supporting documents")
        return data
    
    def clean(self):
        cleaned_data = super().clean()
        bill_date = cleaned_data.get('bill_date')
        expense_date = cleaned_data.get('expense_date')
        
        if bill_date and expense_date:
            if bill_date > expense_date:
                raise ValidationError({
                    'bill_date': 'Bill date cannot be after expense date.'
                })
        
        return cleaned_data


class BudgetForm(TenantAwareModelForm):
    class Meta:
        model = Budget
        fields = [
            'name', 'academic_year', 'total_amount',
            'start_date', 'end_date', 'budget_items', 'notes'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'budget_items': forms.Textarea(attrs={'rows': 10}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.user.is_superuser:
            self.fields['academic_year'].queryset = self.fields['academic_year'].queryset.filter(
                tenant=self.user.tenant
            )
    
    def clean_budget_items(self):
        data = self.cleaned_data.get('budget_items', '[]')
        try:
            if data:
                items = json.loads(data)
                if not isinstance(items, list):
                    raise ValidationError("Budget items must be a JSON array")
                
                # Validate each item has required fields
                for item in items:
                    if not all(key in item for key in ['category', 'amount']):
                        raise ValidationError("Each budget item must have 'category' and 'amount' fields")
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format: {str(e)}")
        return data
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        academic_year = cleaned_data.get('academic_year')
        
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError({
                    'end_date': 'End date must be after start date.'
                })
            
            if academic_year:
                if start_date < academic_year.start_date:
                    raise ValidationError({
                        'start_date': f'Start date cannot be before academic year start date ({academic_year.start_date}).'
                    })
                
                if end_date > academic_year.end_date:
                    raise ValidationError({
                        'end_date': f'End date cannot be after academic year end date ({academic_year.end_date}).'
                    })
        
        return cleaned_data


class BankAccountForm(TenantAwareModelForm):
    class Meta:
        model = BankAccount
        fields = [
            'account_name', 'account_number', 'bank_name',
            'branch_name', 'ifsc_code', 'account_type',
            'current_balance', 'as_of_date', 'bank_contact',
            'bank_address', 'authorized_signatories', 'is_active'
        ]
        widgets = {
            'as_of_date': forms.DateInput(attrs={'type': 'date'}),
            'bank_address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean_account_number(self):
        account_number = self.cleaned_data.get('account_number')
        tenant = self.tenant if hasattr(self, 'tenant') and self.tenant else (self.instance.tenant if self.instance.pk else None)
        if account_number and tenant and BankAccount.objects.filter(
            account_number=account_number,
            tenant=tenant
        ).exclude(pk=self.instance.pk).exists():
            raise ValidationError('A bank account with this account number already exists.')
        return account_number
    
    def clean_ifsc_code(self):
        ifsc_code = self.cleaned_data.get('ifsc_code')
        if ifsc_code and len(ifsc_code) != 11:
            raise ValidationError('IFSC code must be 11 characters long.')
        return ifsc_code.upper() if ifsc_code else ifsc_code


class FinancialReportForm(TenantAwareModelForm):
    class Meta:
        model = FinancialReport
        fields = [
            'report_type', 'report_name', 'period',
            'start_date', 'end_date'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        period = cleaned_data.get('period')
        
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError({
                    'end_date': 'End date must be after start date.'
                })
            
            if period == 'DAILY' and start_date != end_date:
                raise ValidationError({
                    'end_date': 'For daily reports, start and end dates must be the same.'
                })
            
            # Check date range limits
            date_diff = (end_date - start_date).days
            if period == 'WEEKLY' and date_diff > 7:
                raise ValidationError({
                    'end_date': 'For weekly reports, date range cannot exceed 7 days.'
                })
            elif period == 'MONTHLY' and date_diff > 31:
                raise ValidationError({
                    'end_date': 'For monthly reports, date range cannot exceed 31 days.'
                })
            elif period == 'QUARTERLY' and date_diff > 92:
                raise ValidationError({
                    'end_date': 'For quarterly reports, date range cannot exceed 92 days.'
                })
            elif period == 'YEARLY' and date_diff > 365:
                raise ValidationError({
                    'end_date': 'For yearly reports, date range cannot exceed 365 days.'
                })
        
        return cleaned_data


class ApplyDiscountForm(forms.Form):
    discount = forms.ModelChoiceField(
        queryset=FeeDiscount.objects.none(),
        label="Select Discount"
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label="Reason (Optional)"
    )
    
    def __init__(self, *args, **kwargs):
        self.invoice = kwargs.pop('invoice', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.invoice and self.user:
            # Get eligible discounts for this invoice
            eligible_discounts = []
            all_discounts = FeeDiscount.objects.filter(
                tenant=self.user.tenant,
                is_active=True,
                valid_from__lte=timezone.now().date(),
                valid_until__gte=timezone.now().date()
            )
            
            for discount in all_discounts:
                is_eligible, _ = discount.is_eligible(self.invoice.student, self.invoice.subtotal)
                if is_eligible:
                    eligible_discounts.append(discount.id)
            
            self.fields['discount'].queryset = FeeDiscount.objects.filter(
                id__in=eligible_discounts
            )


class BulkInvoiceGenerationForm(forms.Form):
    month = forms.ChoiceField(
        choices=[
            (1, 'January'), (2, 'February'), (3, 'March'),
            (4, 'April'), (5, 'May'), (6, 'June'),
            (7, 'July'), (8, 'August'), (9, 'September'),
            (10, 'October'), (11, 'November'), (12, 'December')
        ],
        initial=timezone.now().month
    )
    year = forms.IntegerField(
        min_value=2020,
        max_value=2100,
        initial=timezone.now().year
    )
    class_id = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="Specific Class (Optional)",
        help_text="Leave empty to generate for all classes"
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.user.is_superuser:
            from apps.academics.models import SchoolClass
            self.fields['class_id'].queryset = SchoolClass.objects.filter(
                tenant=self.user.tenant
            )


class PaymentGatewayForm(forms.Form):
    PAYMENT_METHODS = [
        ('UPI', 'UPI'),
        ('CARD', 'Credit/Debit Card'),
        ('NET_BANKING', 'Net Banking'),
        ('WALLET', 'Wallet'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        widget=forms.RadioSelect
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01
    )
    email = forms.EmailField(
        required=False,
        help_text="Receipt will be sent to this email"
    )
    
    def __init__(self, *args, **kwargs):
        self.invoice = kwargs.pop('invoice', None)
        super().__init__(*args, **kwargs)
        
        if self.invoice:
            self.fields['amount'].initial = self.invoice.due_amount
            self.fields['amount'].max_value = self.invoice.due_amount
            self.fields['email'].initial = self.invoice.student.user.email


# Quick payment form for dashboard
class QuickPaymentForm(TenantAwareModelForm):
    class Meta:
        model = Payment
        fields = ['invoice', 'amount', 'payment_method', 'reference_number']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.user.is_superuser:
            self.fields['invoice'].queryset = self.fields['invoice'].queryset.filter(
                tenant=self.user.tenant,
                due_amount__gt=0
            ).select_related('student')
        
        # Make fields more compact for quick entry
        self.fields['invoice'].widget.attrs.update({'class': 'form-control-sm'})
        self.fields['amount'].widget.attrs.update({'class': 'form-control-sm'})
        self.fields['payment_method'].widget.attrs.update({'class': 'form-control-sm'})
        self.fields['reference_number'].widget.attrs.update({
            'class': 'form-control-sm',
            'placeholder': 'Optional'
        })


# Add these forms to your existing forms.py

class FinancialTransactionForm(TenantAwareModelForm):
    class Meta:
        model = FinancialTransaction
        fields = [
            'transaction_type', 'transaction_date', 'amount',
            'debit_account', 'credit_account', 'description',
            'reference', 'related_invoice', 'related_expense'
        ]
        widgets = {
            'transaction_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class FinancialReportGenerationForm(forms.Form):
    report_type = forms.ChoiceField(
        choices=FinancialReport.REPORT_TYPE_CHOICES,
        label="Report Type"
    )
    period = forms.ChoiceField(
        choices=FinancialReport.PERIOD_CHOICES,
        label="Report Period"
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Start Date"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="End Date"
    )
    export_format = forms.ChoiceField(
        choices=[
            ('PDF', 'PDF'),
            ('EXCEL', 'Excel'),
            ('CSV', 'CSV'),
        ],
        required=False,
        label="Export Format (Optional)"
    )