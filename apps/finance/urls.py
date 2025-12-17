from django.urls import path, include
from django.contrib.auth.decorators import login_required
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'finance'

# ==================== API ROUTER ====================
router = DefaultRouter()
router.register(r'fee-structures', views.FeeStructureAPIViewSet)
router.register(r'invoices', views.InvoiceAPIViewSet)
router.register(r'payments', views.PaymentAPIViewSet)
router.register(r'expenses', views.ExpenseAPIViewSet)

urlpatterns = [
    # ==================== DASHBOARD ====================
    path('', login_required(views.FinanceDashboardView.as_view()), name='dashboard'),

    # ==================== FEE STRUCTURE ====================
    path('fee-structures/', include([
        path('', login_required(views.FeeStructureListView.as_view()), name='fee_structure_list'),
        path('create/', login_required(views.FeeStructureCreateView.as_view()), name='fee_structure_create'),
        path('<uuid:pk>/', include([
            path('', login_required(views.FeeStructureDetailView.as_view()), name='fee_structure_detail'),
            path('edit/', login_required(views.FeeStructureUpdateView.as_view()), name='fee_structure_update'),
            path('delete/', login_required(views.FeeStructureDeleteView.as_view()), name='fee_structure_delete'),
        ])),
    ])),

    # ==================== FEE DISCOUNTS ====================
    path('discounts/', include([
        path('', login_required(views.FeeDiscountListView.as_view()), name='fee_discount_list'),
        path('create/', login_required(views.FeeDiscountCreateView.as_view()), name='fee_discount_create'),
        path('<uuid:pk>/', include([
            path('', login_required(views.FeeDiscountDetailView.as_view()), name='fee_discount_detail'),
            path('edit/', login_required(views.FeeDiscountUpdateView.as_view()), name='fee_discount_update'),
        ])),
    ])),

    # ==================== INVOICES ====================
    path('invoices/', include([
        path('', login_required(views.InvoiceListView.as_view()), name='invoice_list'),
        path('create/', login_required(views.InvoiceCreateView.as_view()), name='invoice_create'),
        path('bulk-action/', login_required(views.BulkInvoiceActionView.as_view()), name='invoice_bulk_action'),
        path('<uuid:pk>/', include([
            path('', login_required(views.InvoiceDetailView.as_view()), name='invoice_detail'),
            path('edit/', login_required(views.InvoiceUpdateView.as_view()), name='invoice_update'),
            path('print/', login_required(views.InvoicePrintView.as_view()), name='invoice_print'),
            path('send/', login_required(views.InvoiceSendView.as_view()), name='invoice_send'),
            path('apply-discount/', login_required(views.InvoiceApplyDiscountView.as_view()), name='invoice_apply_discount'),
        ])),
    ])),

    # ==================== PAYMENTS ====================
    path('payments/', include([
        path('', login_required(views.PaymentListView.as_view()), name='payment_list'),
        path('create/', login_required(views.PaymentCreateView.as_view()), name='payment_create'),
        path('<uuid:pk>/', include([
            path('', login_required(views.PaymentDetailView.as_view()), name='payment_detail'),
            path('verify/', login_required(views.PaymentVerifyView.as_view()), name='payment_verify'),
            path('print/', login_required(views.PaymentPrintView.as_view()), name='payment_print'),
        ])),
    ])),

    # ==================== EXPENSES ====================
    path('expenses/', include([
        path('', login_required(views.ExpenseListView.as_view()), name='expense_list'),
        path('create/', login_required(views.ExpenseCreateView.as_view()), name='expense_create'),
        path('<uuid:pk>/', include([
            path('', login_required(views.ExpenseDetailView.as_view()), name='expense_detail'),
            path('edit/', login_required(views.ExpenseUpdateView.as_view()), name='expense_update'),
            path('approve/', login_required(views.ExpenseApproveView.as_view()), name='expense_approve'),
            path('reject/', login_required(views.ExpenseRejectView.as_view()), name='expense_reject'),
        ])),
    ])),

    # ==================== BUDGET MANAGEMENT ====================
    path('budgets/', include([
        path('', login_required(views.BudgetListView.as_view()), name='budget_list'),
        path('create/', login_required(views.BudgetCreateView.as_view()), name='budget_create'),
        
        # Categories
        path('categories/', include([
             path('', login_required(views.BudgetCategoryListView.as_view()), name='budget_category_list'),
             path('create/', login_required(views.BudgetCategoryCreateView.as_view()), name='budget_category_create'),
             path('<uuid:pk>/edit/', login_required(views.BudgetCategoryUpdateView.as_view()), name='budget_category_update'),
             path('<uuid:pk>/delete/', login_required(views.BudgetCategoryDeleteView.as_view()), name='budget_category_delete'),
        ])),

        # Templates
        path('templates/', include([
             path('', login_required(views.BudgetTemplateListView.as_view()), name='budget_template_list'),
             path('create/', login_required(views.BudgetTemplateCreateView.as_view()), name='budget_template_create'),
             path('<uuid:pk>/edit/', login_required(views.BudgetTemplateUpdateView.as_view()), name='budget_template_update'),
             path('<uuid:pk>/delete/', login_required(views.BudgetTemplateDeleteView.as_view()), name='budget_template_delete'),
        ])),

        path('<uuid:pk>/', include([
            path('', login_required(views.BudgetDetailView.as_view()), name='budget_detail'),
            path('edit/', login_required(views.BudgetUpdateView.as_view()), name='budget_update'),
            path('delete/', login_required(views.BudgetDeleteView.as_view()), name='budget_delete'),
            path('approve/', login_required(views.BudgetApproveView.as_view()), name='budget_approve'),
            path('activate/', login_required(views.BudgetActivateView.as_view()), name='budget_activate'),
        ])),
    ])),

    # ==================== REFUNDS ====================
    path('refunds/', include([
        path('', login_required(views.RefundListView.as_view()), name='refund_list'),
        path('create/', login_required(views.RefundCreateView.as_view()), name='refund_create'),
        path('<uuid:pk>/', include([
            path('', login_required(views.RefundDetailView.as_view()), name='refund_detail'),
            path('approve/', login_required(views.RefundApproveView.as_view()), name='refund_approve'),
            path('process/', login_required(views.RefundProcessView.as_view()), name='refund_process'),
            path('complete/', login_required(views.RefundCompleteView.as_view()), name='refund_complete'),
        ])),
    ])),

    # ==================== BANK ACCOUNTS ====================
    path('bank-accounts/', include([
        path('', login_required(views.BankAccountListView.as_view()), name='bank_account_list'),
        path('create/', login_required(views.BankAccountCreateView.as_view()), name='bank_account_create'),
        path('<uuid:pk>/', include([
            path('', login_required(views.BankAccountDetailView.as_view()), name='bank_account_detail'),
            path('edit/', login_required(views.BankAccountUpdateView.as_view()), name='bank_account_update'),
        ])),
    ])),

    # ==================== EXPENSE CATEGORIES ====================
    path('expense-categories/', include([
        path('', login_required(views.ExpenseCategoryListView.as_view()), name='expense_category_list'),
        path('create/', login_required(views.ExpenseCategoryCreateView.as_view()), name='expense_category_create'),
        path('<uuid:pk>/', include([
            path('', login_required(views.ExpenseCategoryDetailView.as_view()), name='expense_category_detail'),
            path('edit/', login_required(views.ExpenseCategoryUpdateView.as_view()), name='expense_category_update'),
        ])),
    ])),

    # ==================== REPORTS ====================
    path('reports/', include([
        path('fee-collection/', login_required(views.FeeCollectionReportView.as_view()), name='report_fee_collection'),
        path('due-fees/', login_required(views.DueFeesReportView.as_view()), name='report_due_fees'),
        path('expense-summary/', login_required(views.ExpenseSummaryReportView.as_view()), name='report_expense_summary'),
        path('budget-vs-actual/', login_required(views.BudgetVsActualReportView.as_view()), name='report_budget_vs_actual'),
    path('financial/', include([
            path('', login_required(views.FinancialReportListView.as_view()), name='financial_report_list'),
            path('create/', login_required(views.FinancialReportCreateView.as_view()), name='financial_report_create'),
            path('<uuid:pk>/', include([
                path('', login_required(views.FinancialReportDetailView.as_view()), name='financial_report_detail'),
                path('download/', login_required(views.FinancialReportDownloadView.as_view()), name='financial_report_download'),
            ])),
        ])),
    ])),

    # ==================== TRANSACTIONS ====================
    path('transactions/', include([
        path('', login_required(views.FinancialTransactionListView.as_view()), name='financial_transaction_list'),
        path('create/', login_required(views.FinancialTransactionCreateView.as_view()), name='financial_transaction_create'),
        path('<uuid:pk>/', login_required(views.FinancialTransactionDetailView.as_view()), name='financial_transaction_detail'),
    ])),

    # ==================== UTILITIES ====================
    path('generate-invoices/', login_required(views.GenerateMonthlyInvoicesView.as_view()), name='generate_invoices'),
    path('send-reminders/', login_required(views.SendPaymentRemindersView.as_view()), name='send_reminders'),

    # ==================== STUDENT / PARENT PORTAL ====================
    path('my/', include([
        path('invoices/', login_required(views.MyInvoicesView.as_view()), name='my_invoices'),
        path('payments/', login_required(views.MyPaymentsView.as_view()), name='my_payments'),
        path('payment-gateway/<uuid:invoice_id>/', login_required(views.PaymentGatewayView.as_view()), name='payment_gateway'),
        path('payment-callback/', views.PaymentCallbackView.as_view(), name='payment_callback'),
    ])),

    # ==================== API ====================
    path('api/', include(router.urls)),
]
