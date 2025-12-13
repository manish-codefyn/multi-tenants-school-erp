from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path('dashboard/', views.ExamDashboardView.as_view(), name='dashboard'),
    
    # Exam Types
    path('types/', views.ExamTypeListView.as_view(), name='exam_type_list'),
    path('types/create/', views.ExamTypeCreateView.as_view(), name='exam_type_create'),
    path('types/<int:pk>/update/', views.ExamTypeUpdateView.as_view(), name='exam_type_update'),
    path('types/<int:pk>/delete/', views.ExamTypeDeleteView.as_view(), name='exam_type_delete'),
    
    # Exams
    path('', views.ExamListView.as_view(), name='exam_list'),
    path('<int:pk>/', views.ExamDetailView.as_view(), name='exam_detail'),
    path('create/', views.ExamCreateView.as_view(), name='exam_create'),
    path('<int:pk>/update/', views.ExamUpdateView.as_view(), name='exam_update'),
    path('<int:pk>/delete/', views.ExamDeleteView.as_view(), name='exam_delete'),
    
    # Grading Systems
    path('grading/', views.GradingSystemListView.as_view(), name='grading_system_list'),
    path('grading/create/', views.GradingSystemCreateView.as_view(), name='grading_system_create'),
    path('grading/<int:pk>/update/', views.GradingSystemUpdateView.as_view(), name='grading_system_update'),
    path('grading/<int:pk>/delete/', views.GradingSystemDeleteView.as_view(), name='grading_system_delete'),
]
