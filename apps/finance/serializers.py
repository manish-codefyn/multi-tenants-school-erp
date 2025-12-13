from rest_framework import serializers
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models
from .models import (
    FeeStructure, FeeDiscount, Invoice, InvoiceItem,
    AppliedDiscount, Payment, Refund, ExpenseCategory,
    Expense, Budget, FinancialTransaction, BankAccount,
    FinancialReport
)


class FeeStructureSerializer(serializers.ModelSerializer):
    class_name_name = serializers.CharField(source='class_name.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    fee_type_display = serializers.CharField(source='get_fee_type_display', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    
    class Meta:
        model = FeeStructure
        fields = [
            'id', 'name', 'academic_year', 'academic_year_name',
            'class_name', 'class_name_name', 'fee_type', 'fee_type_display',
            'frequency', 'frequency_display', 'amount', 'due_day',
            'late_fee_applicable', 'late_fee_amount', 'late_fee_after_days',
            'discount_allowed', 'max_discount_percentage', 'is_active',
            'total_fee_per_year', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'total_fee_per_year']
    
    def validate(self, data):
        # Check for duplicate fee structure
        if not self.instance:  # New instance
            if FeeStructure.objects.filter(
                academic_year=data.get('academic_year'),
                class_name=data.get('class_name'),
                fee_type=data.get('fee_type'),
                frequency=data.get('frequency'),
                tenant=self.context['request'].user.tenant
            ).exists():
                raise ValidationError("A fee structure with these details already exists.")
        
        return data


class FeeDiscountSerializer(serializers.ModelSerializer):
    discount_type_display = serializers.CharField(source='get_discount_type_display', read_only=True)
    applicable_to_display = serializers.CharField(source='get_applicable_to_display', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    usage_count = serializers.IntegerField(read_only=True)
    remaining_usage = serializers.IntegerField(read_only=True, allow_null=True)
    applicable_classes_names = serializers.SerializerMethodField()
    
    class Meta:
        model = FeeDiscount
        fields = [
            'id', 'name', 'code', 'description', 'discount_type',
            'discount_type_display', 'value', 'applicable_to',
            'applicable_to_display', 'applicable_classes',
            'applicable_classes_names', 'applicable_categories',
            'min_percentage_required', 'max_discount_amount',
            'max_usage_per_student', 'total_usage_limit',
            'valid_from', 'valid_until', 'required_documents',
            'is_active', 'is_valid', 'usage_count', 'remaining_usage',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_valid', 'usage_count', 'remaining_usage']
    
    def get_applicable_classes_names(self, obj):
        return [cls.name for cls in obj.applicable_classes.all()]
    
    def validate_applicable_categories(self, value):
        if value and not isinstance(value, list):
            raise ValidationError("Applicable categories must be a list.")
        return value
    
    def validate_required_documents(self, value):
        if value and not isinstance(value, list):
            raise ValidationError("Required documents must be a list.")
        return value
    
    def validate(self, data):
        valid_from = data.get('valid_from')
        valid_until = data.get('valid_until')
        
        if valid_from and valid_until:
            if valid_until < valid_from:
                raise ValidationError({
                    'valid_until': 'Valid until date must be after valid from date.'
                })
        
        discount_type = data.get('discount_type')
        value = data.get('value')
        
        if discount_type == 'PERCENTAGE' and value:
            if value > 100:
                raise ValidationError({
                    'value': 'Percentage discount cannot exceed 100%.'
                })
        
        return data


class InvoiceItemSerializer(serializers.ModelSerializer):
    fee_structure_name = serializers.CharField(source='fee_structure.name', read_only=True)
    fee_type = serializers.CharField(source='fee_structure.fee_type', read_only=True)
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'invoice', 'fee_structure', 'fee_structure_name',
            'fee_type', 'amount', 'description', 'tax_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AppliedDiscountSerializer(serializers.ModelSerializer):
    discount_name = serializers.CharField(source='discount.name', read_only=True)
    discount_code = serializers.CharField(source='discount.code', read_only=True)
    applied_by_name = serializers.CharField(source='applied_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = AppliedDiscount
        fields = [
            'id', 'invoice', 'discount', 'discount_name', 'discount_code',
            'amount', 'applied_by', 'applied_by_name', 'reason',
            'approved_by', 'approved_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class InvoiceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    class_name = serializers.CharField(source='student.current_class.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    discounts = AppliedDiscountSerializer(many=True, read_only=True)
    payment_progress = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    is_fully_paid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'student', 'student_name',
            'student_roll_number', 'class_name', 'academic_year',
            'academic_year_name', 'billing_period', 'issue_date',
            'due_date', 'subtotal', 'total_discount', 'total_tax',
            'late_fee', 'total_amount', 'paid_amount', 'due_amount',
            'status', 'status_display', 'payment_terms', 'notes',
            'is_overdue', 'overdue_days', 'is_fully_paid',
            'payment_progress', 'items', 'discounts', 'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'invoice_number', 'is_overdue',
            'overdue_days', 'payment_progress', 'is_fully_paid'
        ]
    
    def validate(self, data):
        due_date = data.get('due_date')
        issue_date = data.get('issue_date')
        
        if due_date and issue_date:
            if due_date < issue_date:
                raise ValidationError({
                    'due_date': 'Due date cannot be before issue date.'
                })
        
        return data


class PaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    student_name = serializers.CharField(source='invoice.student.get_full_name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    received_by_name = serializers.CharField(source='received_by.get_full_name', read_only=True)
    paid_by_name = serializers.CharField(source='paid_by.get_full_name', read_only=True, allow_null=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_number', 'invoice', 'invoice_number',
            'student_name', 'amount', 'payment_date', 'payment_method',
            'payment_method_display', 'reference_number', 'bank_name',
            'branch_name', 'cheque_dd_number', 'cheque_dd_date',
            'transaction_id', 'gateway_name', 'gateway_response',
            'status', 'status_display', 'received_by', 'received_by_name',
            'paid_by', 'paid_by_name', 'verified_by', 'verified_by_name',
            'verification_date', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'payment_number',
            'verification_date'
        ]
    
    def validate_amount(self, value):
        if value <= 0:
            raise ValidationError('Payment amount must be greater than 0.')
        return value
    
    def validate(self, data):
        invoice = data.get('invoice')
        amount = data.get('amount')
        
        if invoice and amount:
            if amount > invoice.due_amount:
                raise ValidationError({
                    'amount': f'Payment amount cannot exceed due amount ({invoice.due_amount}).'
                })
        
        payment_method = data.get('payment_method')
        cheque_dd_date = data.get('cheque_dd_date')
        
        if payment_method in ['CHEQUE', 'DD'] and not cheque_dd_date:
            raise ValidationError({
                'cheque_dd_date': 'Cheque/DD date is required for this payment method.'
            })
        
        return data


class RefundSerializer(serializers.ModelSerializer):
    payment_number = serializers.CharField(source='payment.payment_number', read_only=True)
    invoice_number = serializers.CharField(source='payment.invoice.invoice_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True, allow_null=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = Refund
        fields = [
            'id', 'refund_number', 'payment', 'payment_number',
            'invoice_number', 'amount', 'reason', 'request_date',
            'status', 'status_display', 'approved_by', 'approved_by_name',
            'approval_date', 'processed_by', 'processed_by_name',
            'process_date', 'completion_date', 'refund_bank_account',
            'refund_bank_name', 'refund_ifsc_code', 'rejection_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'refund_number',
            'approval_date', 'process_date', 'completion_date'
        ]
    
    def validate_amount(self, value):
        if value <= 0:
            raise ValidationError('Refund amount must be greater than 0.')
        return value
    
    def validate(self, data):
        payment = data.get('payment')
        amount = data.get('amount')
        
        if payment and amount:
            if amount > payment.amount:
                raise ValidationError({
                    'amount': f'Refund amount cannot exceed payment amount ({payment.amount}).'
                })
            
            # Check if refund amount exceeds available amount
            total_refunded = Refund.objects.filter(
                payment=payment,
                status__in=['APPROVED', 'PROCESSED', 'COMPLETED']
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            available_for_refund = payment.amount - total_refunded
            
            if amount > available_for_refund:
                raise ValidationError({
                    'amount': f'Maximum refund available is {available_for_refund}.'
                })
        
        return data


class ExpenseCategorySerializer(serializers.ModelSerializer):
    category_type_display = serializers.CharField(source='get_category_type_display', read_only=True)
    parent_category_name = serializers.CharField(source='parent_category.name', read_only=True, allow_null=True)
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remaining_budget = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    budget_utilization_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = ExpenseCategory
        fields = [
            'id', 'name', 'code', 'category_type', 'category_type_display',
            'description', 'parent_category', 'parent_category_name',
            'budget_amount', 'is_active', 'total_expenses',
            'remaining_budget', 'budget_utilization_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'total_expenses',
            'remaining_budget', 'budget_utilization_percentage'
        ]
    
    def validate_code(self, value):
        # Check for duplicate code within tenant
        if ExpenseCategory.objects.filter(
            code=value,
            tenant=self.context['request'].user.tenant
        ).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise ValidationError('An expense category with this code already exists.')
        return value


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_type = serializers.CharField(source='category.category_type', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'expense_number', 'category', 'category_name',
            'category_type', 'title', 'description', 'amount',
            'expense_date', 'payment_date', 'vendor_name',
            'vendor_contact', 'bill_number', 'bill_date',
            'payment_method', 'payment_method_display',
            'reference_number', 'status', 'status_display',
            'submitted_by', 'submitted_by_name', 'approved_by',
            'approved_by_name', 'approval_date', 'rejection_reason',
            'supporting_documents', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'expense_number',
            'approval_date'
        ]
    
    def validate_supporting_documents(self, value):
        if value and not isinstance(value, list):
            raise ValidationError("Supporting documents must be a list.")
        return value
    
    def validate(self, data):
        bill_date = data.get('bill_date')
        expense_date = data.get('expense_date')
        
        if bill_date and expense_date:
            if bill_date > expense_date:
                raise ValidationError({
                    'bill_date': 'Bill date cannot be after expense date.'
                })
        
        return data


class BudgetSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prepared_by_name = serializers.CharField(source='prepared_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True, allow_null=True)
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remaining_budget = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    utilization_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = Budget
        fields = [
            'id', 'name', 'academic_year', 'academic_year_name',
            'total_amount', 'status', 'status_display', 'start_date',
            'end_date', 'prepared_by', 'prepared_by_name', 'approved_by',
            'approved_by_name', 'approval_date', 'budget_items', 'notes',
            'total_expenses', 'remaining_budget', 'utilization_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'approval_date',
            'total_expenses', 'remaining_budget', 'utilization_percentage'
        ]
    
    def validate_budget_items(self, value):
        if value and not isinstance(value, list):
            raise ValidationError("Budget items must be a list.")
        
        # Validate each item has required fields
        for item in value:
            if not all(key in item for key in ['category', 'amount']):
                raise ValidationError("Each budget item must have 'category' and 'amount' fields")
        
        return value
    
    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        academic_year = data.get('academic_year')
        
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
        
        return data


class BankAccountSerializer(serializers.ModelSerializer):
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    authorized_signatories_names = serializers.SerializerMethodField()
    
    class Meta:
        model = BankAccount
        fields = [
            'id', 'account_name', 'account_number', 'bank_name',
            'branch_name', 'ifsc_code', 'account_type',
            'account_type_display', 'current_balance', 'as_of_date',
            'bank_contact', 'bank_address', 'authorized_signatories',
            'authorized_signatories_names', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_authorized_signatories_names(self, obj):
        return [user.get_full_name() for user in obj.authorized_signatories.all()]
    
    def validate_ifsc_code(self, value):
        if value and len(value) != 11:
            raise ValidationError('IFSC code must be 11 characters long.')
        return value.upper() if value else value
    
    def validate_account_number(self, value):
        # Check for duplicate account number within tenant
        if BankAccount.objects.filter(
            account_number=value,
            tenant=self.context['request'].user.tenant
        ).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise ValidationError('A bank account with this account number already exists.')
        return value


class FinancialTransactionSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    entered_by_name = serializers.CharField(source='entered_by.get_full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True, allow_null=True)
    related_invoice_number = serializers.CharField(source='related_invoice.invoice_number', read_only=True, allow_null=True)
    related_expense_number = serializers.CharField(source='related_expense.expense_number', read_only=True, allow_null=True)
    
    class Meta:
        model = FinancialTransaction
        fields = [
            'id', 'transaction_number', 'transaction_type',
            'transaction_type_display', 'transaction_date', 'amount',
            'debit_account', 'credit_account', 'description',
            'reference', 'related_invoice', 'related_invoice_number',
            'related_expense', 'related_expense_number', 'entered_by',
            'entered_by_name', 'verified_by', 'verified_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'transaction_number']


class FinancialReportSerializer(serializers.ModelSerializer):
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    export_format_display = serializers.CharField(source='get_export_format_display', read_only=True)
    
    class Meta:
        model = FinancialReport
        fields = [
            'id', 'report_type', 'report_type_display', 'report_name',
            'period', 'period_display', 'start_date', 'end_date',
            'report_data', 'summary', 'generated_by', 'generated_by_name',
            'generated_at', 'export_file', 'export_format',
            'export_format_display', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'report_data', 'summary',
            'generated_by', 'generated_at', 'export_file'
        ]
    
    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        period = data.get('period')
        
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
        
        return data


# ==================== NESTED SERIALIZERS ====================

class InvoiceWithPaymentsSerializer(InvoiceSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    
    class Meta(InvoiceSerializer.Meta):
        fields = InvoiceSerializer.Meta.fields + ['payments']


class PaymentWithRefundsSerializer(PaymentSerializer):
    refunds = RefundSerializer(many=True, read_only=True)
    
    class Meta(PaymentSerializer.Meta):
        fields = PaymentSerializer.Meta.fields + ['refunds']


class ExpenseCategoryWithExpensesSerializer(ExpenseCategorySerializer):
    expenses = ExpenseSerializer(many=True, read_only=True)
    
    class Meta(ExpenseCategorySerializer.Meta):
        fields = ExpenseCategorySerializer.Meta.fields + ['expenses']


class BudgetWithAnalysisSerializer(BudgetSerializer):
    budget_analysis = serializers.SerializerMethodField()
    
    class Meta(BudgetSerializer.Meta):
        fields = BudgetSerializer.Meta.fields + ['budget_analysis']
    
    def get_budget_analysis(self, obj):
        # Calculate detailed budget analysis
        try:
            budget_items = obj.budget_items
            if isinstance(budget_items, str):
                import json
                budget_items = json.loads(budget_items)
        except:
            budget_items = []
        
        analysis = []
        for item in budget_items:
            category_name = item.get('category', 'Unknown')
            budget_amount = Decimal(item.get('amount', 0))
            
            # Get actual expenses for this category
            actual_amount = Expense.objects.filter(
                category__name=category_name,
                status='PAID',
                expense_date__range=[obj.start_date, obj.end_date],
                tenant=obj.tenant
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            variance = budget_amount - actual_amount
            variance_percentage = (variance / budget_amount * 100) if budget_amount > 0 else 0
            
            analysis.append({
                'category': category_name,
                'budget': float(budget_amount),
                'actual': float(actual_amount),
                'variance': float(variance),
                'variance_percentage': float(variance_percentage)
            })
        
        return analysis


# ==================== SUMMARY SERIALIZERS ====================

class FinanceSummarySerializer(serializers.Serializer):
    total_collection = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_collection = serializers.DecimalField(max_digits=12, decimal_places=2)
    outstanding_invoices = serializers.IntegerField()
    total_outstanding = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_progress = serializers.DecimalField(max_digits=5, decimal_places=2)


class PaymentMethodSummarySerializer(serializers.Serializer):
    payment_method = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    count = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class ExpenseCategorySummarySerializer(serializers.Serializer):
    category = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    count = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


# ==================== DASHBOARD SERIALIZERS ====================

class DashboardStatsSerializer(serializers.Serializer):
    # Fee Collection
    total_fee_collection = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_collection = serializers.DecimalField(max_digits=12, decimal_places=2)
    collection_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Outstanding
    outstanding_invoices = serializers.IntegerField()
    total_outstanding = serializers.DecimalField(max_digits=12, decimal_places=2)
    overdue_invoices = serializers.IntegerField()
    
    # Expenses
    monthly_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Recent Activity
    recent_payments = PaymentSerializer(many=True)
    recent_invoices = InvoiceSerializer(many=True)
    recent_expenses = ExpenseSerializer(many=True)


class MonthlyCollectionSerializer(serializers.Serializer):
    month = serializers.DateField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2)


class ExpenseByCategorySerializer(serializers.Serializer):
    category = serializers.CharField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)