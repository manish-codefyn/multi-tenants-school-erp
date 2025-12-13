# apps/students/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
import csv

from .models import Student, Guardian, StudentAddress, StudentDocument
from .forms import StudentForm, GuardianForm, StudentDocumentForm, StudentFilterForm


class StudentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Template view for student list"""
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    permission_required = 'students.view_student'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Student.objects.filter(tenant=self.request.tenant)
        
        # Apply filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(admission_number__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(personal_email__icontains=search)
            )
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        class_id = self.request.GET.get('class_id')
        if class_id:
            queryset = queryset.filter(current_class_id=class_id)
        
        return queryset.select_related('current_class', 'section', 'academic_year')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Student.STATUS_CHOICES
        
        # Add filter form
        context['filter_form'] = StudentFilterForm(tenant=self.request.tenant)
        
        # Add classes for filter dropdown
        from apps.academics.models import SchoolClass
        context['classes'] = SchoolClass.objects.filter(tenant=self.request.tenant)
        
        return context


class StudentDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Template view for student detail"""
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'
    permission_required = 'students.view_student'
    
    def get_queryset(self):
        return Student.objects.filter(tenant=self.request.tenant)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object
        
        # Add related data
        context['guardians'] = student.guardians.all()
        context['addresses'] = student.addresses.all()
        context['documents'] = student.documents.all()
        context['medical_info'] = getattr(student, 'medical_info', None)
        context['identification'] = getattr(student, 'identification', None)
        context['academic_history'] = student.academic_history.all()
        
        return context


class StudentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Template view for creating student"""
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    permission_required = 'students.add_student'
    success_url = reverse_lazy('students:student_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.tenant
        return kwargs
    
    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        response = super().form_valid(form)
        
        # Create related records if needed
        if form.cleaned_data.get('create_guardian'):
            # Create primary guardian (you can add logic here)
            pass
        
        # Create user account if requested
        if form.cleaned_data.get('create_user_account'):
            self.object.create_user_account()
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add New Student')
        return context


class StudentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Template view for updating student"""
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    permission_required = 'students.change_student'
    success_url = reverse_lazy('students:student_list')
    
    def get_queryset(self):
        return Student.objects.filter(tenant=self.request.tenant)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.tenant
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Student')
        return context


class StudentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Template view for deleting student"""
    model = Student
    template_name = 'students/student_confirm_delete.html'
    permission_required = 'students.delete_student'
    success_url = reverse_lazy('students:student_list')
    
    def get_queryset(self):
        return Student.objects.filter(tenant=self.request.tenant)


class StudentDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Dashboard view for students"""
    template_name = 'students/dashboard.html'
    permission_required = 'students.view_student_dashboard'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        
        # Get statistics
        students = Student.objects.filter(tenant=tenant)
        
        context['total_students'] = students.count()
        context['active_students'] = students.filter(status='ACTIVE').count()
        context['inactive_students'] = students.filter(status='INACTIVE').count()
        context['graduated_students'] = students.filter(status='GRADUATED').count()
        
        # Class distribution
        from apps.academics.models import SchoolClass
        class_stats = []
        for school_class in SchoolClass.objects.filter(tenant=tenant):
            class_stats.append({
                'name': school_class.name,
                'count': students.filter(current_class=school_class).count()
            })
        context['class_stats'] = class_stats
        
        # Gender distribution
        gender_stats = students.values('gender').annotate(count=models.Count('id'))
        context['gender_stats'] = list(gender_stats)
        
        return context


class StudentExportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Export student data"""
    permission_required = 'students.export_student_data'
    
    def get(self, request, *args, **kwargs):
        # Get all students for current tenant
        students = Student.objects.filter(tenant=request.tenant)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="students_export.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Admission Number', 'Roll Number', 'Full Name',
            'Date of Birth', 'Gender', 'Email', 'Phone',
            'Class', 'Section', 'Status', 'Category'
        ])
        
        # Write data
        for student in students:
            writer.writerow([
                student.admission_number,
                student.roll_number or '',
                student.full_name,
                student.date_of_birth,
                student.get_gender_display(),
                student.personal_email,
                student.mobile_primary,
                student.current_class.name if student.current_class else '',
                student.section.name if student.section else '',
                student.get_status_display(),
                student.get_category_display()
            ])
        
        return response


class GuardianCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create guardian for student"""
    model = Guardian
    form_class = GuardianForm
    template_name = 'students/guardian_form.html'
    permission_required = 'students.add_student'
    
    def get_success_url(self):
        return reverse_lazy('students:student_detail', kwargs={'pk': self.kwargs['student_id']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = get_object_or_404(Student, id=self.kwargs['student_id'], tenant=self.request.tenant)
        return context
    
    def form_valid(self, form):
        student = get_object_or_404(Student, id=self.kwargs['student_id'], tenant=self.request.tenant)
        form.instance.student = student
        form.instance.tenant = self.request.tenant
        return super().form_valid(form)


class DocumentUploadView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Upload document for student"""
    model = StudentDocument
    form_class = StudentDocumentForm
    template_name = 'students/document_form.html'
    permission_required = 'students.add_student'
    
    def get_success_url(self):
        return reverse_lazy('students:student_detail', kwargs={'pk': self.kwargs['student_id']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = get_object_or_404(Student, id=self.kwargs['student_id'], tenant=self.request.tenant)
        return context
    
    def form_valid(self, form):
        student = get_object_or_404(Student, id=self.kwargs['student_id'], tenant=self.request.tenant)
        form.instance.student = student
        form.instance.tenant = self.request.tenant
        return super().form_valid(form)