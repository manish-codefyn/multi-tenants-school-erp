from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('dashboard/', views.StudentDashboardView.as_view(), name='dashboard'),
    
    # Students
    path('', views.StudentListView.as_view(), name='student_list'),
    path('<uuid:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('create/', views.StudentCreateView.as_view(), name='student_create'),
    path('<uuid:pk>/update/', views.StudentUpdateView.as_view(), name='student_update'),
    path('<uuid:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
]
