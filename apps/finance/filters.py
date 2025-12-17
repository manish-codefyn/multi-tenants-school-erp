import django_filters
from django import forms
from django.db.models import Q

# Import models at the top to avoid circular dependencies
from .models import (
    FeeStructure, FeeDiscount, Invoice, Payment, Refund,
    ExpenseCategory, Expense, Budget, BankAccount, 
    FinancialTransaction, FinancialReport  # Added FinancialReport here
)


class FeeStructureFilter(django_filters.FilterSet):
    class_name = django_filters.CharFilter(
        field_name='class_name__name',
        lookup_expr='icontains',
        label='Class Name'
    )
    academic_year = django_filters.CharFilter(
        field_name='academic_year__name',
        lookup_expr='icontains',
        label='Academic Year'
    )
    fee_type = django_filters.ChoiceFilter(
        choices=FeeStructure.FEE_TYPE_CHOICES,
        empty_label='All Fee Types'
    )
    frequency = django_filters.ChoiceFilter(
        choices=FeeStructure.FEE_FREQUENCY_CHOICES,
        empty_label='All Frequencies'
    )
    is_active = django_filters.BooleanFilter(
        widget=forms.CheckboxInput(),
        label='Active Only'
    )
    
    class Meta:
        model = FeeStructure
        fields = ['academic_year', 'class_name', 'fee_type', 'frequency', 'is_active']


class FeeDiscountFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Discount Name'
    )
    code = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Discount Code'
    )
    discount_type = django_filters.ChoiceFilter(
        choices=FeeDiscount.DISCOUNT_TYPE_CHOICES,
        empty_label='All Types'
    )
    applicable_to = django_filters.ChoiceFilter(
        choices=FeeDiscount.APPLICABLE_TO_CHOICES,
        empty_label='All Applicable To'
    )
    is_active = django_filters.BooleanFilter(
        widget=forms.CheckboxInput(),
        label='Active Only'
    )
    is_valid = django_filters.BooleanFilter(
        method='filter_valid',
        widget=forms.CheckboxInput(),
        label='Currently Valid'
    )
    
    class Meta:
        model = FeeDiscount
        fields = ['name', 'code', 'discount_type', 'applicable_to', 'is_active']
    
    def filter_valid(self, queryset, name, value):
        from django.utils import timezone
        today = timezone.now().date()
        
        if value:
            return queryset.filter(
                valid_from__lte=today,
                valid_until__gte=today,
                is_active=True
            )
        return queryset


class InvoiceFilter(django_filters.FilterSet):
    student = django_filters.CharFilter(
        method='filter_student',
        label='Student Name'
    )
    invoice_number = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Invoice Number'
    )
    status = django_filters.ChoiceFilter(
        choices=Invoice.INVOICE_STATUS_CHOICES,
        empty_label='All Statuses',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_overdue = django_filters.BooleanFilter(
        widget=forms.CheckboxInput(),
        label='Overdue Only'
    )
    has_due_amount = django_filters.BooleanFilter(
        method='filter_has_due_amount',
        widget=forms.CheckboxInput(),
        label='Has Due Amount'
    )
    issue_date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'}),
        label='Issue Date Range'
    )
    due_date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'}),
        label='Due Date Range'
    )
    
    class Meta:
        model = Invoice
        fields = ['student', 'invoice_number', 'academic_year', 'status', 'is_overdue']
    
    def filter_student(self, queryset, name, value):
        return queryset.filter(
            Q(student__first_name__icontains=value) |
            Q(student__last_name__icontains=value) |
            Q(student__roll_number__icontains=value)
        )
    
    def filter_has_due_amount(self, queryset, name, value):
        if value:
            return queryset.filter(due_amount__gt=0)
        return queryset


class PaymentFilter(django_filters.FilterSet):
    payment_number = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Payment Number'
    )
    payment_method = django_filters.ChoiceFilter(
        choices=Payment.PAYMENT_METHOD_CHOICES,
        empty_label='All Methods',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = django_filters.ChoiceFilter(
        choices=Payment.PAYMENT_STATUS_CHOICES,
        empty_label='All Statuses',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    received_by = django_filters.CharFilter(
        method='filter_received_by',
        label='Received By'
    )
    payment_date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'}),
        label='Payment Date Range'
    )
    amount_min = django_filters.NumberFilter(
        field_name='amount',
        lookup_expr='gte',
        label='Min Amount'
    )
    amount_max = django_filters.NumberFilter(
        field_name='amount',
        lookup_expr='lte',
        label='Max Amount'
    )
    
    class Meta:
        model = Payment
        fields = ['payment_number', 'payment_method', 'status', 'received_by']
    
    def filter_received_by(self, queryset, name, value):
        return queryset.filter(
            Q(received_by__first_name__icontains=value) |
            Q(received_by__last_name__icontains=value)
        )


class RefundFilter(django_filters.FilterSet):
    refund_number = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Refund Number'
    )
    status = django_filters.ChoiceFilter(
        choices=Refund.REFUND_STATUS_CHOICES,
        empty_label='All Statuses'
    )
    request_date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'}),
        label='Request Date Range'
    )
    
    class Meta:
        model = Refund
        fields = ['refund_number', 'status', 'payment']


class ExpenseFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method='filter_search',
        label='Search'
    )
    title = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Expense Title'
    )
    vendor_name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Vendor Name'
    )
    category = django_filters.ModelChoiceFilter(
        queryset=ExpenseCategory.objects.all(),
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = django_filters.ChoiceFilter(
        choices=Expense.EXPENSE_STATUS_CHOICES,
        empty_label='All Statuses',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    payment_method = django_filters.ChoiceFilter(
        choices=Expense.PAYMENT_METHOD_CHOICES,
        empty_label='All Methods',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    expense_date = django_filters.DateFilter(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Expense Date'
    )
    amount_min = django_filters.NumberFilter(
        field_name='amount',
        lookup_expr='gte',
        label='Min Amount'
    )
    amount_max = django_filters.NumberFilter(
        field_name='amount',
        lookup_expr='lte',
        label='Max Amount'
    )
    
    class Meta:
        model = Expense
        fields = ['category', 'status', 'payment_method']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(vendor_name__icontains=value)
        )


class BudgetFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Budget Name'
    )
    academic_year = django_filters.CharFilter(
        field_name='academic_year__name',
        lookup_expr='icontains',
        label='Academic Year'
    )
    status = django_filters.ChoiceFilter(
        choices=Budget.BUDGET_STATUS_CHOICES,
        empty_label='All Statuses'
    )
    start_date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'}),
        label='Start Date Range'
    )
    end_date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'}),
        label='End Date Range'
    )
    total_amount_min = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='gte',
        label='Min Budget Amount'
    )
    total_amount_max = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='lte',
        label='Max Budget Amount'
    )
    
    class Meta:
        model = Budget
        fields = ['name', 'academic_year', 'status']


class BankAccountFilter(django_filters.FilterSet):
    account_name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Account Name'
    )
    account_number = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Account Number'
    )
    bank_name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Bank Name'
    )
    account_type = django_filters.ChoiceFilter(
        choices=BankAccount.ACCOUNT_TYPE_CHOICES,
        empty_label='All Account Types'
    )
    is_active = django_filters.BooleanFilter(
        widget=forms.CheckboxInput(),
        label='Active Only'
    )
    
    class Meta:
        model = BankAccount
        fields = ['account_name', 'account_number', 'bank_name', 'account_type', 'is_active']


class FinancialTransactionFilter(django_filters.FilterSet):
    transaction_number = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Transaction Number'
    )
    transaction_type = django_filters.ChoiceFilter(
        choices=FinancialTransaction.TRANSACTION_TYPE_CHOICES,
        empty_label='All Types'
    )
    transaction_date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'}),
        label='Transaction Date Range'
    )
    debit_account = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Debit Account'
    )
    credit_account = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Credit Account'
    )
    
    class Meta:
        model = FinancialTransaction
        fields = ['transaction_number', 'transaction_type', 'debit_account', 'credit_account']


class ExpenseCategoryFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method='filter_search',
        label='Search'
    )
    code = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Category Code'
    )
    category_type = django_filters.ChoiceFilter(
        choices=ExpenseCategory.CATEGORY_TYPE_CHOICES,
        empty_label='All Types',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = django_filters.ChoiceFilter(
        choices=[(True, 'Active'), (False, 'Inactive')],
        empty_label='All Statuses',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Status'
    )
    
    class Meta:
        model = ExpenseCategory
        fields = ['search', 'code', 'category_type', 'is_active']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )

    



# Custom filter for student/parent portal
class MyInvoiceFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        choices=Invoice.INVOICE_STATUS_CHOICES,
        empty_label='All Statuses'
    )
    is_overdue = django_filters.BooleanFilter(
        widget=forms.CheckboxInput(),
        label='Overdue Only'
    )
    issue_date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date'}),
        label='Issue Date Range'
    )
    
    class Meta:
        model = Invoice
        fields = ['status', 'is_overdue', 'academic_year']


# Custom filter for reports
class ReportFilter(django_filters.FilterSet):
    period = django_filters.ChoiceFilter(
        choices=FinancialReport.PERIOD_CHOICES,
        empty_label='All Periods'
    )
    report_type = django_filters.ChoiceFilter(
        choices=FinancialReport.REPORT_TYPE_CHOICES,
        empty_label='All Report Types'
    )
    start_date = django_filters.DateFilter(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='From Date'
    )
    end_date = django_filters.DateFilter(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='To Date'
    )
    
    class Meta:
        model = FinancialReport
        fields = ['report_type', 'period']