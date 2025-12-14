# apps/academics/views.py
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import PermissionDenied
import json
import csv
from datetime import datetime, timedelta

from apps.core.permissions.mixins import PermissionRequiredMixin, RoleRequiredMixin, TenantAccessMixin
from apps.core.utils.tenant import get_current_tenant
from apps.core.utils.audit import audit_log

from .models import (
    AcademicYear, Term, SchoolClass, Section, House, HousePoints,
    Subject, ClassSubject, TimeTable, StudentAttendance, Holiday,
    StudyMaterial, Syllabus, Stream, ClassTeacher
)
from .forms import (
    AcademicYearForm, TermForm, SchoolClassForm, SectionForm, HouseForm,
    HousePointsForm, SubjectForm, ClassSubjectForm, TimeTableForm,
    AttendanceForm, BulkAttendanceForm, HolidayForm, StudyMaterialForm,
    SyllabusForm, StreamForm, ClassTeacherForm
)
from apps.core.services.audit_service import AuditService


class AcademicsDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """Academics Dashboard"""
    template_name = 'academics/dashboard.html'
    permission_required = 'academics.view_dashboard'
    roles_required = ['admin', 'principal', 'academic_head', 'teacher']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        today = timezone.now().date()
        
        # Get current academic year and term
        try:
            current_year = AcademicYear.objects.get(tenant=tenant, is_current=True)
            context['current_year'] = current_year
            
            # Get current term
            current_term = Term.objects.filter(
                tenant=tenant,
                academic_year=current_year,
                is_current=True
            ).first()
            context['current_term'] = current_term
            
        except AcademicYear.DoesNotExist:
            current_year = None
            current_term = None
        
        # Class Statistics
        classes = SchoolClass.objects.filter(tenant=tenant, is_active=True)
        context['total_classes'] = classes.count()
        
        # Class distribution by level
        level_stats = []
        for level_code, level_name in SchoolClass.CLASS_LEVEL_CHOICES:
            count = classes.filter(level=level_code).count()
            if count > 0:
                level_stats.append({
                    'level': level_name,
                    'count': count,
                    'color': self.get_level_color(level_code)
                })
        
        context['level_stats'] = level_stats
        
        # Student Statistics (assuming you have a Student model)
        try:
            from apps.students.models import Student
            total_students = Student.objects.filter(tenant=tenant, is_active=True).count()
            context['total_students'] = total_students
            
            # Today's StudentAttendance
            today_attendance = StudentAttendance.objects.filter(
                tenant=tenant,
                date=today
            )
            
            if today_attendance.exists():
                context['present_today'] = today_attendance.filter(
                    status__in=['PRESENT', 'LATE', 'HALF_DAY']
                ).count()
                context['absent_today'] = today_attendance.filter(status='ABSENT').count()
            else:
                context['present_today'] = 0
                context['absent_today'] = 0
                
        except ImportError:
            context['total_students'] = 0
            context['present_today'] = 0
            context['absent_today'] = 0
        
        # Teacher Statistics (assuming you have Staff model)
        try:
            from apps.hr.models import Staff
            total_teachers = Staff.objects.filter(
                tenant=tenant,
                is_active=True,
                user__role='teacher'
            ).count()
            context['total_teachers'] = total_teachers
        except ImportError:
            context['total_teachers'] = 0
        
        # Subject Statistics
        subjects = Subject.objects.filter(tenant=tenant, is_active=True)
        context['total_subjects'] = subjects.count()
        
        # Recent Activities
        context['recent_holidays'] = Holiday.objects.filter(
            tenant=tenant,
            end_date__gte=today
        ).order_by('start_date')[:5]
        
        context['recent_materials'] = StudyMaterial.objects.filter(
            tenant=tenant,
            is_published=True
        ).select_related('class_name', 'subject').order_by('-publish_date')[:5]
        
        # Upcoming Events
        next_week = today + timedelta(days=7)
        context['upcoming_holidays'] = Holiday.objects.filter(
            tenant=tenant,
            start_date__gte=today,
            start_date__lte=next_week
        ).order_by('start_date')[:5]
        
        # House Points Leaderboard
        houses = House.objects.filter(tenant=tenant).order_by('-total_points')[:5]
        context['house_leaderboard'] = houses
        
        # Audit Trail
        AuditService.create_audit_entry(
            action='READ',
            resource_type='Dashboard',
            user=self.request.user,
            request=self.request,
            resource_name='Academics Dashboard',
            details={'section': 'academics'}
        )

        return context
    
    def get_level_color(self, level):
        """Get color for class level"""
        colors = {
            'PRE_PRIMARY': 'primary',
            'PRIMARY': 'success',
            'MIDDLE': 'info',
            'HIGH': 'warning',
            'SENIOR': 'danger'
        }
        return colors.get(level, 'secondary')


# ==================== ACADEMIC YEAR VIEWS ====================

class AcademicYearListView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = AcademicYear
    template_name = 'academics/year/list.html'
    context_object_name = 'academic_years'
    permission_required = 'academics.view_academicyear'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('-start_date')


class AcademicYearDetailView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = AcademicYear
    template_name = 'academics/year/detail.html'
    context_object_name = 'academic_year'
    permission_required = 'academics.view_academicyear'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        academic_year = self.object
        
        # Get terms for this academic year
        context['terms'] = academic_year.terms.all().order_by('order')
        
        # Get holiday count
        context['holiday_count'] = academic_year.holidays.count()
        
        # Get class count for this year
        context['class_count'] = ClassSubject.objects.filter(
            academic_year=academic_year
        ).values('class_name').distinct().count()
        
        return context


class AcademicYearCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'academics/year/form.html'
    permission_required = 'academics.add_academicyear'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:year_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Set created_by and updated_by
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        
        # If setting as current year, update other years
        if form.instance.is_current:
            AcademicYear.objects.filter(
                tenant=get_current_tenant()
            ).exclude(id=form.instance.id).update(is_current=False)
        
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Academic Year '{form.instance.name}' created successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='CREATE_ACADEMIC_YEAR',
            resource='Academic Year',
            resource_id=str(self.object.id),
            details={'name': self.object.name, 'code': self.object.code},
            severity='INFO'
        )
        
        return response


class AcademicYearUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'academics/year/form.html'
    permission_required = 'academics.change_academicyear'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:year_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        
        # If setting as current year, update other years
        if form.instance.is_current:
            AcademicYear.objects.filter(
                tenant=get_current_tenant()
            ).exclude(id=form.instance.id).update(is_current=False)
        
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Academic Year '{form.instance.name}' updated successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='UPDATE_ACADEMIC_YEAR',
            resource='Academic Year',
            resource_id=str(self.object.id),
            details={'changes': form.changed_data},
            severity='INFO'
        )
        
        return response


class AcademicYearDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = AcademicYear
    template_name = 'academics/common/confirm_delete.html'
    permission_required = 'academics.delete_academicyear'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:year_list')
    
    def delete(self, request, *args, **kwargs):
        academic_year = self.get_object()
        
        # Check if academic year has dependencies
        if academic_year.terms.exists():
            messages.error(
                request,
                f"Cannot delete Academic Year '{academic_year.name}' because it has terms."
            )
            return JsonResponse({
                'success': False,
                'error': 'Academic year has terms'
            })
        
        if academic_year.holidays.exists():
            messages.error(
                request,
                f"Cannot delete Academic Year '{academic_year.name}' because it has holidays."
            )
            return JsonResponse({
                'success': False,
                'error': 'Academic year has holidays'
            })
        
        # Perform soft delete
        academic_year.delete(
            user=request.user,
            reason=request.POST.get('deletion_reason', 'No reason provided'),
            category=request.POST.get('deletion_category', 'ADMIN_ACTION')
        )
        
        messages.success(
            request,
            f"Academic Year '{academic_year.name}' has been deleted."
        )
        
        audit_log(
            user=request.user,
            action='DELETE_ACADEMIC_YEAR',
            resource='Academic Year',
            resource_id=str(academic_year.id),
            details={'name': academic_year.name, 'code': academic_year.code},
            severity='WARNING'
        )
        
        return JsonResponse({
            'success': True,
            'redirect': self.get_success_url()
        })


# ==================== TERM VIEWS ====================

class TermListView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = Term
    template_name = 'academics/term/list.html'
    context_object_name = 'terms'
    permission_required = 'academics.view_term'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by academic year if provided
        year_id = self.request.GET.get('academic_year')
        if year_id:
            queryset = queryset.filter(academic_year_id=year_id)
        
        return queryset.order_by('academic_year', 'order')


class TermCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Term
    form_class = TermForm
    template_name = 'academics/term/form.html'
    permission_required = 'academics.add_term'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:term_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        
        # If setting as current term, update other terms in same academic year
        if form.instance.is_current:
            Term.objects.filter(
                tenant=get_current_tenant(),
                academic_year=form.instance.academic_year
            ).exclude(id=form.instance.id).update(is_current=False)
        
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Term '{form.instance.name}' created successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='CREATE_TERM',
            resource='Term',
            resource_id=str(self.object.id),
            details={
                'name': self.object.name,
                'academic_year': str(self.object.academic_year)
            },
            severity='INFO'
        )
        
        return response


class TermUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = Term
    form_class = TermForm
    template_name = 'academics/term/form.html'
    permission_required = 'academics.change_term'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:term_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        
        # If setting as current term, update other terms in same academic year
        if form.instance.is_current:
            Term.objects.filter(
                tenant=get_current_tenant(),
                academic_year=form.instance.academic_year
            ).exclude(id=form.instance.id).update(is_current=False)
        
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Term '{form.instance.name}' updated successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='UPDATE_TERM',
            resource='Term',
            resource_id=str(self.object.id),
            details={'changes': form.changed_data},
            severity='INFO'
        )
        
        return response


class TermDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = Term
    template_name = 'academics/common/confirm_delete.html'
    permission_required = 'academics.delete_term'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:term_list')
    
    def delete(self, request, *args, **kwargs):
        term = self.get_object()
        
        # Check if term is current
        if term.is_current:
            messages.error(
                request,
                f"Cannot delete current term '{term.name}'."
            )
            return JsonResponse({
                'success': False,
                'error': 'Cannot delete current term'
            })
        
        # Perform soft delete
        term.delete(
            user=request.user,
            reason=request.POST.get('deletion_reason', 'No reason provided'),
            category=request.POST.get('deletion_category', 'ADMIN_ACTION')
        )
        
        messages.success(
            request,
            f"Term '{term.name}' has been deleted."
        )
        
        audit_log(
            user=request.user,
            action='DELETE_TERM',
            resource='Term',
            resource_id=str(term.id),
            details={'name': term.name},
            severity='WARNING'
        )
        
        return JsonResponse({
            'success': True,
            'redirect': self.get_success_url()
        })


# ==================== CLASS VIEWS ====================

class SchoolClassListView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = SchoolClass
    template_name = 'academics/class/list.html'
    context_object_name = 'classes'
    permission_required = 'academics.view_schoolclass'
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        
        # Filter by level if provided
        level = self.request.GET.get('level')
        if level and level != 'all':
            queryset = queryset.filter(level=level)
        
        return queryset.order_by('order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['levels'] = SchoolClass.CLASS_LEVEL_CHOICES
        context['current_level'] = self.request.GET.get('level', '')
        return context


class SchoolClassDetailView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = SchoolClass
    template_name = 'academics/class/detail.html'
    context_object_name = 'class_obj'
    permission_required = 'academics.view_schoolclass'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_obj = self.object
        
        # Get sections for this class
        context['sections'] = class_obj.sections.filter(is_active=True)
        
        # Get subjects for this class (current academic year)
        try:
            current_year = AcademicYear.objects.get(
                tenant=get_current_tenant(),
                is_current=True
            )
            context['subjects'] = ClassSubject.objects.filter(
                class_name=class_obj,
                academic_year=current_year
            ).select_related('subject', 'teacher')
        except AcademicYear.DoesNotExist:
            context['subjects'] = []
        
        # Get student count (if Student model exists)
        try:
            from apps.students.models import Student
            context['student_count'] = Student.objects.filter(
                class_name=class_obj,
                is_active=True
            ).count()
        except ImportError:
            context['student_count'] = 0
        
        return context


class SchoolClassCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SchoolClass
    form_class = SchoolClassForm
    template_name = 'academics/class/form.html'
    permission_required = 'academics.add_schoolclass'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:class_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Class '{form.instance.name}' created successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='CREATE_SCHOOL_CLASS',
            resource='School Class',
            resource_id=str(self.object.id),
            details={'name': self.object.name, 'code': self.object.code},
            severity='INFO'
        )
        
        return response


class SchoolClassUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = SchoolClass
    form_class = SchoolClassForm
    template_name = 'academics/class/form.html'
    permission_required = 'academics.change_schoolclass'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:class_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Class '{form.instance.name}' updated successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='UPDATE_SCHOOL_CLASS',
            resource='School Class',
            resource_id=str(self.object.id),
            details={'changes': form.changed_data},
            severity='INFO'
        )
        
        return response


class SchoolClassDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = SchoolClass
    template_name = 'academics/common/confirm_delete.html'
    permission_required = 'academics.delete_schoolclass'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:class_list')
    
    def delete(self, request, *args, **kwargs):
        class_obj = self.get_object()
        
        # Check if class has sections
        if class_obj.sections.exists():
            messages.error(
                request,
                f"Cannot delete class '{class_obj.name}' because it has sections."
            )
            return JsonResponse({
                'success': False,
                'error': 'Class has sections'
            })
        
        # Check if class has students (if Student model exists)
        try:
            from apps.students.models import Student
            if Student.objects.filter(class_name=class_obj).exists():
                messages.error(
                    request,
                    f"Cannot delete class '{class_obj.name}' because it has students."
                )
                return JsonResponse({
                    'success': False,
                    'error': 'Class has students'
                })
        except ImportError:
            pass
        
        # Perform soft delete
        class_obj.delete(
            user=request.user,
            reason=request.POST.get('deletion_reason', 'No reason provided'),
            category=request.POST.get('deletion_category', 'ADMIN_ACTION')
        )
        
        messages.success(
            request,
            f"Class '{class_obj.name}' has been deleted."
        )
        
        audit_log(
            user=request.user,
            action='DELETE_SCHOOL_CLASS',
            resource='School Class',
            resource_id=str(class_obj.id),
            details={'name': class_obj.name, 'code': class_obj.code},
            severity='WARNING'
        )
        
        return JsonResponse({
            'success': True,
            'redirect': self.get_success_url()
        })


# ==================== SECTION VIEWS ====================

class SectionListView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = Section
    template_name = 'academics/section/list.html'
    context_object_name = 'sections'
    permission_required = 'academics.view_section'
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        
        # Filter by class if provided
        class_id = self.request.GET.get('class_id')
        if class_id:
            queryset = queryset.filter(class_name_id=class_id)
        
        return queryset.order_by('class_name__order', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        context['classes'] = SchoolClass.objects.filter(tenant=tenant, is_active=True)
        return context


class SectionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Section
    form_class = SectionForm
    template_name = 'academics/section/form.html'
    permission_required = 'academics.add_section'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        
        # Pre-select class if provided
        class_id = self.request.GET.get('class_id')
        if class_id:
            try:
                class_obj = SchoolClass.objects.get(id=class_id, tenant=get_current_tenant())
                kwargs['initial'] = {'class_name': class_obj}
            except SchoolClass.DoesNotExist:
                pass
        
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:section_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Section '{form.instance.name}' created successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='CREATE_SECTION',
            resource='Section',
            resource_id=str(self.object.id),
            details={
                'name': self.object.name,
                'class': str(self.object.class_name)
            },
            severity='INFO'
        )
        
        return response


class SectionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = Section
    form_class = SectionForm
    template_name = 'academics/section/form.html'
    permission_required = 'academics.change_section'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:section_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Section '{form.instance.name}' updated successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='UPDATE_SECTION',
            resource='Section',
            resource_id=str(self.object.id),
            details={'changes': form.changed_data},
            severity='INFO'
        )
        
        return response


class SectionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = Section
    template_name = 'academics/common/confirm_delete.html'
    permission_required = 'academics.delete_section'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:section_list')
    
    def delete(self, request, *args, **kwargs):
        section = self.get_object()
        
        # Check if section has students (if Student model exists)
        try:
            from apps.students.models import Student
            if section.students.exists():
                messages.error(
                    request,
                    f"Cannot delete section '{section.name}' because it has students."
                )
                return JsonResponse({
                    'success': False,
                    'error': 'Section has students'
                })
        except ImportError:
            pass
        
        # Perform soft delete
        section.delete(
            user=request.user,
            reason=request.POST.get('deletion_reason', 'No reason provided'),
            category=request.POST.get('deletion_category', 'ADMIN_ACTION')
        )
        
        messages.success(
            request,
            f"Section '{section.name}' has been deleted."
        )
        
        audit_log(
            user=request.user,
            action='DELETE_SECTION',
            resource='Section',
            resource_id=str(section.id),
            details={'name': section.name, 'class': str(section.class_name)},
            severity='WARNING'
        )
        
        return JsonResponse({
            'success': True,
            'redirect': self.get_success_url()
        })


# ==================== SUBJECT VIEWS ====================

class SubjectListView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = Subject
    template_name = 'academics/subject/list.html'
    context_object_name = 'subjects'
    permission_required = 'academics.view_subject'
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        
        # Filter by subject type if provided
        subject_type = self.request.GET.get('subject_type')
        if subject_type and subject_type != 'all':
            queryset = queryset.filter(subject_type=subject_type)
        
        # Search
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subject_types'] = Subject.SUBJECT_TYPE_CHOICES
        context['current_type'] = self.request.GET.get('subject_type', '')
        context['search'] = self.request.GET.get('search', '')
        return context


class SubjectCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'academics/subject/form.html'
    permission_required = 'academics.add_subject'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:subject_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Subject '{form.instance.name}' created successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='CREATE_SUBJECT',
            resource='Subject',
            resource_id=str(self.object.id),
            details={'name': self.object.name, 'code': self.object.code},
            severity='INFO'
        )
        
        return response


class SubjectUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'academics/subject/form.html'
    permission_required = 'academics.change_subject'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:subject_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Subject '{form.instance.name}' updated successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='UPDATE_SUBJECT',
            resource='Subject',
            resource_id=str(self.object.id),
            details={'changes': form.changed_data},
            severity='INFO'
        )
        
        return response


class SubjectDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = Subject
    template_name = 'academics/common/confirm_delete.html'
    permission_required = 'academics.delete_subject'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:subject_list')
    
    def delete(self, request, *args, **kwargs):
        subject = self.get_object()
        
        # Check if subject is used in any class
        if subject.class_subjects.exists():
            messages.error(
                request,
                f"Cannot delete subject '{subject.name}' because it is assigned to classes."
            )
            return JsonResponse({
                'success': False,
                'error': 'Subject is assigned to classes'
            })
        
        # Perform soft delete
        subject.delete(
            user=request.user,
            reason=request.POST.get('deletion_reason', 'No reason provided'),
            category=request.POST.get('deletion_category', 'ADMIN_ACTION')
        )
        
        messages.success(
            request,
            f"Subject '{subject.name}' has been deleted."
        )
        
        audit_log(
            user=request.user,
            action='DELETE_SUBJECT',
            resource='Subject',
            resource_id=str(subject.id),
            details={'name': subject.name, 'code': subject.code},
            severity='WARNING'
        )
        
        return JsonResponse({
            'success': True,
            'redirect': self.get_success_url()
        })


# ==================== CLASS SUBJECT VIEWS ====================

class ClassSubjectListView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = ClassSubject
    template_name = 'academics/class_subject/list.html'
    context_object_name = 'class_subjects'
    permission_required = 'academics.view_classsubject'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by class if provided
        class_id = self.request.GET.get('class_id')
        if class_id:
            queryset = queryset.filter(class_name_id=class_id)
        
        # Filter by academic year if provided
        year_id = self.request.GET.get('academic_year')
        if year_id:
            queryset = queryset.filter(academic_year_id=year_id)
        
        return queryset.select_related('class_name', 'subject', 'teacher', 'academic_year').order_by('class_name__order', 'subject__name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        context['classes'] = SchoolClass.objects.filter(tenant=tenant, is_active=True)
        context['academic_years'] = AcademicYear.objects.filter(tenant=tenant)
        return context


class ClassSubjectCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ClassSubject
    form_class = ClassSubjectForm
    template_name = 'academics/class_subject/form.html'
    permission_required = 'academics.add_classsubject'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        
        # Pre-select class and academic year if provided
        class_id = self.request.GET.get('class_id')
        year_id = self.request.GET.get('academic_year')
        
        initial_data = {}
        
        if class_id:
            try:
                class_obj = SchoolClass.objects.get(id=class_id, tenant=get_current_tenant())
                initial_data['class_name'] = class_obj
            except SchoolClass.DoesNotExist:
                pass
        
        if year_id:
            try:
                year = AcademicYear.objects.get(id=year_id, tenant=get_current_tenant())
                initial_data['academic_year'] = year
            except AcademicYear.DoesNotExist:
                pass
        else:
            # Default to current academic year
            try:
                current_year = AcademicYear.objects.get(tenant=get_current_tenant(), is_current=True)
                initial_data['academic_year'] = current_year
            except AcademicYear.DoesNotExist:
                pass
        
        if initial_data:
            kwargs['initial'] = initial_data
        
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:classsubject_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Subject '{form.instance.subject.name}' assigned to class '{form.instance.class_name.name}' successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='CREATE_CLASS_SUBJECT',
            resource='Class Subject',
            resource_id=str(self.object.id),
            details={
                'class': str(self.object.class_name),
                'subject': str(self.object.subject),
                'teacher': str(self.object.teacher) if self.object.teacher else 'None'
            },
            severity='INFO'
        )
        
        return response


class ClassSubjectUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = ClassSubject
    form_class = ClassSubjectForm
    template_name = 'academics/class_subject/form.html'
    permission_required = 'academics.change_classsubject'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:classsubject_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Class subject assignment updated successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='UPDATE_CLASS_SUBJECT',
            resource='Class Subject',
            resource_id=str(self.object.id),
            details={'changes': form.changed_data},
            severity='INFO'
        )
        
        return response


class ClassSubjectDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = ClassSubject
    template_name = 'academics/common/confirm_delete.html'
    permission_required = 'academics.delete_classsubject'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:classsubject_list')
    
    def delete(self, request, *args, **kwargs):
        class_subject = self.get_object()
        
        # Check if class subject has timetable entries
        if class_subject.timetable_entries.exists():
            messages.error(
                request,
                f"Cannot delete subject assignment because it has timetable entries."
            )
            return JsonResponse({
                'success': False,
                'error': 'Class subject has timetable entries'
            })
        
        # Perform soft delete
        class_subject.delete(
            user=request.user,
            reason=request.POST.get('deletion_reason', 'No reason provided'),
            category=request.POST.get('deletion_category', 'ADMIN_ACTION')
        )
        
        messages.success(
            request,
            f"Subject assignment has been deleted."
        )
        
        audit_log(
            user=request.user,
            action='DELETE_CLASS_SUBJECT',
            resource='Class Subject',
            resource_id=str(class_subject.id),
            details={
                'class': str(class_subject.class_name),
                'subject': str(class_subject.subject)
            },
            severity='WARNING'
        )
        
        return JsonResponse({
            'success': True,
            'redirect': self.get_success_url()
        })


# ==================== TIMETABLE VIEWS ====================

class TimeTableListView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = TimeTable
    template_name = 'academics/timetable/list.html'
    context_object_name = 'timetables'
    permission_required = 'academics.view_timetable'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by class if provided
        class_id = self.request.GET.get('class_id')
        if class_id:
            queryset = queryset.filter(class_name_id=class_id)
        
        # Filter by section if provided
        section_id = self.request.GET.get('section_id')
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        
        # Filter by academic year if provided
        year_id = self.request.GET.get('academic_year')
        if year_id:
            queryset = queryset.filter(academic_year_id=year_id)
        
        return queryset.select_related(
            'class_name', 'section', 'subject', 'teacher', 'academic_year'
        ).order_by('day', 'period_number')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['classes'] = SchoolClass.objects.filter(tenant=tenant, is_active=True)
        context['academic_years'] = AcademicYear.objects.filter(tenant=tenant)
        
        # Get sections if class is selected
        class_id = self.request.GET.get('class_id')
        if class_id:
            context['sections'] = Section.objects.filter(
                class_name_id=class_id,
                is_active=True
            )
        else:
            context['sections'] = []
        
        return context


class TimeTableCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = TimeTable
    form_class = TimeTableForm
    template_name = 'academics/timetable/form.html'
    permission_required = 'academics.add_timetable'
    roles_required = ['admin', 'principal', 'academic_head', 'teacher']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        
        # Pre-select class, section, and academic year if provided
        class_id = self.request.GET.get('class_id')
        section_id = self.request.GET.get('section_id')
        year_id = self.request.GET.get('academic_year')
        
        initial_data = {}
        
        if class_id:
            try:
                class_obj = SchoolClass.objects.get(id=class_id, tenant=get_current_tenant())
                initial_data['class_name'] = class_obj
            except SchoolClass.DoesNotExist:
                pass
        
        if section_id:
            try:
                section = Section.objects.get(id=section_id, tenant=get_current_tenant())
                initial_data['section'] = section
            except Section.DoesNotExist:
                pass
        
        if year_id:
            try:
                year = AcademicYear.objects.get(id=year_id, tenant=get_current_tenant())
                initial_data['academic_year'] = year
            except AcademicYear.DoesNotExist:
                pass
        else:
            # Default to current academic year
            try:
                current_year = AcademicYear.objects.get(tenant=get_current_tenant(), is_current=True)
                initial_data['academic_year'] = current_year
            except AcademicYear.DoesNotExist:
                pass
        
        if initial_data:
            kwargs['initial'] = initial_data
        
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:timetable_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        
        # Set teacher from subject if not provided
        if not form.instance.teacher and form.instance.subject and form.instance.subject.teacher:
            form.instance.teacher = form.instance.subject.teacher
        
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Timetable entry created successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='CREATE_TIMETABLE',
            resource='TimeTable',
            resource_id=str(self.object.id),
            details={
                'class': str(self.object.class_name),
                'section': str(self.object.section),
                'day': self.object.day,
                'period': self.object.period_number
            },
            severity='INFO'
        )
        
        return response


class TimeTableUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = TimeTable
    form_class = TimeTableForm
    template_name = 'academics/timetable/form.html'
    permission_required = 'academics.change_timetable'
    roles_required = ['admin', 'principal', 'academic_head', 'teacher']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:timetable_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Timetable entry updated successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='UPDATE_TIMETABLE',
            resource='TimeTable',
            resource_id=str(self.object.id),
            details={'changes': form.changed_data},
            severity='INFO'
        )
        
        return response


class TimeTableDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = TimeTable
    template_name = 'academics/common/confirm_delete.html'
    permission_required = 'academics.delete_timetable'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_success_url(self):
        return reverse_lazy('academics:timetable_list')
    
    def delete(self, request, *args, **kwargs):
        timetable = self.get_object()
        
        # Perform soft delete
        timetable.delete(
            user=request.user,
            reason=request.POST.get('deletion_reason', 'No reason provided'),
            category=request.POST.get('deletion_category', 'ADMIN_ACTION')
        )
        
        messages.success(
            request,
            f"Timetable entry has been deleted."
        )
        
        audit_log(
            user=request.user,
            action='DELETE_TIMETABLE',
            resource='TimeTable',
            resource_id=str(timetable.id),
            details={
                'class': str(timetable.class_name),
                'section': str(timetable.section),
                'day': timetable.day,
                'period': timetable.period_number
            },
            severity='WARNING'
        )
        
        return JsonResponse({
            'success': True,
            'redirect': self.get_success_url()
        })


class TimeTableWeeklyView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Weekly timetable view"""
    template_name = 'academics/timetable/weekly.html'
    permission_required = 'academics.view_timetable'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        # Get parameters
        class_id = self.request.GET.get('class_id')
        section_id = self.request.GET.get('section_id')
        year_id = self.request.GET.get('academic_year')
        
        # Validate parameters
        if not class_id or not section_id:
            messages.error(self.request, "Please select a class and section.")
            return context
        
        try:
            class_obj = SchoolClass.objects.get(id=class_id, tenant=tenant)
            section = Section.objects.get(id=section_id, tenant=tenant, class_name=class_obj)
            
            # Get academic year
            if year_id:
                academic_year = AcademicYear.objects.get(id=year_id, tenant=tenant)
            else:
                academic_year = AcademicYear.objects.get(tenant=tenant, is_current=True)
            
            # Get timetable entries
            timetable_entries = TimeTable.objects.filter(
                tenant=tenant,
                class_name=class_obj,
                section=section,
                academic_year=academic_year
            ).select_related('subject', 'teacher').order_by('day', 'period_number')
            
            # Organize by day
            weekly_timetable = {}
            for day_code, day_name in TimeTable.DAY_CHOICES:
                day_entries = timetable_entries.filter(day=day_code)
                if day_entries.exists():
                    weekly_timetable[day_name] = list(day_entries)
            
            context['class_obj'] = class_obj
            context['section'] = section
            context['academic_year'] = academic_year
            context['weekly_timetable'] = weekly_timetable
            context['days'] = dict(TimeTable.DAY_CHOICES)
            
        except (SchoolClass.DoesNotExist, Section.DoesNotExist, AcademicYear.DoesNotExist) as e:
            messages.error(self.request, str(e))
        
        # Get classes and sections for filter
        context['classes'] = SchoolClass.objects.filter(tenant=tenant, is_active=True)
        context['academic_years'] = AcademicYear.objects.filter(tenant=tenant)
        
        return context


# ==================== StudentAttendance VIEWS ====================

class AttendanceListView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = StudentAttendance
    template_name = 'academics/StudentAttendance/list.html'
    context_object_name = 'attendances'
    permission_required = 'academics.view_attendance'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date if provided
        date_filter = self.request.GET.get('date')
        if date_filter:
            try:
                date_obj = datetime.strptime(date_filter, '%Y-%m-%d').date()
                queryset = queryset.filter(date=date_obj)
            except ValueError:
                pass
        
        # Filter by class if provided
        class_id = self.request.GET.get('class_id')
        if class_id:
            queryset = queryset.filter(class_name_id=class_id)
        
        # Filter by section if provided
        section_id = self.request.GET.get('section_id')
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        return queryset.select_related(
            'student', 'class_name', 'section', 'marked_by'
        ).order_by('-date', 'class_name__order', 'section__name', 'student__admission_number')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        today = timezone.now().date()
        
        context['classes'] = SchoolClass.objects.filter(tenant=tenant, is_active=True)
        context['status_choices'] = StudentAttendance.ATTENDANCE_STATUS
        context['today'] = today
        
        # Get sections if class is selected
        class_id = self.request.GET.get('class_id')
        if class_id:
            context['sections'] = Section.objects.filter(
                class_name_id=class_id,
                is_active=True
            )
        else:
            context['sections'] = []
        
        context['filters'] = {
            'date': self.request.GET.get('date', today.strftime('%Y-%m-%d')),
            'class_id': self.request.GET.get('class_id', ''),
            'section_id': self.request.GET.get('section_id', ''),
            'status': self.request.GET.get('status', ''),
        }
        
        return context


class AttendanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = StudentAttendance
    form_class = AttendanceForm
    template_name = 'academics/StudentAttendance/form.html'
    permission_required = 'academics.add_attendance'
    roles_required = ['admin', 'principal', 'academic_head', 'teacher', 'class_teacher']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        
        # Pre-fill marked_by
        kwargs['initial'] = {'marked_by': self.request.user}
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:attendance_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"StudentAttendance for {form.instance.student} marked successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='CREATE_ATTENDANCE',
            resource='StudentAttendance',
            resource_id=str(self.object.id),
            details={
                'student': str(self.object.student),
                'date': str(self.object.date),
                'status': self.object.status
            },
            severity='INFO'
        )
        
        return response


class AttendanceBulkCreateView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Bulk StudentAttendance marking"""
    template_name = 'academics/StudentAttendance/bulk.html'
    permission_required = 'academics.add_attendance'
    roles_required = ['admin', 'principal', 'academic_head', 'teacher', 'class_teacher']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        today = timezone.now().date()
        
        # Get parameters
        date = self.request.GET.get('date', today.strftime('%Y-%m-%d'))
        class_id = self.request.GET.get('class_id')
        section_id = self.request.GET.get('section_id')
        session = self.request.GET.get('session', 'FULL_DAY')
        
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            date_obj = today
        
        context['date'] = date_obj
        context['session'] = session
        context['status_choices'] = StudentAttendance.ATTENDANCE_STATUS
        
        # Get students if class and section are selected
        if class_id and section_id:
            try:
                class_obj = SchoolClass.objects.get(id=class_id, tenant=tenant)
                section = Section.objects.get(id=section_id, tenant=tenant, class_name=class_obj)
                
                # Get students (assuming Student model exists)
                try:
                    from apps.students.models import Student
                    students = Student.objects.filter(
                        tenant=tenant,
                        class_name=class_obj,
                        section=section,
                        is_active=True
                    ).order_by('admission_number')
                    
                    # Get existing StudentAttendance for this date and session
                    existing_attendance = StudentAttendance.objects.filter(
                        tenant=tenant,
                        date=date_obj,
                        session=session,
                        class_name=class_obj,
                        section=section
                    )
                    
                    # Create a dictionary of existing StudentAttendance by student
                    attendance_dict = {}
                    for att in existing_attendance:
                        attendance_dict[att.student_id] = att
                    
                    # Prepare student data with StudentAttendance
                    student_data = []
                    for student in students:
                        att = attendance_dict.get(student.id)
                        student_data.append({
                            'student': student,
                            'StudentAttendance': att,
                            'has_record': att is not None
                        })
                    
                    context['class_obj'] = class_obj
                    context['section'] = section
                    context['student_data'] = student_data
                    
                except ImportError:
                    messages.error(self.request, "Student model not found.")
                
            except (SchoolClass.DoesNotExist, Section.DoesNotExist) as e:
                messages.error(self.request, str(e))
        
        # Get classes and sections for filter
        context['classes'] = SchoolClass.objects.filter(tenant=tenant, is_active=True)
        
        if class_id:
            context['sections'] = Section.objects.filter(
                class_name_id=class_id,
                is_active=True
            )
        else:
            context['sections'] = []
        
        context['filters'] = {
            'date': date,
            'class_id': class_id or '',
            'section_id': section_id or '',
            'session': session,
        }
        
        return context
    
    def post(self, request, *args, **kwargs):
        if not request.user.has_perm('academics.add_attendance'):
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        date = request.POST.get('date')
        class_id = request.POST.get('class_id')
        section_id = request.POST.get('section_id')
        session = request.POST.get('session')
        
        if not all([date, class_id, section_id, session]):
            return JsonResponse({'success': False, 'error': 'Missing parameters'})
        
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            class_obj = SchoolClass.objects.get(id=class_id, tenant=get_current_tenant())
            section = Section.objects.get(id=section_id, tenant=get_current_tenant(), class_name=class_obj)
            
            # Get students
            from apps.students.models import Student
            students = Student.objects.filter(
                tenant=get_current_tenant(),
                class_name=class_obj,
                section=section,
                is_active=True
            )
            
            created_count = 0
            updated_count = 0
            
            for student in students:
                status_key = f"status_{student.id}"
                remarks_key = f"remarks_{student.id}"
                
                status = request.POST.get(status_key)
                if status:
                    # Create or update StudentAttendance record
                    StudentAttendance, created = StudentAttendance.objects.update_or_create(
                        tenant=get_current_tenant(),
                        student=student,
                        date=date_obj,
                        session=session,
                        defaults={
                            'status': status,
                            'class_name': class_obj,
                            'section': section,
                            'remarks': request.POST.get(remarks_key, ''),
                            'marked_by': request.user,
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
            
            audit_log(
                user=request.user,
                action='BULK_ATTENDANCE',
                resource='StudentAttendance',
                details={
                    'date': date,
                    'class': str(class_obj),
                    'section': str(section),
                    'created': created_count,
                    'updated': updated_count
                },
                severity='INFO'
            )
            
            messages.success(
                request,
                f"StudentAttendance marked for {created_count + updated_count} students."
            )
            
            return JsonResponse({
                'success': True,
                'message': f"StudentAttendance saved successfully. Created: {created_count}, Updated: {updated_count}"
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class AttendanceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = StudentAttendance
    form_class = AttendanceForm
    template_name = 'academics/StudentAttendance/form.html'
    permission_required = 'academics.change_attendance'
    roles_required = ['admin', 'principal', 'academic_head', 'teacher', 'class_teacher']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:attendance_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"StudentAttendance record updated successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='UPDATE_ATTENDANCE',
            resource='StudentAttendance',
            resource_id=str(self.object.id),
            details={'changes': form.changed_data},
            severity='INFO'
        )
        
        return response


class AttendanceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = StudentAttendance
    template_name = 'academics/common/confirm_delete.html'
    permission_required = 'academics.delete_attendance'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_success_url(self):
        return reverse_lazy('academics:attendance_list')
    
    def delete(self, request, *args, **kwargs):
        StudentAttendance = self.get_object()
        
        # Perform soft delete
        StudentAttendance.delete(
            user=request.user,
            reason=request.POST.get('deletion_reason', 'No reason provided'),
            category=request.POST.get('deletion_category', 'ADMIN_ACTION')
        )
        
        messages.success(
            request,
            f"StudentAttendance record has been deleted."
        )
        
        audit_log(
            user=request.user,
            action='DELETE_ATTENDANCE',
            resource='StudentAttendance',
            resource_id=str(StudentAttendance.id),
            details={
                'student': str(StudentAttendance.student),
                'date': str(StudentAttendance.date)
            },
            severity='WARNING'
        )
        
        return JsonResponse({
            'success': True,
            'redirect': self.get_success_url()
        })


class AttendanceReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """StudentAttendance report view"""
    template_name = 'academics/StudentAttendance/report.html'
    permission_required = 'academics.view_attendance_report'
    roles_required = ['admin', 'principal', 'academic_head', 'teacher']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        today = timezone.now().date()
        
        # Get parameters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        class_id = self.request.GET.get('class_id')
        section_id = self.request.GET.get('section_id')
        
        # Set default dates (current month)
        if not start_date or not end_date:
            start_date = today.replace(day=1)
            end_date = today
        else:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = today.replace(day=1)
                end_date = today
        
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        # Get StudentAttendance data
        attendance_qs = StudentAttendance.objects.filter(
            tenant=tenant,
            date__range=[start_date, end_date]
        )
        
        if class_id:
            attendance_qs = attendance_qs.filter(class_name_id=class_id)
        
        if section_id:
            attendance_qs = attendance_qs.filter(section_id=section_id)
        
        # Calculate statistics
        total_records = attendance_qs.count()
        present_count = attendance_qs.filter(status__in=['PRESENT', 'LATE', 'HALF_DAY']).count()
        absent_count = attendance_qs.filter(status='ABSENT').count()
        leave_count = attendance_qs.filter(status='LEAVE').count()
        
        context['total_records'] = total_records
        context['present_count'] = present_count
        context['absent_count'] = absent_count
        context['leave_count'] = leave_count
        context['attendance_percentage'] = (present_count / total_records * 100) if total_records > 0 else 0
        
        # Get classes and sections for filter
        context['classes'] = SchoolClass.objects.filter(tenant=tenant, is_active=True)
        
        if class_id:
            context['sections'] = Section.objects.filter(
                class_name_id=class_id,
                is_active=True
            )
        else:
            context['sections'] = []
        
        context['filters'] = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'class_id': class_id or '',
            'section_id': section_id or '',
        }
        
        return context


# ==================== HOLIDAY VIEWS ====================

class HolidayListView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = Holiday
    template_name = 'academics/holiday/list.html'
    context_object_name = 'holidays'
    permission_required = 'academics.view_holiday'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by holiday type if provided
        holiday_type = self.request.GET.get('holiday_type')
        if holiday_type and holiday_type != 'all':
            queryset = queryset.filter(holiday_type=holiday_type)
        
        # Filter by academic year if provided
        year_id = self.request.GET.get('academic_year')
        if year_id:
            queryset = queryset.filter(academic_year_id=year_id)
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(
                    Q(start_date__lte=end) & Q(end_date__gte=start)
                )
            except ValueError:
                pass
        
        return queryset.select_related('academic_year').order_by('-start_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['holiday_types'] = Holiday.HOLIDAY_TYPE_CHOICES
        context['academic_years'] = AcademicYear.objects.filter(tenant=tenant)
        context['current_type'] = self.request.GET.get('holiday_type', '')
        context['filters'] = {
            'start_date': self.request.GET.get('start_date', ''),
            'end_date': self.request.GET.get('end_date', ''),
            'academic_year': self.request.GET.get('academic_year', ''),
        }
        return context


class HolidayCalendarView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Holiday Calendar View"""
    template_name = 'academics/holiday/calendar.html'
    permission_required = 'academics.view_holiday'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        # Get academic year if specified
        year_id = self.request.GET.get('academic_year')
        
        if year_id:
            try:
                academic_year = AcademicYear.objects.get(id=year_id, tenant=tenant)
            except AcademicYear.DoesNotExist:
                academic_year = AcademicYear.objects.filter(tenant=tenant, is_current=True).first()
        else:
            academic_year = AcademicYear.objects.filter(tenant=tenant, is_current=True).first()
        
        # Get holidays for the academic year
        holidays = Holiday.objects.filter(tenant=tenant)
        if academic_year:
            holidays = holidays.filter(academic_year=academic_year)
        
        # Format holidays for calendar
        holiday_events = []
        for holiday in holidays:
            holiday_events.append({
                'id': holiday.id,
                'title': holiday.name,
                'start': holiday.start_date.isoformat(),
                'end': holiday.end_date.isoformat(),
                'description': holiday.description,
                'type': holiday.get_holiday_type_display(),
                'color': self.get_holiday_color(holiday.holiday_type),
                'allDay': True,
            })
        
        context['holiday_events'] = json.dumps(holiday_events)
        context['academic_years'] = AcademicYear.objects.filter(tenant=tenant)
        context['selected_year'] = academic_year
        
        return context
    
    def get_holiday_color(self, holiday_type):
        """Get color for holiday type"""
        colors = {
            'NATIONAL': 'danger',
            'RELIGIOUS': 'info',
            'SCHOOL': 'warning',
            'SPORTS': 'success',
            'CULTURAL': 'primary',
            'OTHER': 'secondary'
        }
        return colors.get(holiday_type, 'secondary')


class HolidayDetailView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = Holiday
    template_name = 'academics/holiday/detail.html'
    context_object_name = 'holiday'
    permission_required = 'academics.view_holiday'


class HolidayCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Holiday
    form_class = HolidayForm
    template_name = 'academics/holiday/form.html'
    permission_required = 'academics.add_holiday'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        
        # Pre-select current academic year
        try:
            current_year = AcademicYear.objects.get(tenant=get_current_tenant(), is_current=True)
            kwargs['initial'] = {'academic_year': current_year}
        except AcademicYear.DoesNotExist:
            pass
        
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:holiday_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Holiday '{form.instance.name}' created successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='CREATE_HOLIDAY',
            resource='Holiday',
            resource_id=str(self.object.id),
            details={
                'name': self.object.name,
                'start_date': str(self.object.start_date),
                'end_date': str(self.object.end_date)
            },
            severity='INFO'
        )
        
        return response


class HolidayUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = Holiday
    form_class = HolidayForm
    template_name = 'academics/holiday/form.html'
    permission_required = 'academics.change_holiday'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:holiday_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Holiday '{form.instance.name}' updated successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='UPDATE_HOLIDAY',
            resource='Holiday',
            resource_id=str(self.object.id),
            details={'changes': form.changed_data},
            severity='INFO'
        )
        
        return response


class HolidayDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = Holiday
    template_name = 'academics/common/confirm_delete.html'
    permission_required = 'academics.delete_holiday'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:holiday_list')
    
    def delete(self, request, *args, **kwargs):
        holiday = self.get_object()
        
        # Perform soft delete
        holiday.delete(
            user=request.user,
            reason=request.POST.get('deletion_reason', 'No reason provided'),
            category=request.POST.get('deletion_category', 'ADMIN_ACTION')
        )
        
        messages.success(
            request,
            f"Holiday '{holiday.name}' has been deleted."
        )
        
        audit_log(
            user=request.user,
            action='DELETE_HOLIDAY',
            resource='Holiday',
            resource_id=str(holiday.id),
            details={'name': holiday.name},
            severity='WARNING'
        )
        
        return JsonResponse({
            'success': True,
            'redirect': self.get_success_url()
        })


# ==================== STUDY MATERIAL VIEWS ====================

class StudyMaterialListView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = StudyMaterial
    template_name = 'academics/study_material/list.html'
    context_object_name = 'materials'
    permission_required = 'academics.view_studymaterial'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by class if provided
        class_id = self.request.GET.get('class_id')
        if class_id:
            queryset = queryset.filter(class_name_id=class_id)
        
        # Filter by subject if provided
        subject_id = self.request.GET.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        
        # Filter by material type if provided
        material_type = self.request.GET.get('material_type')
        if material_type and material_type != 'all':
            queryset = queryset.filter(material_type=material_type)
        
        # Filter by publish status
        status = self.request.GET.get('status', 'published')
        if status == 'published':
            queryset = queryset.filter(is_published=True)
        elif status == 'draft':
            queryset = queryset.filter(is_published=False)
        
        # Search
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
        
        return queryset.select_related(
            'class_name', 'subject', 'uploaded_by'
        ).order_by('-publish_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['classes'] = SchoolClass.objects.filter(tenant=tenant, is_active=True)
        context['subjects'] = Subject.objects.filter(tenant=tenant, is_active=True)
        context['material_types'] = StudyMaterial.MATERIAL_TYPE_CHOICES
        context['current_type'] = self.request.GET.get('material_type', '')
        context['status'] = self.request.GET.get('status', 'published')
        context['search'] = self.request.GET.get('search', '')
        return context


class StudyMaterialDetailView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = StudyMaterial
    template_name = 'academics/study_material/detail.html'
    context_object_name = 'material'
    permission_required = 'academics.view_studymaterial'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        material = self.object
        
        # Increment view count
        material.view_count += 1
        material.save(update_fields=['view_count', 'updated_at'])
        
        # Get related materials
        related_materials = StudyMaterial.objects.filter(
            tenant=material.tenant,
            class_name=material.class_name,
            subject=material.subject,
            is_published=True
        ).exclude(id=material.id)[:5]
        
        context['related_materials'] = related_materials
        return context


class StudyMaterialCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = StudyMaterial
    form_class = StudyMaterialForm
    template_name = 'academics/study_material/form.html'
    permission_required = 'academics.add_studymaterial'
    roles_required = ['admin', 'principal', 'academic_head', 'teacher']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        
        # Pre-select current user as uploaded_by
        kwargs['initial'] = {'uploaded_by': self.request.user}
        
        # Pre-select class and subject if provided
        class_id = self.request.GET.get('class_id')
        subject_id = self.request.GET.get('subject_id')
        
        if class_id:
            try:
                class_obj = SchoolClass.objects.get(id=class_id, tenant=get_current_tenant())
                kwargs['initial']['class_name'] = class_obj
            except SchoolClass.DoesNotExist:
                pass
        
        if subject_id:
            try:
                subject = Subject.objects.get(id=subject_id, tenant=get_current_tenant())
                kwargs['initial']['subject'] = subject
            except Subject.DoesNotExist:
                pass
        
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:studymaterial_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        
        # Set publish date if publishing
        if form.instance.is_published and not form.instance.publish_date:
            form.instance.publish_date = timezone.now()
        
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Study material '{form.instance.title}' created successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='CREATE_STUDY_MATERIAL',
            resource='Study Material',
            resource_id=str(self.object.id),
            details={
                'title': self.object.title,
                'class': str(self.object.class_name),
                'subject': str(self.object.subject),
                'type': self.object.material_type
            },
            severity='INFO'
        )
        
        return response


class StudyMaterialUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = StudyMaterial
    form_class = StudyMaterialForm
    template_name = 'academics/study_material/form.html'
    permission_required = 'academics.change_studymaterial'
    roles_required = ['admin', 'principal', 'academic_head', 'teacher']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:studymaterial_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        
        # Set publish date if publishing for the first time
        if form.instance.is_published and not form.instance.publish_date:
            form.instance.publish_date = timezone.now()
        
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Study material '{form.instance.title}' updated successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='UPDATE_STUDY_MATERIAL',
            resource='Study Material',
            resource_id=str(self.object.id),
            details={'changes': form.changed_data},
            severity='INFO'
        )
        
        return response


class StudyMaterialDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = StudyMaterial
    template_name = 'academics/common/confirm_delete.html'
    permission_required = 'academics.delete_studymaterial'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_success_url(self):
        return reverse_lazy('academics:studymaterial_list')
    
    def delete(self, request, *args, **kwargs):
        material = self.get_object()
        
        # Perform soft delete
        material.delete(
            user=request.user,
            reason=request.POST.get('deletion_reason', 'No reason provided'),
            category=request.POST.get('deletion_category', 'ADMIN_ACTION')
        )
        
        messages.success(
            request,
            f"Study material '{material.title}' has been deleted."
        )
        
        audit_log(
            user=request.user,
            action='DELETE_STUDY_MATERIAL',
            resource='Study Material',
            resource_id=str(material.id),
            details={'title': material.title},
            severity='WARNING'
        )
        
        return JsonResponse({
            'success': True,
            'redirect': self.get_success_url()
        })


class StudyMaterialDownloadView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DetailView):
    """View to download study material file"""
    model = StudyMaterial
    permission_required = 'academics.download_studymaterial'
    
    def get(self, request, *args, **kwargs):
        material = self.get_object()
        
        # Check if file exists
        if not material.file:
            messages.error(request, "File not found.")
            return HttpResponseRedirect(reverse('academics:studymaterial_detail', kwargs={'pk': material.pk}))
        
        # Increment download count
        material.download_count += 1
        material.save(update_fields=['download_count', 'updated_at'])
        
        # Log download
        audit_log(
            user=request.user,
            action='DOWNLOAD_STUDY_MATERIAL',
            resource='Study Material',
            resource_id=str(material.id),
            details={'title': material.title, 'file': material.file.name},
            severity='INFO'
        )
        
        # Serve file
        response = HttpResponse(material.file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{material.file.name}"'
        return response


# ==================== SYLLABUS VIEWS ====================

class SyllabusListView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = Syllabus
    template_name = 'academics/syllabus/list.html'
    context_object_name = 'syllabi'
    permission_required = 'academics.view_syllabus'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by class if provided
        class_id = self.request.GET.get('class_id')
        if class_id:
            queryset = queryset.filter(class_name_id=class_id)
        
        # Filter by subject if provided
        subject_id = self.request.GET.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        
        # Filter by academic year if provided
        year_id = self.request.GET.get('academic_year')
        if year_id:
            queryset = queryset.filter(academic_year_id=year_id)
        
        return queryset.select_related(
            'class_name', 'subject', 'academic_year', 'uploaded_by'
        ).order_by('-academic_year__start_date', 'class_name__order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['classes'] = SchoolClass.objects.filter(tenant=tenant, is_active=True)
        context['subjects'] = Subject.objects.filter(tenant=tenant, is_active=True)
        context['academic_years'] = AcademicYear.objects.filter(tenant=tenant)
        return context


class SyllabusCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Syllabus
    form_class = SyllabusForm
    template_name = 'academics/syllabus/form.html'
    permission_required = 'academics.add_syllabus'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        
        # Pre-select current user as uploaded_by
        kwargs['initial'] = {'uploaded_by': self.request.user}
        
        # Pre-select current academic year
        try:
            current_year = AcademicYear.objects.get(tenant=get_current_tenant(), is_current=True)
            kwargs['initial']['academic_year'] = current_year
        except AcademicYear.DoesNotExist:
            pass
        
        # Pre-select class and subject if provided
        class_id = self.request.GET.get('class_id')
        subject_id = self.request.GET.get('subject_id')
        
        if class_id:
            try:
                class_obj = SchoolClass.objects.get(id=class_id, tenant=get_current_tenant())
                kwargs['initial']['class_name'] = class_obj
            except SchoolClass.DoesNotExist:
                pass
        
        if subject_id:
            try:
                subject = Subject.objects.get(id=subject_id, tenant=get_current_tenant())
                kwargs['initial']['subject'] = subject
            except Subject.DoesNotExist:
                pass
        
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:syllabus_list')
    
    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Syllabus for {form.instance.subject} created successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='CREATE_SYLLABUS',
            resource='Syllabus',
            resource_id=str(self.object.id),
            details={
                'class': str(self.object.class_name),
                'subject': str(self.object.subject),
                'academic_year': str(self.object.academic_year)
            },
            severity='INFO'
        )
        
        return response


class SyllabusUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = Syllabus
    form_class = SyllabusForm
    template_name = 'academics/syllabus/form.html'
    permission_required = 'academics.change_syllabus'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:syllabus_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Syllabus updated successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='UPDATE_SYLLABUS',
            resource='Syllabus',
            resource_id=str(self.object.id),
            details={'changes': form.changed_data},
            severity='INFO'
        )
        
        return response


class SyllabusDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = Syllabus
    template_name = 'academics/common/confirm_delete.html'
    permission_required = 'academics.delete_syllabus'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:syllabus_list')
    
    def delete(self, request, *args, **kwargs):
        syllabus = self.get_object()
        
        # Perform soft delete
        syllabus.delete(
            user=request.user,
            reason=request.POST.get('deletion_reason', 'No reason provided'),
            category=request.POST.get('deletion_category', 'ADMIN_ACTION')
        )
        
        messages.success(
            request,
            f"Syllabus has been deleted."
        )
        
        audit_log(
            user=request.user,
            action='DELETE_SYLLABUS',
            resource='Syllabus',
            resource_id=str(syllabus.id),
            details={
                'class': str(syllabus.class_name),
                'subject': str(syllabus.subject)
            },
            severity='WARNING'
        )
        
        return JsonResponse({
            'success': True,
            'redirect': self.get_success_url()
        })


# ==================== HOUSE VIEWS ====================

class HouseListView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = House
    template_name = 'academics/house/list.html'
    context_object_name = 'houses'
    permission_required = 'academics.view_house'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Calculate total points for each house
        for house in context['houses']:
            house.total_points = house.points.aggregate(total=Sum('points'))['total'] or 0
        return context


class HouseDetailView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DetailView):
    model = House
    template_name = 'academics/house/detail.html'
    context_object_name = 'house'
    permission_required = 'academics.view_house'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house = self.object
        
        # Get house points with filters
        points_qs = house.points.select_related('student', 'awarded_by', 'student__class_name').order_by('-awarded_date')
        
        # Filter by date range if provided
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                points_qs = points_qs.filter(awarded_date__range=[start, end])
            except ValueError:
                pass
        
        # Filter by point type if provided
        point_type = self.request.GET.get('point_type')
        if point_type and point_type != 'all':
            points_qs = points_qs.filter(point_type=point_type)
        
        context['house_points'] = points_qs
        context['total_points'] = points_qs.aggregate(total=Sum('points'))['total'] or 0
        
        # Get point type choices for filter
        context['point_types'] = HousePoints.POINT_TYPE_CHOICES
        
        context['filters'] = {
            'start_date': self.request.GET.get('start_date', ''),
            'end_date': self.request.GET.get('end_date', ''),
            'point_type': self.request.GET.get('point_type', ''),
        }
        
        return context


class HouseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = House
    form_class = HouseForm
    template_name = 'academics/house/form.html'
    permission_required = 'academics.add_house'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:house_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"House '{form.instance.name}' created successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='CREATE_HOUSE',
            resource='House',
            resource_id=str(self.object.id),
            details={'name': self.object.name, 'motto': self.object.motto},
            severity='INFO'
        )
        
        return response


class HouseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = House
    form_class = HouseForm
    template_name = 'academics/house/form.html'
    permission_required = 'academics.change_house'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:house_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"House '{form.instance.name}' updated successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='UPDATE_HOUSE',
            resource='House',
            resource_id=str(self.object.id),
            details={'changes': form.changed_data},
            severity='INFO'
        )
        
        return response


class HouseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = House
    template_name = 'academics/common/confirm_delete.html'
    permission_required = 'academics.delete_house'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:house_list')
    
    def delete(self, request, *args, **kwargs):
        house = self.get_object()
        
        # Check if house has students
        if house.students.exists():
            messages.error(
                request,
                f"Cannot delete house '{house.name}' because it has students."
            )
            return JsonResponse({
                'success': False,
                'error': 'House has students'
            })
        
        # Perform soft delete
        house.delete(
            user=request.user,
            reason=request.POST.get('deletion_reason', 'No reason provided'),
            category=request.POST.get('deletion_category', 'ADMIN_ACTION')
        )
        
        messages.success(
            request,
            f"House '{house.name}' has been deleted."
        )
        
        audit_log(
            user=request.user,
            action='DELETE_HOUSE',
            resource='House',
            resource_id=str(house.id),
            details={'name': house.name},
            severity='WARNING'
        )
        
        return JsonResponse({
            'success': True,
            'redirect': self.get_success_url()
        })


# ==================== HOUSE POINTS VIEWS ====================

class HousePointsCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = HousePoints
    form_class = HousePointsForm
    template_name = 'academics/house_points/form.html'
    permission_required = 'academics.add_housepoints'
    roles_required = ['admin', 'principal', 'academic_head', 'teacher']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        
        # Pre-select awarded_by
        kwargs['initial'] = {'awarded_by': self.request.user}
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:house_detail', kwargs={'pk': self.object.house.pk})
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        form.instance.awarded_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"House points awarded successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='CREATE_HOUSE_POINTS',
            resource='House Points',
            resource_id=str(self.object.id),
            details={
                'house': str(self.object.house),
                'student': str(self.object.student),
                'points': self.object.points,
                'reason': self.object.reason
            },
            severity='INFO'
        )
        
        return response


class HousePointsUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = HousePoints
    form_class = HousePointsForm
    template_name = 'academics/house_points/form.html'
    permission_required = 'academics.change_housepoints'
    roles_required = ['admin', 'principal', 'academic_head', 'teacher']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:house_detail', kwargs={'pk': self.object.house.pk})
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"House points updated successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='UPDATE_HOUSE_POINTS',
            resource='House Points',
            resource_id=str(self.object.id),
            details={'changes': form.changed_data},
            severity='INFO'
        )
        
        return response


class HousePointsDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = HousePoints
    template_name = 'academics/common/confirm_delete.html'
    permission_required = 'academics.delete_housepoints'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_success_url(self):
        house_id = self.object.house.id
        return reverse_lazy('academics:house_detail', kwargs={'pk': house_id})
    
    def delete(self, request, *args, **kwargs):
        house_points = self.get_object()
        house_id = house_points.house.id
        
        # Perform soft delete
        house_points.delete(
            user=request.user,
            reason=request.POST.get('deletion_reason', 'No reason provided'),
            category=request.POST.get('deletion_category', 'ADMIN_ACTION')
        )
        
        messages.success(
            request,
            f"House points have been deleted."
        )
        
        audit_log(
            user=request.user,
            action='DELETE_HOUSE_POINTS',
            resource='House Points',
            resource_id=str(house_points.id),
            details={
                'house': str(house_points.house),
                'student': str(house_points.student),
                'points': house_points.points
            },
            severity='WARNING'
        )
        
        return JsonResponse({
            'success': True,
            'redirect': self.get_success_url()
        })


# ==================== STREAM VIEWS ====================

class StreamListView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = Stream
    template_name = 'academics/stream/list.html'
    context_object_name = 'streams'
    permission_required = 'academics.view_stream'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('class_name').order_by('class_name__order', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        context['classes'] = SchoolClass.objects.filter(tenant=tenant, is_active=True)
        return context


class StreamCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Stream
    form_class = StreamForm
    template_name = 'academics/stream/form.html'
    permission_required = 'academics.add_stream'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:stream_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Stream '{form.instance.name}' created successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='CREATE_STREAM',
            resource='Stream',
            resource_id=str(self.object.id),
            details={
                'name': self.object.name,
                'class': str(self.object.class_name)
            },
            severity='INFO'
        )
        
        return response


class StreamUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = Stream
    form_class = StreamForm
    template_name = 'academics/stream/form.html'
    permission_required = 'academics.change_stream'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:stream_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Stream '{form.instance.name}' updated successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='UPDATE_STREAM',
            resource='Stream',
            resource_id=str(self.object.id),
            details={'changes': form.changed_data},
            severity='INFO'
        )
        
        return response


class StreamDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = Stream
    template_name = 'academics/common/confirm_delete.html'
    permission_required = 'academics.delete_stream'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:stream_list')
    
    def delete(self, request, *args, **kwargs):
        stream = self.get_object()
        
        # Check if stream has students (if Student model exists)
        try:
            from apps.students.models import Student
            if stream.students.exists():
                messages.error(
                    request,
                    f"Cannot delete stream '{stream.name}' because it has students."
                )
                return JsonResponse({
                    'success': False,
                    'error': 'Stream has students'
                })
        except ImportError:
            pass
        
        # Perform soft delete
        stream.delete(
            user=request.user,
            reason=request.POST.get('deletion_reason', 'No reason provided'),
            category=request.POST.get('deletion_category', 'ADMIN_ACTION')
        )
        
        messages.success(
            request,
            f"Stream '{stream.name}' has been deleted."
        )
        
        audit_log(
            user=request.user,
            action='DELETE_STREAM',
            resource='Stream',
            resource_id=str(stream.id),
            details={'name': stream.name, 'class': str(stream.class_name)},
            severity='WARNING'
        )
        
        return JsonResponse({
            'success': True,
            'redirect': self.get_success_url()
        })


# ==================== CLASS TEACHER VIEWS ====================

class ClassTeacherListView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, ListView):
    model = ClassTeacher
    template_name = 'academics/class_teacher/list.html'
    context_object_name = 'class_teachers'
    permission_required = 'academics.view_classteacher'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by class if provided
        class_id = self.request.GET.get('class_id')
        if class_id:
            queryset = queryset.filter(class_name_id=class_id)
        
        # Filter by section if provided
        section_id = self.request.GET.get('section_id')
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        
        # Filter by academic year if provided
        year_id = self.request.GET.get('academic_year')
        if year_id:
            queryset = queryset.filter(academic_year_id=year_id)
        
        return queryset.select_related(
            'class_name', 'section', 'teacher', 'academic_year'
        ).order_by('academic_year__start_date', 'class_name__order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['classes'] = SchoolClass.objects.filter(tenant=tenant, is_active=True)
        context['academic_years'] = AcademicYear.objects.filter(tenant=tenant)
        
        # Get sections if class is selected
        class_id = self.request.GET.get('class_id')
        if class_id:
            context['sections'] = Section.objects.filter(
                class_name_id=class_id,
                is_active=True
            )
        else:
            context['sections'] = []
        
        return context


class ClassTeacherCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ClassTeacher
    form_class = ClassTeacherForm
    template_name = 'academics/class_teacher/form.html'
    permission_required = 'academics.add_classteacher'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        
        # Pre-select current academic year
        try:
            current_year = AcademicYear.objects.get(tenant=get_current_tenant(), is_current=True)
            kwargs['initial'] = {'academic_year': current_year}
        except AcademicYear.DoesNotExist:
            pass
        
        # Pre-select class and section if provided
        class_id = self.request.GET.get('class_id')
        section_id = self.request.GET.get('section_id')
        
        if class_id:
            try:
                class_obj = SchoolClass.objects.get(id=class_id, tenant=get_current_tenant())
                kwargs['initial']['class_name'] = class_obj
            except SchoolClass.DoesNotExist:
                pass
        
        if section_id:
            try:
                section = Section.objects.get(id=section_id, tenant=get_current_tenant())
                kwargs['initial']['section'] = section
            except Section.DoesNotExist:
                pass
        
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:classteacher_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Class teacher assigned successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='CREATE_CLASS_TEACHER',
            resource='Class Teacher',
            resource_id=str(self.object.id),
            details={
                'class': str(self.object.class_name),
                'section': str(self.object.section),
                'teacher': str(self.object.teacher),
                'academic_year': str(self.object.academic_year)
            },
            severity='INFO'
        )
        
        return response


class ClassTeacherUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, UpdateView):
    model = ClassTeacher
    form_class = ClassTeacherForm
    template_name = 'academics/class_teacher/form.html'
    permission_required = 'academics.change_classteacher'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('academics:classteacher_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"Class teacher assignment updated successfully."
        )
        
        audit_log(
            user=self.request.user,
            action='UPDATE_CLASS_TEACHER',
            resource='Class Teacher',
            resource_id=str(self.object.id),
            details={'changes': form.changed_data},
            severity='INFO'
        )
        
        return response


class ClassTeacherDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TenantAccessMixin, DeleteView):
    model = ClassTeacher
    template_name = 'academics/common/confirm_delete.html'
    permission_required = 'academics.delete_classteacher'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:classteacher_list')
    
    def delete(self, request, *args, **kwargs):
        class_teacher = self.get_object()
        
        # Perform soft delete
        class_teacher.delete(
            user=request.user,
            reason=request.POST.get('deletion_reason', 'No reason provided'),
            category=request.POST.get('deletion_category', 'ADMIN_ACTION')
        )
        
        messages.success(
            request,
            f"Class teacher assignment has been deleted."
        )
        
        audit_log(
            user=request.user,
            action='DELETE_CLASS_TEACHER',
            resource='Class Teacher',
            resource_id=str(class_teacher.id),
            details={
                'class': str(class_teacher.class_name),
                'section': str(class_teacher.section),
                'teacher': str(class_teacher.teacher)
            },
            severity='WARNING'
        )
        
        return JsonResponse({
            'success': True,
            'redirect': self.get_success_url()
        })


# ==================== API VIEWS ====================

class GetSectionsByClassView(LoginRequiredMixin, View):
    """API view to get sections by class"""
    
    def get(self, request, *args, **kwargs):
        class_id = request.GET.get('class_id')
        if not class_id:
            return JsonResponse({'sections': []})
        
        tenant = get_current_tenant()
        sections = Section.objects.filter(
            tenant=tenant,
            class_name_id=class_id,
            is_active=True
        ).order_by('name').values('id', 'name')
        
        return JsonResponse({'sections': list(sections)})


class GetSubjectsByClassView(LoginRequiredMixin, View):
    """API view to get subjects by class and academic year"""
    
    def get(self, request, *args, **kwargs):
        class_id = request.GET.get('class_id')
        year_id = request.GET.get('academic_year')
        
        if not class_id or not year_id:
            return JsonResponse({'subjects': []})
        
        tenant = get_current_tenant()
        class_subjects = ClassSubject.objects.filter(
            tenant=tenant,
            class_name_id=class_id,
            academic_year_id=year_id
        ).select_related('subject').order_by('subject__name').values(
            'subject__id', 'subject__name', 'subject__code'
        )
        
        subjects = []
        for cs in class_subjects:
            subjects.append({
                'id': cs['subject__id'],
                'name': cs['subject__name'],
                'code': cs['subject__code']
            })
        
        return JsonResponse({'subjects': subjects})


class GetTimeTableByClassSectionView(LoginRequiredMixin, View):
    """API view to get timetable by class and section"""
    
    def get(self, request, *args, **kwargs):
        class_id = request.GET.get('class_id')
        section_id = request.GET.get('section_id')
        year_id = request.GET.get('academic_year')
        
        if not class_id or not section_id:
            return JsonResponse({'timetable': {}})
        
        tenant = get_current_tenant()
        
        # Default to current academic year
        if not year_id:
            try:
                current_year = AcademicYear.objects.get(tenant=tenant, is_current=True)
                year_id = current_year.id
            except AcademicYear.DoesNotExist:
                return JsonResponse({'timetable': {}})
        
        timetable_entries = TimeTable.objects.filter(
            tenant=tenant,
            class_name_id=class_id,
            section_id=section_id,
            academic_year_id=year_id
        ).select_related('subject', 'teacher').order_by('day', 'period_number')
        
        # Organize by day
        timetable_data = {}
        for entry in timetable_entries:
            day_name = dict(TimeTable.DAY_CHOICES).get(entry.day, entry.day)
            if day_name not in timetable_data:
                timetable_data[day_name] = []
            
            timetable_data[day_name].append({
                'period': entry.period_number,
                'start_time': entry.start_time.strftime('%H:%M'),
                'end_time': entry.end_time.strftime('%H:%M'),
                'subject': str(entry.subject),
                'teacher': str(entry.teacher) if entry.teacher else '',
                'room': entry.room_number or ''
            })
        
        return JsonResponse({'timetable': timetable_data})


class AttendanceStatisticsView(LoginRequiredMixin, View):
    """API view to get StudentAttendance statistics"""
    
    def get(self, request, *args, **kwargs):
        tenant = get_current_tenant()
        today = timezone.now().date()
        
        # Get parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        class_id = request.GET.get('class_id')
        
        if not start_date or not end_date:
            # Default to current month
            start_date = today.replace(day=1)
            end_date = today
        else:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': 'Invalid date format'}, status=400)
        
        # Get StudentAttendance data
        attendance_qs = StudentAttendance.objects.filter(
            tenant=tenant,
            date__range=[start_date, end_date]
        )
        
        if class_id:
            attendance_qs = attendance_qs.filter(class_name_id=class_id)
        
        # Calculate statistics
        total_records = attendance_qs.count()
        present_count = attendance_qs.filter(status__in=['PRESENT', 'LATE', 'HALF_DAY']).count()
        absent_count = attendance_qs.filter(status='ABSENT').count()
        leave_count = attendance_qs.filter(status='LEAVE').count()
        
        attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0
        
        # Daily StudentAttendance trend (last 30 days)
        trend_start_date = today - timedelta(days=30)
        daily_attendance = StudentAttendance.objects.filter(
            tenant=tenant,
            date__gte=trend_start_date,
            date__lte=today
        )
        
        if class_id:
            daily_attendance = daily_attendance.filter(class_name_id=class_id)
        
        daily_stats = daily_attendance.values('date').annotate(
            present=Count('id', filter=Q(status__in=['PRESENT', 'LATE', 'HALF_DAY'])),
            total=Count('id')
        ).order_by('date')
        
        daily_data = []
        for stat in daily_stats:
            daily_percentage = (stat['present'] / stat['total'] * 100) if stat['total'] > 0 else 0
            daily_data.append({
                'date': stat['date'].isoformat(),
                'percentage': round(daily_percentage, 2)
            })
        
        return JsonResponse({
            'statistics': {
                'total_records': total_records,
                'present_count': present_count,
                'absent_count': absent_count,
                'leave_count': leave_count,
                'attendance_percentage': round(attendance_percentage, 2)
            },
            'daily_trend': daily_data,
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        })


class ExportAttendanceCSVView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Export StudentAttendance data to CSV"""
    permission_required = 'academics.export_attendance'
    roles_required = ['admin', 'principal', 'academic_head']
    
    def get(self, request, *args, **kwargs):
        tenant = get_current_tenant()
        
        # Get parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        class_id = request.GET.get('class_id')
        section_id = request.GET.get('section_id')
        
        if not start_date or not end_date:
            messages.error(request, "Please provide start and end dates.")
            return HttpResponseRedirect(reverse('academics:attendance_report'))
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return HttpResponseRedirect(reverse('academics:attendance_report'))
        
        # Get StudentAttendance data
        attendance_qs = StudentAttendance.objects.filter(
            tenant=tenant,
            date__range=[start_date, end_date]
        )
        
        if class_id:
            attendance_qs = attendance_qs.filter(class_name_id=class_id)
        
        if section_id:
            attendance_qs = attendance_qs.filter(section_id=section_id)
        
        attendance_qs = attendance_qs.select_related(
            'student', 'class_name', 'section', 'marked_by'
        ).order_by('date', 'class_name__order', 'section__name', 'student__admission_number')
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        filename = f'attendance_report_{start_date}_{end_date}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Write headers
        writer.writerow([
            'Date', 'Student ID', 'Student Name', 'Class', 'Section',
            'Status', 'Remarks', 'Marked By', 'Session'
        ])
        
        # Write data
        for StudentAttendance in attendance_qs:
            writer.writerow([
                StudentAttendance.date,
                StudentAttendance.student.admission_number if StudentAttendance.student else '',
                StudentAttendance.student.get_full_name() if StudentAttendance.student else '',
                StudentAttendance.class_name.name if StudentAttendance.class_name else '',
                StudentAttendance.section.name if StudentAttendance.section else '',
                StudentAttendance.get_status_display(),
                StudentAttendance.remarks or '',
                StudentAttendance.marked_by.get_full_name() if StudentAttendance.marked_by else '',
                StudentAttendance.get_session_display()
            ])
        
        # Log export action
        audit_log(
            user=request.user,
            action='EXPORT_ATTENDANCE_CSV',
            resource='StudentAttendance',
            details={
                'start_date': str(start_date),
                'end_date': str(end_date),
                'class_id': class_id,
                'section_id': section_id
            },
            severity='INFO'
        )
        
        return response


# ==================== UTILITY VIEWS ====================

class AcademicCalendarView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Academic Calendar View"""
    template_name = 'academics/calendar.html'
    permission_required = 'academics.view_academic_calendar'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        # Get current academic year
        try:
            current_year = AcademicYear.objects.get(tenant=tenant, is_current=True)
            context['current_year'] = current_year
            
            # Get terms
            terms = current_year.terms.all().order_by('start_date')
            context['terms'] = terms
            
            # Get holidays
            holidays = Holiday.objects.filter(
                tenant=tenant,
                academic_year=current_year
            ).order_by('start_date')
            context['holidays'] = holidays
            
            # Prepare calendar data
            calendar_data = []
            
            # Add terms to calendar
            for term in terms:
                calendar_data.append({
                    'type': 'term',
                    'title': term.name,
                    'start_date': term.start_date,
                    'end_date': term.end_date,
                    'description': term.description or '',
                    'color': 'info'
                })
            
            # Add holidays to calendar
            for holiday in holidays:
                calendar_data.append({
                    'type': 'holiday',
                    'title': holiday.name,
                    'start_date': holiday.start_date,
                    'end_date': holiday.end_date,
                    'description': holiday.description or '',
                    'color': self.get_holiday_color(holiday.holiday_type)
                })
            
            context['calendar_data'] = json.dumps(calendar_data, default=str)
            
        except AcademicYear.DoesNotExist:
            messages.warning(self.request, "No current academic year found.")
        
        return context
    
    def get_holiday_color(self, holiday_type):
        """Get color for holiday type in calendar"""
        colors = {
            'NATIONAL': 'danger',
            'RELIGIOUS': 'purple',
            'SCHOOL': 'warning',
            'SPORTS': 'success',
            'CULTURAL': 'primary',
            'OTHER': 'secondary'
        }
        return colors.get(holiday_type, 'secondary')


class DashboardWidgetsView(LoginRequiredMixin, View):
    """API view for dashboard widgets data"""
    
    def get(self, request, *args, **kwargs):
        tenant = get_current_tenant()
        today = timezone.now().date()
        
        # Get current academic year
        try:
            current_year = AcademicYear.objects.get(tenant=tenant, is_current=True)
        except AcademicYear.DoesNotExist:
            current_year = None
        
        # Class statistics
        classes = SchoolClass.objects.filter(tenant=tenant, is_active=True)
        class_stats = []
        for level_code, level_name in SchoolClass.CLASS_LEVEL_CHOICES:
            count = classes.filter(level=level_code).count()
            if count > 0:
                class_stats.append({
                    'level': level_name,
                    'count': count
                })
        
        # StudentAttendance statistics
        today_attendance = StudentAttendance.objects.filter(tenant=tenant, date=today)
        present_today = today_attendance.filter(status__in=['PRESENT', 'LATE', 'HALF_DAY']).count()
        absent_today = today_attendance.filter(status='ABSENT').count()
        
        # Teacher statistics (assuming Staff model exists)
        try:
            from apps.hr.models import Staff
            total_teachers = Staff.objects.filter(
                tenant=tenant,
                is_active=True,
                user__role='teacher'
            ).count()
        except ImportError:
            total_teachers = 0
        
        # Recent materials
        recent_materials = StudyMaterial.objects.filter(
            tenant=tenant,
            is_published=True
        ).select_related('class_name', 'subject').order_by('-publish_date')[:5]
        
        materials_list = []
        for material in recent_materials:
            materials_list.append({
                'id': material.id,
                'title': material.title,
                'class': str(material.class_name),
                'subject': str(material.subject),
                'date': material.publish_date.strftime('%b %d') if material.publish_date else '',
                'type': material.get_material_type_display()
            })
        
        # Upcoming holidays
        upcoming_holidays = Holiday.objects.filter(
            tenant=tenant,
            start_date__gte=today
        ).order_by('start_date')[:5]
        
        holidays_list = []
        for holiday in upcoming_holidays:
            holidays_list.append({
                'id': holiday.id,
                'name': holiday.name,
                'start_date': holiday.start_date.strftime('%b %d'),
                'end_date': holiday.end_date.strftime('%b %d'),
                'type': holiday.get_holiday_type_display()
            })
        
        return JsonResponse({
            'class_stats': class_stats,
            'StudentAttendance': {
                'present_today': present_today,
                'absent_today': absent_today
            },
            'teacher_count': total_teachers,
            'recent_materials': materials_list,
            'upcoming_holidays': holidays_list,
            'current_year': str(current_year) if current_year else 'Not Set'
        })