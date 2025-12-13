from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from apps.core.utils.tenant import get_current_tenant
from apps.core.permissions.mixins import PermissionRequiredMixin
from .models import (
    TimeTable, Attendance, ClassSubject, StudyMaterial, 
    SchoolClass, Section, AcademicYear, Term, Subject
)

# ==================== DASHBOARDS ====================
class TeacherDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'academics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        user = self.request.user
        today = timezone.now().date()
        
        # Add today's date to context
        context['today'] = today
        
        # Get today's schedule
        context['todays_schedule'] = TimeTable.objects.filter(
            teacher=user,
            day=today.strftime('%A').upper()
        ).select_related('subject', 'class_name', 'section').order_by('start_time')
        
        # Get classes where teacher is class teacher
        context['my_classes'] = SchoolClass.objects.filter(
            class_teacher=user,
            is_active=True
        )
        
        # Get subjects taught by teacher - using correct field name 'class_name'
        context['my_subjects'] = ClassSubject.objects.filter(
            teacher=user,
            academic_year__is_current=True
        ).select_related('class_name', 'subject', 'academic_year')
        
        context['tenant'] = tenant
        return context

# ==================== ACADEMIC YEAR MANAGEMENT ====================

class AcademicYearListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = AcademicYear
    template_name = 'academics/academic_year_list.html'
    context_object_name = 'academic_years'
    permission_required = 'academics.view_academicyear'

class AcademicYearCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = AcademicYear
    fields = ['name', 'code', 'start_date', 'end_date', 'is_current', 'has_terms']
    template_name = 'academics/academic_year_form.html'
    success_url = reverse_lazy('academics:academic_year_list')
    permission_required = 'academics.add_academicyear'

    def form_valid(self, form):
        messages.success(self.request, "Academic Year created successfully.")
        return super().form_valid(form)

class AcademicYearUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = AcademicYear
    fields = ['name', 'code', 'start_date', 'end_date', 'is_current', 'has_terms']
    template_name = 'academics/academic_year_form.html'
    success_url = reverse_lazy('academics:academic_year_list')
    permission_required = 'academics.change_academicyear'

    def form_valid(self, form):
        messages.success(self.request, "Academic Year updated successfully.")
        return super().form_valid(form)

class AcademicYearDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = AcademicYear
    template_name = 'academics/confirm_delete.html'
    success_url = reverse_lazy('academics:academic_year_list')
    permission_required = 'academics.delete_academicyear'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Academic Year deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== TERM MANAGEMENT ====================

class TermListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Term
    template_name = 'academics/term_list.html'
    context_object_name = 'terms'
    permission_required = 'academics.view_term'

class TermCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Term
    fields = ['academic_year', 'name', 'term_type', 'order', 'start_date', 'end_date', 'is_current']
    template_name = 'academics/term_form.html'
    success_url = reverse_lazy('academics:term_list')
    permission_required = 'academics.add_term'

    def form_valid(self, form):
        messages.success(self.request, "Term created successfully.")
        return super().form_valid(form)

class TermUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Term
    fields = ['academic_year', 'name', 'term_type', 'order', 'start_date', 'end_date', 'is_current']
    template_name = 'academics/term_form.html'
    success_url = reverse_lazy('academics:term_list')
    permission_required = 'academics.change_term'

    def form_valid(self, form):
        messages.success(self.request, "Term updated successfully.")
        return super().form_valid(form)

class TermDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Term
    template_name = 'academics/confirm_delete.html'
    success_url = reverse_lazy('academics:term_list')
    permission_required = 'academics.delete_term'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Term deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== CLASS MANAGEMENT ====================

class SchoolClassListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = SchoolClass
    template_name = 'academics/class_list.html'
    context_object_name = 'classes'
    permission_required = 'academics.view_schoolclass'

class SchoolClassCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SchoolClass
    fields = ['name', 'numeric_name', 'code', 'level', 'order', 'class_teacher', 'max_strength', 'tuition_fee', 'is_active']
    template_name = 'academics/class_form.html'
    success_url = reverse_lazy('academics:class_list')
    permission_required = 'academics.add_schoolclass'

    def form_valid(self, form):
        messages.success(self.request, "Class created successfully.")
        return super().form_valid(form)

class SchoolClassUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SchoolClass
    fields = ['name', 'numeric_name', 'code', 'level', 'order', 'class_teacher', 'max_strength', 'tuition_fee', 'is_active']
    template_name = 'academics/class_form.html'
    success_url = reverse_lazy('academics:class_list')
    permission_required = 'academics.change_schoolclass'

    def form_valid(self, form):
        messages.success(self.request, "Class updated successfully.")
        return super().form_valid(form)

class SchoolClassDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = SchoolClass
    template_name = 'academics/confirm_delete.html'
    success_url = reverse_lazy('academics:class_list')
    permission_required = 'academics.delete_schoolclass'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Class deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== SECTION MANAGEMENT ====================

class SectionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Section
    template_name = 'academics/section_list.html'
    context_object_name = 'sections'
    permission_required = 'academics.view_section'

class SectionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Section
    fields = ['class_name', 'name', 'code', 'section_incharge', 'max_strength', 'room_number', 'is_active']
    template_name = 'academics/section_form.html'
    success_url = reverse_lazy('academics:section_list')
    permission_required = 'academics.add_section'

    def form_valid(self, form):
        messages.success(self.request, "Section created successfully.")
        return super().form_valid(form)

class SectionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Section
    fields = ['class_name', 'name', 'code', 'section_incharge', 'max_strength', 'room_number', 'is_active']
    template_name = 'academics/section_form.html'
    success_url = reverse_lazy('academics:section_list')
    permission_required = 'academics.change_section'

    def form_valid(self, form):
        messages.success(self.request, "Section updated successfully.")
        return super().form_valid(form)

class SectionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Section
    template_name = 'academics/confirm_delete.html'
    success_url = reverse_lazy('academics:section_list')
    permission_required = 'academics.delete_section'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Section deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== SUBJECT MANAGEMENT ====================

class SubjectListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Subject
    template_name = 'academics/subject_list.html'
    context_object_name = 'subjects'
    permission_required = 'academics.view_subject'

class SubjectCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Subject
    fields = ['name', 'code', 'subject_type', 'subject_group', 'description', 'has_practical', 'has_project', 'is_scoring', 'credit_hours', 'max_marks', 'pass_marks', 'is_active']
    template_name = 'academics/subject_form.html'
    success_url = reverse_lazy('academics:subject_list')
    permission_required = 'academics.add_subject'

    def form_valid(self, form):
        messages.success(self.request, "Subject created successfully.")
        return super().form_valid(form)

class SubjectUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Subject
    fields = ['name', 'code', 'subject_type', 'subject_group', 'description', 'has_practical', 'has_project', 'is_scoring', 'credit_hours', 'max_marks', 'pass_marks', 'is_active']
    template_name = 'academics/subject_form.html'
    success_url = reverse_lazy('academics:subject_list')
    permission_required = 'academics.change_subject'

    def form_valid(self, form):
        messages.success(self.request, "Subject updated successfully.")
        return super().form_valid(form)

class SubjectDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Subject
    template_name = 'academics/confirm_delete.html'
    success_url = reverse_lazy('academics:subject_list')
    permission_required = 'academics.delete_subject'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Subject deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ==================== TEACHER & STUDENT VIEWS ====================

class ScheduleView(LoginRequiredMixin, ListView):
    model = TimeTable
    template_name = 'academics/schedule.html'
    context_object_name = 'schedule_entries'

    def get_queryset(self):
        user = self.request.user
        return TimeTable.objects.filter(
            teacher=user
        ).order_by('day', 'start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Group by day for easier template rendering
        schedule_by_day = {}
        days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
        
        for day in days:
            entries = self.get_queryset().filter(day=day)
            if entries.exists():
                schedule_by_day[day] = entries
                
        context['schedule_by_day'] = schedule_by_day
        context['days'] = days
        return context

class AttendanceView(LoginRequiredMixin, TemplateView):
    template_name = 'academics/attendance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Classes where user is class teacher or subject teacher
        context['classes'] = SchoolClass.objects.filter(
            class_teacher=user,
            is_active=True
        )
        
        return context

class GradingView(LoginRequiredMixin, TemplateView):
    template_name = 'academics/grading.html'

class AssignmentsView(LoginRequiredMixin, TemplateView):
    template_name = 'academics/assignments.html'

class StudentCoursesView(LoginRequiredMixin, ListView):
    model = ClassSubject
    template_name = 'academics/student_courses.html'
    context_object_name = 'courses'

    def get_queryset(self):
        # Assuming student is linked to a user
        # This logic needs to be adjusted based on how Student model is linked to User
        # For now returning empty or based on student profile if available
        if hasattr(self.request.user, 'student_profile'):
            student = self.request.user.student_profile
            return ClassSubject.objects.filter(
                class_name=student.current_class,
                academic_year__is_current=True
            )
        return ClassSubject.objects.none()

class StudentGradesView(LoginRequiredMixin, TemplateView):
    template_name = 'academics/student_grades.html'

class StudentAttendanceView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = 'academics/student_attendance.html'
    context_object_name = 'attendance_records'

    def get_queryset(self):
        if hasattr(self.request.user, 'student_profile'):
            return Attendance.objects.filter(
                student=self.request.user.student_profile
            ).order_by('-date')
        return Attendance.objects.none()

class StudentAssignmentsView(LoginRequiredMixin, TemplateView):
    template_name = 'academics/student_assignments.html'

class TimetableView(LoginRequiredMixin, TemplateView):
    template_name = 'academics/timetable.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'student_profile'):
            student = self.request.user.student_profile
            context['timetable'] = TimeTable.objects.filter(
                class_name=student.current_class,
                section=student.section
            ).order_by('day', 'start_time')
        return context
