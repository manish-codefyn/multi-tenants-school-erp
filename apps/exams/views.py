from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from apps.core.permissions.mixins import PermissionRequiredMixin
from apps.core.utils.tenant import get_current_tenant
from .models import ExamType, Exam, ExamSubject, GradingSystem, Grade, ExamResult

class ExamDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'exams/dashboard.html'
    permission_required = 'exams.view_exam'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['total_exams'] = Exam.objects.filter(tenant=tenant).count()
        context['ongoing_exams'] = Exam.objects.filter(tenant=tenant, status='ONGOING').count()
        context['upcoming_exams'] = Exam.objects.filter(tenant=tenant, status='SCHEDULED').count()
        context['exam_types'] = ExamType.objects.filter(tenant=tenant, is_active=True).count()
        
        return context

# ==================== EXAM TYPE ====================

class ExamTypeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ExamType
    template_name = 'exams/exam_type_list.html'
    context_object_name = 'exam_types'
    permission_required = 'exams.view_examtype'

class ExamTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ExamType
    fields = ['name', 'code', 'description', 'weightage', 'is_final', 'order', 'is_active']
    template_name = 'exams/exam_type_form.html'
    success_url = reverse_lazy('exams:exam_type_list')
    permission_required = 'exams.add_examtype'

    def form_valid(self, form):
        messages.success(self.request, "Exam Type created successfully.")
        return super().form_valid(form)

class ExamTypeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ExamType
    fields = ['name', 'code', 'description', 'weightage', 'is_final', 'order', 'is_active']
    template_name = 'exams/exam_type_form.html'
    success_url = reverse_lazy('exams:exam_type_list')
    permission_required = 'exams.change_examtype'

    def form_valid(self, form):
        messages.success(self.request, "Exam Type updated successfully.")
        return super().form_valid(form)

class ExamTypeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ExamType
    template_name = 'exams/confirm_delete.html'
    success_url = reverse_lazy('exams:exam_type_list')
    permission_required = 'exams.delete_examtype'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Exam Type deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== EXAM ====================

class ExamListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Exam
    template_name = 'exams/exam_list.html'
    context_object_name = 'exams'
    permission_required = 'exams.view_exam'

class ExamDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Exam
    template_name = 'exams/exam_detail.html'
    context_object_name = 'exam'
    permission_required = 'exams.view_exam'

class ExamCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Exam
    fields = ['name', 'code', 'exam_type', 'academic_year', 'class_name', 'start_date', 
              'end_date', 'exam_mode', 'total_marks', 'pass_percentage', 'grace_marks', 
              'status', 'instructions', 'is_published']
    template_name = 'exams/exam_form.html'
    success_url = reverse_lazy('exams:exam_list')
    permission_required = 'exams.add_exam'

    def form_valid(self, form):
        messages.success(self.request, "Exam created successfully.")
        return super().form_valid(form)

class ExamUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Exam
    fields = ['name', 'code', 'exam_type', 'academic_year', 'class_name', 'start_date', 
              'end_date', 'exam_mode', 'total_marks', 'pass_percentage', 'grace_marks', 
              'status', 'instructions', 'is_published']
    template_name = 'exams/exam_form.html'
    success_url = reverse_lazy('exams:exam_list')
    permission_required = 'exams.change_exam'

    def form_valid(self, form):
        messages.success(self.request, "Exam updated successfully.")
        return super().form_valid(form)

class ExamDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Exam
    template_name = 'exams/confirm_delete.html'
    success_url = reverse_lazy('exams:exam_list')
    permission_required = 'exams.delete_exam'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Exam deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== GRADING SYSTEM ====================

class GradingSystemListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = GradingSystem
    template_name = 'exams/grading_system_list.html'
    context_object_name = 'grading_systems'
    permission_required = 'exams.view_gradingsystem'

class GradingSystemCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = GradingSystem
    fields = ['name', 'code', 'description', 'is_active', 'is_default']
    template_name = 'exams/grading_system_form.html'
    success_url = reverse_lazy('exams:grading_system_list')
    permission_required = 'exams.add_gradingsystem'

    def form_valid(self, form):
        messages.success(self.request, "Grading System created successfully.")
        return super().form_valid(form)

class GradingSystemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = GradingSystem
    fields = ['name', 'code', 'description', 'is_active', 'is_default']
    template_name = 'exams/grading_system_form.html'
    success_url = reverse_lazy('exams:grading_system_list')
    permission_required = 'exams.change_gradingsystem'

    def form_valid(self, form):
        messages.success(self.request, "Grading System updated successfully.")
        return super().form_valid(form)

class GradingSystemDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = GradingSystem
    template_name = 'exams/confirm_delete.html'
    success_url = reverse_lazy('exams:grading_system_list')
    permission_required = 'exams.delete_gradingsystem'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Grading System deleted successfully.")
        return super().delete(request, *args, **kwargs)
