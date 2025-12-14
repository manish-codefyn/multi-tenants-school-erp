from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.StudentDashboardView.as_view(), name='dashboard'),
    
    # CRUD Operations
    path('', views.StudentListView.as_view(), name='student_list'),
    path('create/', views.StudentCreateView.as_view(), name='student_create'),
    path('<uuid:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('<uuid:pk>/edit/', views.StudentUpdateView.as_view(), name='student_update'),
    path('<uuid:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
    path('<uuid:pk>/id-card/', views.StudentIdCardView.as_view(), name='student_id_card'),
    
    # Registration Wizard
    path('register/step1/', views.StudentRegistrationStep1View.as_view(), name='registration_step1'),
    path('register/step2/<uuid:student_id>/', views.StudentRegistrationStep2View.as_view(), name='registration_step2'),
    path('register/step3/<uuid:student_id>/', views.StudentRegistrationStep3View.as_view(), name='registration_step3'),
    
    # Guardian Management
    path('<uuid:student_id>/guardians/add/', views.GuardianCreateView.as_view(), name='guardian_create'),
    path('<uuid:student_id>/guardians/<uuid:guardian_id>/edit/', views.GuardianUpdateView.as_view(), name='guardian_update'),
    
    # Document Management
    path('<uuid:student_id>/documents/upload/', views.DocumentUploadView.as_view(), name='document_upload'),
    path('documents/<uuid:pk>/download/', views.DocumentDownloadView.as_view(), name='document_download'),
    
    # Bulk Operations
    path('bulk-upload/', views.StudentBulkUploadView.as_view(), name='bulk_upload'),
    path('bulk-upload/summary/', views.BulkUploadSummaryView.as_view(), name='bulk_upload_summary'),
    path('bulk-upload/sample/', views.BulkUploadSampleView.as_view(), name='bulk_upload_sample'),
    path('bulk-upload/validate/', views.BulkUploadValidateView.as_view(), name='bulk_upload_validate'),
    
    # Export
    path('export/', views.StudentExportView.as_view(), name='student_export'),
    
    # Specialized Views
    path('<uuid:pk>/academic-history/', views.StudentAcademicHistoryView.as_view(), name='student_academic_history'),
    path('<uuid:pk>/promote/', views.StudentPromoteView.as_view(), name='student_promote'),
    path('<uuid:pk>/report/', views.StudentReportView.as_view(), name='student_report'),
]