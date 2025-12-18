from django.urls import path, include
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'exams'

urlpatterns = [
    # ==================== DASHBOARD ====================
    path('', login_required(views.ExamDashboardView.as_view()), name='dashboard'),

    # ==================== EXAM TYPE ====================
    path('types/', include([
        path('', login_required(views.ExamTypeListView.as_view()), name='exam_type_list'),
        path('create/', login_required(views.ExamTypeCreateView.as_view()), name='exam_type_create'),
        path('<uuid:pk>/', include([
            path('edit/', login_required(views.ExamTypeUpdateView.as_view()), name='exam_type_update'),
            path('delete/', login_required(views.ExamTypeDeleteView.as_view()), name='exam_type_delete'),
        ])),
    ])),

    # ==================== EXAM ====================
    path('exams/', include([
        path('', login_required(views.ExamListView.as_view()), name='exam_list'),
        path('create/', login_required(views.ExamCreateView.as_view()), name='exam_create'),
        path('<uuid:pk>/', include([
            path('edit/', login_required(views.ExamUpdateView.as_view()), name='exam_update'),
            path('delete/', login_required(views.ExamDeleteView.as_view()), name='exam_delete'),
        ])),
    ])),

    # ==================== GRADING SYSTEM ====================
    path('grading/', include([
        path('', login_required(views.GradingSystemListView.as_view()), name='grading_system_list'),
        path('create/', login_required(views.GradingSystemCreateView.as_view()), name='grading_system_create'),
        path('<uuid:pk>/', include([
            path('edit/', login_required(views.GradingSystemUpdateView.as_view()), name='grading_system_update'),
            path('delete/', login_required(views.GradingSystemDeleteView.as_view()), name='grading_system_delete'),
        ])),
    ])),

    # ==================== RESULTS ====================
    path('results/', include([
        path('', login_required(views.ExamResultListView.as_view()), name='result_list'),
        path('<uuid:pk>/', login_required(views.ExamResultDetailView.as_view()), name='result_detail'),
        path('<uuid:pk>/PDF/', login_required(views.MarkSheetPDFView.as_view()), name='result_pdf'),
        path('verify/', views.MarkSheetVerificationView.as_view(), name='verify_result'),
        path('generate/<uuid:pk>/', login_required(views.GenerateResultsView.as_view()), name='generate_results'),
    ])),
]
