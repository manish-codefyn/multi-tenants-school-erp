from django.contrib import admin
from .models import (
    FeeStructure, FeeDiscount, Invoice, InvoiceItem,
    AppliedDiscount, Payment
)

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'class_name', 'fee_type', 'frequency', 'amount', 'is_active')
    list_filter = ('fee_type', 'frequency', 'is_active', 'academic_year', 'class_name')
    search_fields = ('name', 'class_name__name')

@admin.register(FeeDiscount)
class FeeDiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'discount_type', 'value', 'applicable_to', 'valid_from', 'valid_until', 'is_active')
    list_filter = ('discount_type', 'applicable_to', 'is_active')
    search_fields = ('name', 'code')

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0

class AppliedDiscountInline(admin.TabularInline):
    model = AppliedDiscount
    extra = 0

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'student', 'issue_date', 'due_date', 'total_amount', 'paid_amount', 'status', 'is_overdue')
    list_filter = ('status', 'is_overdue', 'academic_year')
    search_fields = ('invoice_number', 'student__first_name', 'student__last_name', 'student__admission_number')
    inlines = [InvoiceItemInline, AppliedDiscountInline, PaymentInline]
    date_hierarchy = 'issue_date'

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'fee_structure', 'amount', 'tax_amount')
    search_fields = ('invoice__invoice_number', 'fee_structure__name')

@admin.register(AppliedDiscount)
class AppliedDiscountAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'discount', 'amount', 'applied_by')
    search_fields = ('invoice__invoice_number', 'discount__name')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_number', 'invoice', 'amount', 'payment_date', 'payment_method', 'status')
    list_filter = ('status', 'payment_method', 'payment_date')
    search_fields = ('payment_number', 'invoice__invoice_number', 'reference_number')
    date_hierarchy = 'payment_date'
