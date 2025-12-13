from django.urls import path
from . import views

app_name = 'communications'

urlpatterns = [
    path('dashboard/', views.CommunicationDashboardView.as_view(), name='dashboard'),
    path('messages/', views.MessageListView.as_view(), name='messages'),
    path('messages/<uuid:pk>/', views.MessageDetailView.as_view(), name='message_detail'),
    path('messages/compose/', views.MessageCreateView.as_view(), name='message_compose'),
    path('parent/messages/', views.ParentMessageListView.as_view(), name='parent_messages'),
]
