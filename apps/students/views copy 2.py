from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count
from apps.core.permissions.mixins import PermissionRequiredMixin
from apps.core.utils.tenant import get_current_tenant
from .models import Student

class StudentDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'students/dashboard.html'
    permission_required = 'students.view_student'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['total_students'] = Student.objects.filter(tenant=tenant).count()
        context['active_students'] = Student.objects.filter(tenant=tenant, status='ACTIVE').count()
        context['alumni'] = Student.objects.filter(tenant=tenant, status='ALUMNI').count()
        context['suspended'] = Student.objects.filter(tenant=tenant, status='SUSPENDED').count()
        
        return context

# ==================== STUDENT ====================

class StudentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    permission_required = 'students.view_student'

class StudentDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'
    permission_required = 'students.view_student'

class StudentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Student
    fields = ['admission_number', 'roll_number', 'first_name', 'middle_name', 'last_name', 
              'date_of_birth', 'gender', 'blood_group', 'nationality', 'personal_email', 
              'mobile_primary', 'status']
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:student_list')
    permission_required = 'students.add_student'

    def form_valid(self, form):
        messages.success(self.request, "Student created successfully.")
        return super().form_valid(form)

class StudentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Student
    fields = ['admission_number', 'roll_number', 'first_name', 'middle_name', 'last_name', 
              'date_of_birth', 'gender', 'blood_group', 'nationality', 'personal_email', 
              'mobile_number', 'status']
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:student_list')
    permission_required = 'students.change_student'

    def form_valid(self, form):
        messages.success(self.request, "Student updated successfully.")
        return super().form_valid(form)

class StudentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Student
    template_name = 'students/confirm_delete.html'
    success_url = reverse_lazy('students:student_list')
    permission_required = 'students.delete_student'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Student deleted successfully.")
        return super().delete(request, *args, **kwargs)
