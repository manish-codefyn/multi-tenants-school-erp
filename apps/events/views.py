import logging
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q

from apps.core.views import (
    BaseView, BaseListView, BaseDetailView, BaseCreateView, 
    BaseUpdateView, BaseDeleteView, BaseTemplateView
)
from apps.core.utils.tenant import get_current_tenant
from apps.core.utils.audit import audit_log

from .models import Event, EventCategory, EventRegistration, EventDocument
from .forms import EventForm, EventCategoryForm, EventRegistrationForm, EventDocumentForm

logger = logging.getLogger(__name__)

class EventDashboardView(BaseTemplateView):
    template_name = 'events/dashboard.html'
    permission_required = 'events.view_event'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        today = timezone.now().date()
        
        # Event Statistics
        event_queryset = Event.objects.filter(tenant=tenant)
        context['total_events'] = event_queryset.count()
        context['upcoming_events'] = event_queryset.filter(start_date__gt=today).count()
        context['ongoing_events'] = event_queryset.filter(start_date__lte=today, end_date__gte=today).count()
        context['completed_events'] = event_queryset.filter(end_date__lt=today).count()
        
        # Category Statistics
        context['categories'] = EventCategory.objects.filter(tenant=tenant).annotate(
            event_count=Count('events')
        )
        
        # Recent Activity
        context['recent_events'] = event_queryset.order_by('-created_at')[:5]
        context['recent_registrations'] = EventRegistration.objects.filter(tenant=tenant).order_by('-registration_date')[:5]
        
        return context

# ==================== EVENT CATEGORY VIEWS ====================

class EventCategoryListView(BaseListView):
    model = EventCategory
    template_name = 'events/category/list.html'
    context_object_name = 'categories'
    permission_required = 'events.view_eventcategory'

class EventCategoryCreateView(BaseCreateView):
    model = EventCategory
    form_class = EventCategoryForm
    template_name = 'events/category/form.html'
    permission_required = 'events.add_eventcategory'
    success_url = reverse_lazy('events:category_list')

class EventCategoryUpdateView(BaseUpdateView):
    model = EventCategory
    form_class = EventCategoryForm
    template_name = 'events/category/form.html'
    permission_required = 'events.change_eventcategory'
    success_url = reverse_lazy('events:category_list')

class EventCategoryDeleteView(BaseDeleteView):
    model = EventCategory
    template_name = 'events/common/confirm_delete.html'
    permission_required = 'events.delete_eventcategory'
    success_url = reverse_lazy('events:category_list')

# ==================== EVENT VIEWS ====================

class EventListView(BaseListView):
    model = Event
    template_name = 'events/event/list.html'
    context_object_name = 'events'
    permission_required = 'events.view_event'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('category', 'academic_year')
        
        # Apply filters
        event_type = self.request.GET.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
            
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
            
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(venue__icontains=search) |
                Q(organizer_name__icontains=search)
            )
            
        return queryset

class EventDetailView(BaseDetailView):
    model = Event
    template_name = 'events/event/detail.html'
    context_object_name = 'event'
    permission_required = 'events.view_event'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        context['registrations'] = event.registrations.all().select_related('student', 'user')[:10]
        context['documents'] = event.documents.all()
        return context

class EventCreateView(BaseCreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event/form.html'
    permission_required = 'events.add_event'
    success_url = reverse_lazy('events:event_list')

class EventUpdateView(BaseUpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event/form.html'
    permission_required = 'events.change_event'
    success_url = reverse_lazy('events:event_list')

class EventDeleteView(BaseDeleteView):
    model = Event
    template_name = 'events/common/confirm_delete.html'
    permission_required = 'events.delete_event'
    success_url = reverse_lazy('events:event_list')

# ==================== REGISTRATION VIEWS ====================

class EventRegistrationListView(BaseListView):
    model = EventRegistration
    template_name = 'events/registration/list.html'
    context_object_name = 'registrations'
    permission_required = 'events.view_eventregistration'
    
    def get_queryset(self):
        return super().get_queryset().select_related('event', 'student', 'user')

class EventRegistrationCreateView(BaseCreateView):
    model = EventRegistration
    form_class = EventRegistrationForm
    template_name = 'events/registration/form.html'
    permission_required = 'events.add_eventregistration'
    success_url = reverse_lazy('events:registration_list')

class EventRegistrationUpdateView(BaseUpdateView):
    model = EventRegistration
    form_class = EventRegistrationForm
    template_name = 'events/registration/form.html'
    permission_required = 'events.change_eventregistration'
    success_url = reverse_lazy('events:registration_list')

class EventRegistrationDeleteView(BaseDeleteView):
    model = EventRegistration
    template_name = 'events/common/confirm_delete.html'
    permission_required = 'events.delete_eventregistration'
    success_url = reverse_lazy('events:registration_list')
