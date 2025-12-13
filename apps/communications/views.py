from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.db.models import Q
from .models import Communication, CommunicationChannel
from apps.core.utils.tenant import get_current_tenant
from apps.students.models import Student
from apps.hr.models import Department, Staff
from apps.academics.models import AcademicYear

class CommunicationDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'communications/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        # Stats
        context['total_students'] = Student.objects.filter(
            tenant=tenant, 
            status='ACTIVE'
        ).count()
        
        context['total_teachers'] = Staff.objects.filter(
            tenant=tenant,
            employment_status='ACTIVE',
            designation__category='TEACHING'
        ).count()
        
        context['departments'] = Department.objects.filter(tenant=tenant)
        
        context['current_academic_year'] = AcademicYear.objects.filter(
            tenant=tenant,
            is_current=True
        ).first()
        
        # Feature flags (simplified for now)
        context['show_financial_data'] = True
        context['show_student_management'] = True
        
        return context

class MessageListView(LoginRequiredMixin, ListView):
    model = Communication
    template_name = 'communications/message_list.html'
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        folder = self.request.GET.get('folder', 'inbox')
        
        queryset = Communication.objects.filter(tenant=get_current_tenant())
        
        if folder == 'inbox':
            # For now, assuming inbox means messages where the user is the recipient
            # This logic might need adjustment based on how GenericForeignKey is handled for User
            # But for simplicity, let's assume we filter by recipient_id if it matches user.id
            queryset = queryset.filter(recipient_id=user.id)
        elif folder == 'sent':
            queryset = queryset.filter(sender=user)
        elif folder == 'drafts':
            queryset = queryset.filter(sender=user, status='DRAFT')
            
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['folder'] = self.request.GET.get('folder', 'inbox')
        return context

class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Communication
    template_name = 'communications/message_detail.html'
    context_object_name = 'message'

    def get_queryset(self):
        # Ensure user can only see their own messages
        user = self.request.user
        return Communication.objects.filter(
            Q(sender=user) | Q(recipient_id=user.id),
            tenant=get_current_tenant()
        )
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Mark as read if user is recipient
        if obj.recipient_id == self.request.user.id and not obj.read_at:
            obj.mark_as_read()
        return obj

class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Communication
    template_name = 'communications/message_compose.html'
    fields = ['recipient_id', 'subject', 'content', 'priority'] # Simplified fields
    success_url = reverse_lazy('communications:messages')

    def form_valid(self, form):
        form.instance.sender = self.request.user
        form.instance.tenant = get_current_tenant()
        # Set default channel for now, or handle it in form
        # form.instance.channel = ... 
        return super().form_valid(form)

class ParentMessageListView(LoginRequiredMixin, ListView):
    model = Communication
    template_name = 'communications/parent_message_list.html'
    context_object_name = 'messages'
    
    def get_queryset(self):
        # Placeholder for parent messages
        return Communication.objects.none()
