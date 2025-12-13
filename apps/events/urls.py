from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('dashboard/', views.EventDashboardView.as_view(), name='dashboard'),
    
    # Event Categories
    path('categories/', views.EventCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.EventCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', views.EventCategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.EventCategoryDeleteView.as_view(), name='category_delete'),
    
    # Events
    path('', views.EventListView.as_view(), name='event_list'),
    path('<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('create/', views.EventCreateView.as_view(), name='event_create'),
    path('<int:pk>/update/', views.EventUpdateView.as_view(), name='event_update'),
    path('<int:pk>/delete/', views.EventDeleteView.as_view(), name='event_delete'),
]
