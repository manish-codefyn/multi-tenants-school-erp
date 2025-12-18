from django.urls import path, include
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'inventory'

urlpatterns = [
    # ==================== DASHBOARD ====================
    path('', login_required(views.InventoryDashboardView.as_view()), name='dashboard'),

    # ==================== CATEGORY ====================
    path('categories/', include([
        path('', login_required(views.CategoryListView.as_view()), name='category_list'),
        path('create/', login_required(views.CategoryCreateView.as_view()), name='category_create'),
        path('<uuid:pk>/', include([
            path('edit/', login_required(views.CategoryUpdateView.as_view()), name='category_update'),
            path('delete/', login_required(views.CategoryDeleteView.as_view()), name='category_delete'),
        ])),
    ])),

    # ==================== SUPPLIER ====================
    path('suppliers/', include([
        path('', login_required(views.SupplierListView.as_view()), name='supplier_list'),
        path('create/', login_required(views.SupplierCreateView.as_view()), name='supplier_create'),
        path('<uuid:pk>/', include([
            path('edit/', login_required(views.SupplierUpdateView.as_view()), name='supplier_update'),
            path('delete/', login_required(views.SupplierDeleteView.as_view()), name='supplier_delete'),
        ])),
    ])),

    # ==================== ITEM ====================
    path('items/', include([
        path('', login_required(views.ItemListView.as_view()), name='item_list'),
        path('create/', login_required(views.ItemCreateView.as_view()), name='item_create'),
        path('<uuid:pk>/', include([
            path('edit/', login_required(views.ItemUpdateView.as_view()), name='item_update'),
            path('delete/', login_required(views.ItemDeleteView.as_view()), name='item_delete'),
        ])),
    ])),

    # ==================== STOCK MOVEMENT ====================
    path('movements/', include([
        path('', login_required(views.StockMovementListView.as_view()), name='stock_movement_list'),
        path('create/', login_required(views.StockMovementCreateView.as_view()), name='stock_movement_create'),
    ])),

    # ==================== PURCHASE ORDER ====================
    path('orders/', include([
        path('', login_required(views.PurchaseOrderListView.as_view()), name='purchase_order_list'),
        path('create/', login_required(views.PurchaseOrderCreateView.as_view()), name='purchase_order_create'),
        path('<uuid:pk>/', include([
            path('edit/', login_required(views.PurchaseOrderUpdateView.as_view()), name='purchase_order_update'),
            path('delete/', login_required(views.PurchaseOrderDeleteView.as_view()), name='purchase_order_delete'),
        ])),
    ])),
]
