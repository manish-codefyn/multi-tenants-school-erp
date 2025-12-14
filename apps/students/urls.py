# students/urls.py
from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Main Lists & Dashboard
    path('dashboard/', views.StudentDashboardView.as_view(), name='dashboard'),
    
    path('', views.StudentListView.as_view(), name='student_list'),
    path('onboarding/<uuid:pk>/', views.StudentOnboardingView.as_view(), name='student_onboarding'),
    path('list/', views.StudentListView.as_view(), name='student_list_alt'), 
    path('detail/<uuid:pk>/', views.StudentDetailView.as_view(), name='student_detail'),

    # Step 1: Basic Info
    path('create/basic/', views.StudentBasicCreateView.as_view(), name='student_create_basic'),
    path('update/<uuid:pk>/basic/', views.StudentBasicUpdateView.as_view(), name='student_update_basic'),

    # Step 2: Guardian
    path('create/<uuid:student_id>/guardian/', views.GuardianCreateView.as_view(), name='guardian_create'),
    path('update/<uuid:student_id>/guardian/<uuid:guardian_id>/', views.GuardianUpdateView.as_view(), name='guardian_update'),

    # Step 3: Address
    path('create/<uuid:student_id>/address/', views.AddressCreateView.as_view(), name='address_create'),
    path('update/<uuid:student_id>/address/<uuid:pk>/', views.AddressUpdateView.as_view(), name='address_update'),

    # Step 4: Medical
    path('create/<uuid:student_id>/medical/', views.MedicalInfoCreateView.as_view(), name='medical_create'),
    path('update/<uuid:student_id>/medical/<uuid:pk>/', views.MedicalInfoUpdateView.as_view(), name='medical_update'),

    # Step 5: Transport
    path('create/<uuid:student_id>/transport/', views.StudentTransportCreateView.as_view(), name='transport_create'),
    path('update/<uuid:student_id>/transport/<uuid:pk>/', views.StudentTransportUpdateView.as_view(), name='transport_update'),

    # Step 6: Hostel
    path('create/<uuid:student_id>/hostel/', views.StudentHostelCreateView.as_view(), name='hostel_create'),
    path('update/<uuid:student_id>/hostel/<uuid:pk>/', views.StudentHostelUpdateView.as_view(), name='hostel_update'),

    # Step 7: Academic History
    path('create/<uuid:student_id>/history/', views.StudentHistoryCreateView.as_view(), name='history_create'),
    path('update/<uuid:student_id>/history/<uuid:pk>/', views.StudentHistoryUpdateView.as_view(), name='history_update'),

    # Step 8: Identification
    path('create/<uuid:student_id>/identity/', views.StudentIdentificationCreateView.as_view(), name='identity_create'),
    path('update/<uuid:student_id>/identity/<uuid:pk>/', views.StudentIdentificationUpdateView.as_view(), name='identity_update'),

    # Step 9: Documents
    path('upload/<uuid:student_id>/document/', views.DocumentUploadView.as_view(), name='document_upload'),
    path('document/<uuid:document_id>/download/', views.DocumentDownloadView.as_view(), name='document_download'),
    path('document/<uuid:pk>/delete/', views.DocumentDeleteView.as_view(), name='document_delete'),

    # Bulk Operations
    path('bulk/upload/', views.StudentBulkUploadView.as_view(), name='bulk_upload'),
    path('bulk/summary/', views.BulkUploadSummaryView.as_view(), name='bulk_upload_summary'),
    path('bulk/sample/', views.BulkUploadSampleView.as_view(), name='bulk_upload_sample'),
    path('bulk/validate/', views.BulkUploadValidateView.as_view(), name='bulk_upload_validate'),

    # Export
    path('export/', views.StudentExportView.as_view(), name='student_export'),

    # Special Actions
    path('promote/<uuid:pk>/', views.StudentPromoteView.as_view(), name='student_promote'),
    path('report/<uuid:pk>/', views.StudentReportView.as_view(), name='student_report'),
    path('id-card/<uuid:pk>/', views.StudentIdCardView.as_view(), name='student_id_card'),
]