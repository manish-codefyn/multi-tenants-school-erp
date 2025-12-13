# apps/students/urls.py
from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Student CRUD
    path('', views.StudentListView.as_view(), name='student_list'),
    path('create/', views.StudentCreateView.as_view(), name='student_create'),
    path('<uuid:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('<uuid:pk>/edit/', views.StudentUpdateView.as_view(), name='student_update'),
    path('<uuid:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
    
    # Dashboard
    path('dashboard/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    
    # Export
    path('export/', views.StudentExportView.as_view(), name='student_export'),
    
    # Guardian management
    path('<uuid:student_id>/guardians/add/', views.GuardianCreateView.as_view(), name='guardian_create'),
    
    # Document management
    path('<uuid:student_id>/documents/upload/', views.DocumentUploadView.as_view(), name='document_upload'),
]