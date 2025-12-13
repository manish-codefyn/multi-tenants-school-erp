
from django.urls import path
from . import views

app_name = 'admission'

urlpatterns = [
    # Public URLs
    path('', views.AdmissionLandingView.as_view(), name='landing'),
    path('apply/', views.AdmissionRegistrationView.as_view(), name='apply_step1'),
    path('apply/<uuid:pk>/contact/', views.AdmissionContactView.as_view(), name='apply_step2'),
    path('apply/<uuid:pk>/academic/', views.AdmissionAcademicView.as_view(), name='apply_step3'),
    path('apply/<uuid:pk>/documents/', views.AdmissionDocumentView.as_view(), name='apply_step4'),
    path('apply/<uuid:pk>/review/', views.AdmissionReviewView.as_view(), name='apply_step5'),
    path('apply/success/<str:application_number>/', views.AdmissionSuccessView.as_view(), name='apply_success'),
    path('status/', views.AdmissionStatusView.as_view(), name='status'),
    
    # Staff URLs
    path('manage/', views.AdmissionListView.as_view(), name='staff_list'),
    path('manage/<uuid:pk>/', views.AdmissionDetailView.as_view(), name='staff_detail'),
    path('manage/<uuid:pk>/update/', views.AdmissionUpdateView.as_view(), name='staff_update'),
    path('manage/<uuid:pk>/delete/', views.AdmissionDeleteView.as_view(), name='staff_delete'),

    # Admission Cycle URLs
    path('cycles/', views.AdmissionCycleListView.as_view(), name='cycle_list'),
    path('cycles/create/', views.AdmissionCycleCreateView.as_view(), name='cycle_create'),
    path('cycles/<uuid:pk>/update/', views.AdmissionCycleUpdateView.as_view(), name='cycle_update'),
    path('cycles/<uuid:pk>/delete/', views.AdmissionCycleDeleteView.as_view(), name='cycle_delete'),

    # Admission Program URLs
    path('programs/', views.AdmissionProgramListView.as_view(), name='program_list'),
    path('programs/create/', views.AdmissionProgramCreateView.as_view(), name='program_create'),
    path('programs/<uuid:pk>/update/', views.AdmissionProgramUpdateView.as_view(), name='program_update'),
    path('programs/<uuid:pk>/delete/', views.AdmissionProgramDeleteView.as_view(), name='program_delete'),
]