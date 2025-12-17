from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'finance'

router = DefaultRouter()
router.register(r'fee-structures', views.FeeStructureAPIViewSet)
router.register(r'invoices', views.InvoiceAPIViewSet)
router.register(r'payments', views.PaymentAPIViewSet)
router.register(r'expenses', views.ExpenseAPIViewSet)

urlpatterns = [
    # Dashboard
    path('', views.FinanceDashboardView.as_view(), name='dashboard'),
    
    # Fee Structure
    path('fee-structures/', views.FeeStructureListView.as_view(), name='fee_structure_list'),
    path('fee-structures/create/', views.FeeStructureCreateView.as_view(), name='fee_structure_create'),
    path('fee-structures/<uuid:pk>/', views.FeeStructureDetailView.as_view(), name='fee_structure_detail'),
    path('fee-structures/<uuid:pk>/update/', views.FeeStructureUpdateView.as_view(), name='fee_structure_update'),
    path('fee-structures/<uuid:pk>/delete/', views.FeeStructureDeleteView.as_view(), name='fee_structure_delete'),
    
    # Fee Discount
    path('discounts/', views.FeeDiscountListView.as_view(), name='fee_discount_list'),
    path('discounts/create/', views.FeeDiscountCreateView.as_view(), name='fee_discount_create'),
    path('discounts/<uuid:pk>/', views.FeeDiscountDetailView.as_view(), name='fee_discount_detail'),
    path('discounts/<uuid:pk>/update/', views.FeeDiscountUpdateView.as_view(), name='fee_discount_update'),
    
    # Invoice
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<uuid:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<uuid:pk>/update/', views.InvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/<uuid:pk>/print/', views.InvoicePrintView.as_view(), name='invoice_print'),
    path('invoices/<uuid:pk>/send/', views.InvoiceSendView.as_view(), name='invoice_send'),
    path('invoices/<uuid:pk>/apply-discount/', views.InvoiceApplyDiscountView.as_view(), name='invoice_apply_discount'),
    path('invoices/bulk-action/', views.BulkInvoiceActionView.as_view(), name='invoice_bulk_action'),
    
    # Payment
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/create/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('payments/<uuid:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('payments/<uuid:pk>/verify/', views.PaymentVerifyView.as_view(), name='payment_verify'),
    
    # Expense
    path('expenses/', views.ExpenseListView.as_view(), name='expense_list'),
    path('expenses/create/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/<uuid:pk>/', views.ExpenseDetailView.as_view(), name='expense_detail'),
    path('expenses/<uuid:pk>/update/', views.ExpenseUpdateView.as_view(), name='expense_update'),
    path('expenses/<uuid:pk>/approve/', views.ExpenseApproveView.as_view(), name='expense_approve'),
    path('expenses/<uuid:pk>/reject/', views.ExpenseRejectView.as_view(), name='expense_reject'),
    
    # Reports
    path('reports/fee-collection/', views.FeeCollectionReportView.as_view(), name='report_fee_collection'),
    path('reports/due-fees/', views.DueFeesReportView.as_view(), name='report_due_fees'),
    path('reports/expense-summary/', views.ExpenseSummaryReportView.as_view(), name='report_expense_summary'),
    path('reports/budget-vs-actual/', views.BudgetVsActualReportView.as_view(), name='report_budget_vs_actual'),
    
    # Utilities
    path('generate-invoices/', views.GenerateMonthlyInvoicesView.as_view(), name='generate_invoices'),
    path('send-reminders/', views.SendPaymentRemindersView.as_view(), name='send_reminders'),
    
    # Student/Parent Portal & Online Payments
    path('my-invoices/', views.MyInvoicesView.as_view(), name='my_invoices'),
    path('my-payments/', views.MyPaymentsView.as_view(), name='my_payments'),
    path('payment-gateway/<uuid:invoice_id>/', views.PaymentGatewayView.as_view(), name='payment_gateway'),
    path('payment-callback/', views.PaymentCallbackView.as_view(), name='payment_callback'),
    
    # Budget URLs
    path('budgets/', views.BudgetListView.as_view(), name='budget_list'),
    path('budgets/create/', views.BudgetCreateView.as_view(), name='budget_create'),
    path('budgets/<uuid:pk>/', views.BudgetDetailView.as_view(), name='budget_detail'),
    path('budgets/<uuid:pk>/update/', views.BudgetUpdateView.as_view(), name='budget_update'),
    path('budgets/<uuid:pk>/approve/', views.BudgetApproveView.as_view(), name='budget_approve'),
    path('budgets/<uuid:pk>/activate/', views.BudgetActivateView.as_view(), name='budget_activate'),
    
    # Refund URLs
    path('refunds/', views.RefundListView.as_view(), name='refund_list'),
    path('refunds/create/', views.RefundCreateView.as_view(), name='refund_create'),
    path('refunds/<uuid:pk>/', views.RefundDetailView.as_view(), name='refund_detail'),
    path('refunds/<uuid:pk>/approve/', views.RefundApproveView.as_view(), name='refund_approve'),
    path('refunds/<uuid:pk>/process/', views.RefundProcessView.as_view(), name='refund_process'),
    path('refunds/<uuid:pk>/complete/', views.RefundCompleteView.as_view(), name='refund_complete'),
    
    # Bank Account URLs
    path('bank-accounts/', views.BankAccountListView.as_view(), name='bank_account_list'),
    path('bank-accounts/create/', views.BankAccountCreateView.as_view(), name='bank_account_create'),
    path('bank-accounts/<uuid:pk>/', views.BankAccountDetailView.as_view(), name='bank_account_detail'),
    path('bank-accounts/<uuid:pk>/update/', views.BankAccountUpdateView.as_view(), name='bank_account_update'),
    
    # Expense Category URLs
    path('expense-categories/', views.ExpenseCategoryListView.as_view(), name='expense_category_list'),
    path('expense-categories/create/', views.ExpenseCategoryCreateView.as_view(), name='expense_category_create'),
    path('expense-categories/<uuid:pk>/', views.ExpenseCategoryDetailView.as_view(), name='expense_category_detail'),
    path('expense-categories/<uuid:pk>/update/', views.ExpenseCategoryUpdateView.as_view(), name='expense_category_update'),
    
    # Financial Transaction URLs
    path('financial-transactions/', views.FinancialTransactionListView.as_view(), name='financial_transaction_list'),
    path('financial-transactions/create/', views.FinancialTransactionCreateView.as_view(), name='financial_transaction_create'),
    path('financial-transactions/<uuid:pk>/', views.FinancialTransactionDetailView.as_view(), name='financial_transaction_detail'),
    
    # Financial Report URLs
    path('financial-reports/', views.FinancialReportListView.as_view(), name='financial_report_list'),
    path('financial-reports/create/', views.FinancialReportCreateView.as_view(), name='financial_report_create'),
    path('financial-reports/<uuid:pk>/', views.FinancialReportDetailView.as_view(), name='financial_report_detail'),
    path('financial-reports/<uuid:pk>/download/', views.FinancialReportDownloadView.as_view(), name='financial_report_download'),
    
    # API
    path('api/', include(router.urls)),
]
