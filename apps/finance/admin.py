from django.contrib import admin
from .models import (
    FeeStructure,
    FeeDiscount,
    Invoice,
    InvoiceItem,
    AppliedDiscount,
    Payment,
    Refund,
    ExpenseCategory,
    Expense,
    Budget,
    FinancialTransaction,
    BankAccount,
    FinancialReport,
)

# =========================
# INLINE ADMINS
# =========================

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


class AppliedDiscountInline(admin.TabularInline):
    model = AppliedDiscount
    extra = 0
    readonly_fields = ("amount",)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("payment_number", "payment_date", "status")


# =========================
# FEE STRUCTURE
# =========================

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "academic_year",
        "class_name",
        "fee_type",
        "frequency",
        "amount",
        "is_active",
    )
    list_filter = (
        "academic_year",
        "fee_type",
        "frequency",
        "is_active",
    )
    search_fields = ("name",)
    ordering = ("academic_year", "class_name")


# =========================
# FEE DISCOUNT
# =========================

@admin.register(FeeDiscount)
class FeeDiscountAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "discount_type",
        "value",
        "applicable_to",
        "valid_from",
        "valid_until",
        "is_active",
    )
    list_filter = (
        "discount_type",
        "applicable_to",
        "is_active",
    )
    search_fields = ("name", "code")
    filter_horizontal = ("applicable_classes",)


# =========================
# INVOICE
# =========================

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "student",
        "academic_year",
        "total_amount",
        "paid_amount",
        "due_amount",
        "status",
        "is_overdue",
    )
    list_filter = (
        "status",
        "academic_year",
        "is_overdue",
    )
    search_fields = ("invoice_number", "student__admission_number")
    date_hierarchy = "issue_date"
    inlines = [InvoiceItemInline, AppliedDiscountInline, PaymentInline]
    readonly_fields = (
        "subtotal",
        "total_discount",
        "total_tax",
        "total_amount",
        "paid_amount",
        "due_amount",
        "is_overdue",
        "overdue_days",
    )


# =========================
# PAYMENT
# =========================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "payment_number",
        "invoice",
        "amount",
        "payment_method",
        "status",
        "payment_date",
    )
    list_filter = ("payment_method", "status")
    search_fields = ("payment_number", "reference_number")
    date_hierarchy = "payment_date"


# =========================
# REFUND
# =========================

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = (
        "refund_number",
        "payment",
        "amount",
        "status",
        "request_date",
    )
    list_filter = ("status",)
    search_fields = ("refund_number",)
    date_hierarchy = "request_date"


# =========================
# EXPENSE CATEGORY
# =========================

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "category_type",
        "budget_amount",
        "is_active",
    )
    list_filter = ("category_type", "is_active")
    search_fields = ("name", "code")


# =========================
# EXPENSE
# =========================

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "expense_number",
        "title",
        "category",
        "amount",
        "status",
        "expense_date",
    )
    list_filter = ("status", "category")
    search_fields = ("expense_number", "title", "vendor_name")
    date_hierarchy = "expense_date"


# =========================
# BUDGET
# =========================

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "academic_year",
        "total_amount",
        "status",
        "start_date",
        "end_date",
    )
    list_filter = ("status", "academic_year")
    search_fields = ("name",)


# =========================
# FINANCIAL TRANSACTION
# =========================

@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_number",
        "transaction_type",
        "amount",
        "transaction_date",
    )
    list_filter = ("transaction_type",)
    search_fields = ("transaction_number",)
    date_hierarchy = "transaction_date"


# =========================
# BANK ACCOUNT
# =========================

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        "bank_name",
        "account_number",
        "account_name",
        "account_type",
        "current_balance",
        "is_active",
    )
    list_filter = ("bank_name", "account_type", "is_active")
    search_fields = ("account_number", "account_name")
    filter_horizontal = ("authorized_signatories",)


# =========================
# FINANCIAL REPORT
# =========================

@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = (
        "report_name",
        "report_type",
        "period",
        "start_date",
        "end_date",
        "generated_at",
    )
    list_filter = ("report_type", "period")
    search_fields = ("report_name",)
    date_hierarchy = "generated_at"
