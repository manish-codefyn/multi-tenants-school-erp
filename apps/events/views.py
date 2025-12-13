from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from apps.core.permissions.mixins import PermissionRequiredMixin
from apps.core.utils.tenant import get_current_tenant
from .models import Event, EventCategory, EventRegistration

class EventDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'events/dashboard.html'
    permission_required = 'events.view_event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['total_events'] = Event.objects.filter(tenant=tenant).count()
        context['upcoming_events'] = Event.objects.filter(tenant=tenant, status='SCHEDULED').count()
        context['ongoing_events'] = Event.objects.filter(tenant=tenant, status='ONGOING').count()
        context['event_categories'] = EventCategory.objects.filter(tenant=tenant, is_active=True).count()
        
        return context

# ==================== EVENT CATEGORY ====================

class EventCategoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = EventCategory
    template_name = 'events/category_list.html'
    context_object_name = 'categories'
    permission_required = 'events.view_eventcategory'

class EventCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = EventCategory
    fields = ['name', 'code', 'description', 'color', 'icon', 'is_active']
    template_name = 'events/category_form.html'
    success_url = reverse_lazy('events:category_list')
    permission_required = 'events.add_eventcategory'

    def form_valid(self, form):
        messages.success(self.request, "Event Category created successfully.")
        return super().form_valid(form)

class EventCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = EventCategory
    fields = ['name', 'code', 'description', 'color', 'icon', 'is_active']
    template_name = 'events/category_form.html'
    success_url = reverse_lazy('events:category_list')
    permission_required = 'events.change_eventcategory'

    def form_valid(self, form):
        messages.success(self.request, "Event Category updated successfully.")
        return super().form_valid(form)

class EventCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = EventCategory
    template_name = 'events/confirm_delete.html'
    success_url = reverse_lazy('events:category_list')
    permission_required = 'events.delete_eventcategory'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Event Category deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== EVENT ====================

class EventListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    permission_required = 'events.view_event'

class EventDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'
    permission_required = 'events.view_event'

class EventCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Event
    fields = ['title', 'code', 'category', 'description', 'event_type', 'start_date', 
              'end_date', 'start_time', 'end_time', 'venue', 'max_participants', 
              'registration_required', 'registration_deadline', 'status', 'is_public']
    template_name = 'events/event_form.html'
    success_url = reverse_lazy('events:event_list')
    permission_required = 'events.add_event'

    def form_valid(self, form):
        messages.success(self.request, "Event created successfully.")
        return super().form_valid(form)

class EventUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Event
    fields = ['title', 'code', 'category', 'description', 'event_type', 'start_date', 
              'end_date', 'start_time', 'end_time', 'venue', 'max_participants', 
              'registration_required', 'registration_deadline', 'status', 'is_public']
    template_name = 'events/event_form.html'
    success_url = reverse_lazy('events:event_list')
    permission_required = 'events.change_event'

    def form_valid(self, form):
        messages.success(self.request, "Event updated successfully.")
        return super().form_valid(form)

class EventDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Event
    template_name = 'events/confirm_delete.html'
    success_url = reverse_lazy('events:event_list')
    permission_required = 'events.delete_event'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Event deleted successfully.")
        return super().delete(request, *args, **kwargs)
