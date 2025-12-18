from django.urls import path, include
from . import views

app_name = 'events'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.EventDashboardView.as_view(), name='dashboard'),
    
    # Categories
    path('categories/', include([
        path('', views.EventCategoryListView.as_view(), name='category_list'),
        path('create/', views.EventCategoryCreateView.as_view(), name='category_create'),
        path('<uuid:pk>/update/', views.EventCategoryUpdateView.as_view(), name='category_update'),
        path('<uuid:pk>/delete/', views.EventCategoryDeleteView.as_view(), name='category_delete'),
    ])),
    
    # Events
    path('events/', include([
        path('', views.EventListView.as_view(), name='event_list'),
        path('create/', views.EventCreateView.as_view(), name='event_create'),
        path('<uuid:pk>/', include([
            path('', views.EventDetailView.as_view(), name='event_detail'),
            path('update/', views.EventUpdateView.as_view(), name='event_update'),
            path('delete/', views.EventDeleteView.as_view(), name='event_delete'),
        ])),
    ])),
    
    # Registrations
    path('registrations/', include([
        path('', views.EventRegistrationListView.as_view(), name='registration_list'),
        path('create/', views.EventRegistrationCreateView.as_view(), name='registration_create'),
        path('<uuid:pk>/', include([
            path('update/', views.EventRegistrationUpdateView.as_view(), name='registration_update'),
            path('delete/', views.EventRegistrationDeleteView.as_view(), name='registration_delete'),
        ])),
    ])),
]
