"""
Academic Management Views
"""
import logging
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.core.exceptions import ValidationError

from apps.core.views import (
    BaseListView, BaseDetailView, BaseCreateView, 
    BaseUpdateView, BaseDeleteView, BaseTemplateView
)
from apps.academics.models import (
    AcademicYear, Term, SchoolClass, Section, House, HousePoints,
    Subject, ClassSubject, TimeTable, StudentAttendance, Holiday,
    StudyMaterial, Syllabus, Stream, ClassTeacher, GradingSystem, Grade
)
from apps.academics.forms import (
    AcademicYearForm, TermForm, SchoolClassForm, SectionForm,
    HouseForm, HousePointsForm, SubjectForm, ClassSubjectForm,
    TimeTableForm, StudentAttendanceForm, HolidayForm,
    StudyMaterialForm, SyllabusForm, StreamForm, ClassTeacherForm,
    GradingSystemForm, GradeForm
)

logger = logging.getLogger(__name__)

# ============================================================================
# DASHBOARD AND REPORTS
# ============================================================================

class AcademicsDashboardView(BaseTemplateView):
    """Academics dashboard"""
    template_name = 'academics/dashboard.html'
    permission_required = 'academics.view_academics'
    roles_required = ['admin', 'principal', 'teacher',]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current academic year and term
        current_year = AcademicYear.objects.filter(is_current=True).first()
        current_term = Term.objects.filter(is_current=True).first()
        
        # Statistics - using proper context variable names
        context['total_classes'] = SchoolClass.objects.count()
        context['total_classes_all'] = SchoolClass.objects.with_deleted().count()
        
        # Active classes count for the card
        context['active_classes_count'] = SchoolClass.objects.count()  # or SchoolClass.objects.filter(is_active=True).count()
        
        # Academic Years
        context['total_academic_years'] = AcademicYear.objects.count()
        context['total_academic_years_all'] = AcademicYear.objects.with_deleted().count()
        
        # Terms
        context['total_terms'] = Term.objects.count()
        context['total_terms_all'] = Term.objects.with_deleted().count()
        
        # Other Stats
        context['total_sections'] = Section.objects.filter(is_active=True).count()
        context['total_subjects'] = Subject.objects.filter(is_active=True).count()
        
        context['total_students'] = self.get_total_students(active_only=True)
        context['total_students_all'] = self.get_total_students(active_only=False)
        context['total_students_count'] = self.get_total_students(active_only=True)  # For the card
        
        # Today's attendance
        today = timezone.now().date()
        context['today_attendance'] = self.get_today_attendance(today)
        
        # Upcoming holidays
        context['upcoming_holidays'] = Holiday.objects.filter(
            start_date__gte=today
        ).order_by('start_date')[:5]
        
        # Recent study materials
        context['recent_materials'] = StudyMaterial.objects.filter(
            is_published=True
        ).order_by('-publish_date')[:5]
        
        # Fixed variable names - should match template
        context['current_academic_year'] = current_year  # Changed from 'current_year'
        context['current_term'] = current_term
        
        # Alerts context
        context['missing_academic_year'] = not current_year
        context['missing_term'] = not current_term
        
        return context
    
    def get_total_students(self, active_only=True):
        """Get total students"""
        from apps.students.models import Student
        if active_only:
            return Student.objects.filter(is_active=True).count()  # Assuming Student has is_active field
        return Student.objects.with_deleted().count()
    
    def get_today_attendance(self, date):
        """Get today's attendance summary"""
        attendances = StudentAttendance.objects.filter(date=date)
        total = attendances.count()
        present = attendances.filter(status__in=['PRESENT', 'LATE', 'HALF_DAY']).count()
        
        return {
            'total': total,
            'present': present,
            'absent': total - present if total > 0 else 0,
            'percentage': round((present / total * 100), 2) if total > 0 else 0
        }



# ============================================================================
# ACADEMIC YEAR VIEWS
# ============================================================================

class AcademicYearListView(BaseListView):
    """List all academic years"""
    model = AcademicYear
    template_name = 'academics/academic_year_list.html'
    context_object_name = 'academic_years'
    ordering = ['-start_date']
    search_fields = ['name', 'code']
    permission_required = 'academics.view_academicyear'
    roles_required = ['admin', 'principal', 'registrar']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_year'] = AcademicYear.objects.filter(is_current=True).first()
        return context


class AcademicYearDetailView(BaseDetailView):
    """View academic year details"""
    model = AcademicYear
    template_name = 'academics/academic_year_detail.html'
    context_object_name = 'academic_year'
    permission_required = 'academics.view_academicyear'
    roles_required = ['admin', 'principal', 'registrar']


class AcademicYearCreateView(BaseCreateView):
    """Create a new academic year"""
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'academics/academic_year_form.html'
    permission_required = 'academics.add_academicyear'
    roles_required = ['admin', 'principal', 'registrar']

    def form_valid(self, form):
        """Handle form validation"""
        try:
            with transaction.atomic():
                # If setting as current, unset current from others
                if form.cleaned_data.get('is_current'):
                    AcademicYear.objects.filter(is_current=True).update(is_current=False)
                
                response = super().form_valid(form)
                messages.success(self.request, f"Academic Year '{form.instance.name}' created successfully!")
                return response
                
        except Exception as e:
            messages.error(self.request, f"Error creating academic year: {str(e)}")
            return self.form_invalid(form)


class AcademicYearUpdateView(BaseUpdateView):
    """Update academic year"""
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'academics/academic_year_form.html'
    permission_required = 'academics.change_academicyear'
    roles_required = ['admin', 'principal', 'registrar']

    def form_valid(self, form):
        """Handle form validation"""
        try:
            with transaction.atomic():
                # If setting as current, unset current from others
                if form.cleaned_data.get('is_current'):
                    AcademicYear.objects.filter(is_current=True).exclude(pk=self.object.pk).update(is_current=False)
                
                response = super().form_valid(form)
                messages.success(self.request, f"Academic Year '{form.instance.name}' updated successfully!")
                return response
                
        except Exception as e:
            messages.error(self.request, f"Error updating academic year: {str(e)}")
            return self.form_invalid(form)


class AcademicYearDeleteView(BaseDeleteView):
    """Delete academic year"""
    model = AcademicYear
    template_name = 'academics/academic_year_confirm_delete.html'
    success_url = reverse_lazy('academics:academic_year_list')
    permission_required = 'academics.delete_academicyear'
    roles_required = ['admin', 'principal']


class SetCurrentAcademicYearView(BaseTemplateView):
    """Set academic year as current"""
    template_name = 'academics/set_current_academic_year.html'
    permission_required = 'academics.change_academicyear'
    roles_required = ['admin', 'principal']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['academic_years'] = AcademicYear.objects.all()
        context['current_year'] = AcademicYear.objects.filter(is_current=True).first()
        return context
    
    def post(self, request, *args, **kwargs):
        """Set academic year as current"""
        year_id = request.POST.get('academic_year_id')
        
        try:
            with transaction.atomic():
                # Unset current from all
                AcademicYear.objects.filter(is_current=True).update(is_current=False)
                
                # Set new current
                academic_year = AcademicYear.objects.get(id=year_id)
                academic_year.is_current = True
                academic_year.save()
                
                messages.success(request, f"'{academic_year.name}' set as current academic year!")
                
        except AcademicYear.DoesNotExist:
            messages.error(request, "Academic year not found!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        
        return redirect('academics:set_current_academic_year')


# ============================================================================
# TERM VIEWS
# ============================================================================

class TermListView(BaseListView):
    """List all terms"""
    model = Term
    template_name = 'academics/term_list.html'
    context_object_name = 'terms'
    ordering = ['academic_year', 'order']
    search_fields = ['name', 'term_type']
    permission_required = 'academics.view_term'
    roles_required = ['admin', 'principal', 'registrar', 'teacher']

    def get_queryset(self):
        """Filter terms by academic year if provided"""
        queryset = super().get_queryset()
        
        # Filter by academic year if provided
        academic_year_id = self.request.GET.get('academic_year')
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['academic_years'] = AcademicYear.objects.all()
        context['current_term'] = Term.objects.filter(is_current=True).first()
        return context


class TermDetailView(BaseDetailView):
    """View term details"""
    model = Term
    template_name = 'academics/term_detail.html'
    context_object_name = 'term'
    permission_required = 'academics.view_term'
    roles_required = ['admin', 'principal', 'registrar', 'teacher']


class TermCreateView(BaseCreateView):
    """Create a new term"""
    model = Term
    form_class = TermForm
    template_name = 'academics/term_form.html'
    permission_required = 'academics.add_term'
    roles_required = ['admin', 'principal', 'registrar']

    def get_form_kwargs(self):
        """Add academic year to form kwargs"""
        kwargs = super().get_form_kwargs()
        academic_year_id = self.request.GET.get('academic_year')
        if academic_year_id:
            kwargs['initial'] = {'academic_year': academic_year_id}
        return kwargs
    
    def form_valid(self, form):
        """Handle form validation"""
        try:
            with transaction.atomic():
                # If setting as current, unset current from others
                if form.cleaned_data.get('is_current'):
                    Term.objects.filter(is_current=True).update(is_current=False)
                
                response = super().form_valid(form)
                messages.success(self.request, f"Term '{form.instance.name}' created successfully!")
                return response
                
        except Exception as e:
            messages.error(self.request, f"Error creating term: {str(e)}")
            return self.form_invalid(form)


class TermUpdateView(BaseUpdateView):
    """Update term"""
    model = Term
    form_class = TermForm
    template_name = 'academics/term_form.html'
    permission_required = 'academics.change_term'
    roles_required = ['admin', 'principal', 'registrar']

    def form_valid(self, form):
        """Handle form validation"""
        try:
            with transaction.atomic():
                # If setting as current, unset current from others
                if form.cleaned_data.get('is_current'):
                    Term.objects.filter(is_current=True).exclude(pk=self.object.pk).update(is_current=False)
                
                response = super().form_valid(form)
                messages.success(self.request, f"Term '{form.instance.name}' updated successfully!")
                return response
                
        except Exception as e:
            messages.error(self.request, f"Error updating term: {str(e)}")
            return self.form_invalid(form)


class TermDeleteView(BaseDeleteView):
    """Delete term"""
    model = Term
    template_name = 'academics/term_confirm_delete.html'
    permission_required = 'academics.delete_term'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:term_list')


class SetCurrentTermView(BaseTemplateView):
    """Set term as current"""
    template_name = 'academics/set_current_term.html'
    permission_required = 'academics.change_term'
    roles_required = ['admin', 'principal']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['terms'] = Term.objects.all()
        context['current_term'] = Term.objects.filter(is_current=True).first()
        return context
    
    def post(self, request, *args, **kwargs):
        """Set term as current"""
        term_id = request.POST.get('term_id')
        
        try:
            with transaction.atomic():
                # Unset current from all
                Term.objects.filter(is_current=True).update(is_current=False)
                
                # Set new current
                term = Term.objects.get(id=term_id)
                term.is_current = True
                term.save()
                
                messages.success(request, f"'{term.name}' set as current term!")
                
        except Term.DoesNotExist:
            messages.error(request, "Term not found!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        
        return redirect('academics:set_current_term')


# ============================================================================
# SCHOOL CLASS VIEWS
# ============================================================================

class SchoolClassListView(BaseListView):
    """List all school classes"""
    model = SchoolClass
    template_name = 'academics/class_list.html'
    context_object_name = 'classes'
    ordering = ['order']
    search_fields = ['name', 'code', 'level']
    permission_required = 'academics.view_schoolclass'
    roles_required = ['admin', 'principal', 'teacher', 'registrar']


class SchoolClassDetailView(BaseDetailView):
    """View class details"""
    model = SchoolClass
    template_name = 'academics/class_detail.html'
    context_object_name = 'class_obj'
    permission_required = 'academics.view_schoolclass'
    roles_required = ['admin', 'principal', 'teacher', 'registrar']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_obj = self.object
        
        # Add related data
        context['sections'] = class_obj.sections.filter(is_active=True)
        context['students'] = class_obj.students.filter(is_active=True)
        context['class_subjects'] = class_obj.class_subjects.all()
        
        return context


class SchoolClassCreateView(BaseCreateView):
    """Create a new class"""
    model = SchoolClass
    form_class = SchoolClassForm
    template_name = 'academics/class_form.html'
    permission_required = 'academics.add_schoolclass'
    roles_required = ['admin', 'principal']


class SchoolClassUpdateView(BaseUpdateView):
    """Update class"""
    model = SchoolClass
    form_class = SchoolClassForm
    template_name = 'academics/class_form.html'
    permission_required = 'academics.change_schoolclass'
    roles_required = ['admin', 'principal']


class SchoolClassDeleteView(BaseDeleteView):
    """Delete class"""
    model = SchoolClass
    template_name = 'academics/class_confirm_delete.html'
    success_url = reverse_lazy('academics:class_list')
    permission_required = 'academics.delete_schoolclass'
    roles_required = ['admin', 'principal']


# ============================================================================
# SECTION VIEWS
# ============================================================================

class SectionListView(BaseListView):
    """List all sections"""
    model = Section
    template_name = 'academics/section_list.html'
    context_object_name = 'sections'
    ordering = ['class_name__order', 'name']
    search_fields = ['name', 'code', 'class_name__name']
    permission_required = 'academics.view_section'
    roles_required = ['admin', 'principal', 'teacher']

    def get_queryset(self):
        """Filter sections by class if provided"""
        queryset = super().get_queryset()
        
        # Filter by class if provided
        class_id = self.request.GET.get('class_id')
        if class_id:
            queryset = queryset.filter(class_name_id=class_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classes'] = SchoolClass.objects.filter(is_active=True)
        return context


class SectionDetailView(BaseDetailView):
    """View section details"""
    model = Section
    template_name = 'academics/section_detail.html'
    context_object_name = 'section'
    permission_required = 'academics.view_section'
    roles_required = ['admin', 'principal', 'teacher']


class SectionCreateView(BaseCreateView):
    """Create a new section"""
    model = Section
    form_class = SectionForm
    template_name = 'academics/section_form.html'
    permission_required = 'academics.add_section'
    roles_required = ['admin', 'principal']


class SectionUpdateView(BaseUpdateView):
    """Update section"""
    model = Section
    form_class = SectionForm
    template_name = 'academics/section_form.html'
    permission_required = 'academics.change_section'
    roles_required = ['admin', 'principal']


class SectionDeleteView(BaseDeleteView):
    """Delete section"""
    model = Section
    template_name = 'academics/section_confirm_delete.html'
    permission_required = 'academics.delete_section'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:section_list')


# ============================================================================
# HOUSE VIEWS
# ============================================================================

class HouseListView(BaseListView):
    """List all houses"""
    model = House
    template_name = 'academics/house_list.html'
    context_object_name = 'houses'
    ordering = ['name']
    search_fields = ['name', 'code', 'color']
    permission_required = 'academics.view_house'
    roles_required = ['admin', 'principal', 'teacher']


class HouseDetailView(BaseDetailView):
    """View house details"""
    model = House
    template_name = 'academics/house_detail.html'
    context_object_name = 'house'
    permission_required = 'academics.view_house'
    roles_required = ['admin', 'principal', 'teacher']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house = self.object
        
        # Add points history
        context['points_history'] = house.points_records.all().order_by('-date_awarded')
        
        return context


class HouseCreateView(BaseCreateView):
    """Create a new house"""
    model = House
    form_class = HouseForm
    template_name = 'academics/house_form.html'
    permission_required = 'academics.add_house'
    roles_required = ['admin', 'principal']


class HouseUpdateView(BaseUpdateView):
    """Update house"""
    model = House
    form_class = HouseForm
    template_name = 'academics/house_form.html'
    permission_required = 'academics.change_house'
    roles_required = ['admin', 'principal']


class HouseDeleteView(BaseDeleteView):
    """Delete house"""
    model = House
    template_name = 'academics/house_confirm_delete.html'
    success_url = reverse_lazy('academics:house_list')
    permission_required = 'academics.delete_house'
    roles_required = ['admin', 'principal']


# ============================================================================
# HOUSE POINTS VIEWS
# ============================================================================

class HousePointsListView(BaseListView):
    """List all house points"""
    model = HousePoints
    template_name = 'academics/house_points_list.html'
    context_object_name = 'house_points'
    ordering = ['-date_awarded']
    search_fields = ['house__name', 'activity', 'description']
    permission_required = 'academics.view_housepoints'
    roles_required = ['admin', 'principal', 'teacher']

    def get_queryset(self):
        """Filter house points"""
        queryset = super().get_queryset()
        
        # Filter by house if provided
        house_id = self.request.GET.get('house_id')
        if house_id:
            queryset = queryset.filter(house_id=house_id)
        
        # Filter by date range if provided
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(date_awarded__range=[start_date, end_date])
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['houses'] = House.objects.all()
        context['total_points'] = sum(point.points for point in context['house_points'])
        return context


class HousePointsCreateView(BaseCreateView):
    """Award house points"""
    model = HousePoints
    form_class = HousePointsForm
    template_name = 'academics/house_points_form.html'
    permission_required = 'academics.add_housepoints'
    roles_required = ['admin', 'principal', 'teacher']
    
    def form_valid(self, form):
        """Handle form validation"""
        try:
            with transaction.atomic():
                # Update house total points
                house = form.cleaned_data['house']
                house.total_points += form.cleaned_data['points']
                house.save()
                
                response = super().form_valid(form)
                messages.success(self.request, f"{form.cleaned_data['points']} points awarded to {house.name}!")
                return response
                
        except Exception as e:
            messages.error(self.request, f"Error awarding points: {str(e)}")
            return self.form_invalid(form)


class HousePointsDeleteView(BaseDeleteView):
    """Remove house points"""
    model = HousePoints
    template_name = 'academics/house_points_confirm_delete.html'
    permission_required = 'academics.delete_housepoints'
    roles_required = ['admin', 'principal']
    
    def delete(self, request, *args, **kwargs):
        """Handle deletion and adjust house total"""
        self.object = self.get_object()
        
        try:
            with transaction.atomic():
                # Remove points from house total
                house = self.object.house
                house.total_points -= self.object.points
                if house.total_points < 0:
                    house.total_points = 0
                house.save()
                
                success_url = self.get_success_url()
                self.object.delete()
                
                messages.success(request, f"Points entry removed from {house.name}!")
                return redirect(success_url)
                
        except Exception as e:
            messages.error(request, f"Error removing points: {str(e)}")
            return self.render_to_response(self.get_context_data())
    
    def get_success_url(self):
        return reverse_lazy('academics:house_points_list')


# ============================================================================
# SUBJECT VIEWS
# ============================================================================

class SubjectListView(BaseListView):
    """List all subjects"""
    model = Subject
    template_name = 'academics/subject_list.html'
    context_object_name = 'subjects'
    ordering = ['name']
    search_fields = ['name', 'code', 'subject_type']
    permission_required = 'academics.view_subject'
    roles_required = ['admin', 'principal', 'teacher']


class SubjectDetailView(BaseDetailView):
    """View subject details"""
    model = Subject
    template_name = 'academics/subject_detail.html'
    context_object_name = 'subject'
    permission_required = 'academics.view_subject'
    roles_required = ['admin', 'principal', 'teacher']


class SubjectCreateView(BaseCreateView):
    """Create a new subject"""
    model = Subject
    form_class = SubjectForm
    template_name = 'academics/subject_form.html'
    permission_required = 'academics.add_subject'
    roles_required = ['admin', 'principal']


class SubjectUpdateView(BaseUpdateView):
    """Update subject"""
    model = Subject
    form_class = SubjectForm
    template_name = 'academics/subject_form.html'
    permission_required = 'academics.change_subject'
    roles_required = ['admin', 'principal']


class SubjectDeleteView(BaseDeleteView):
    """Delete subject"""
    model = Subject
    template_name = 'academics/subject_confirm_delete.html'
    success_url = reverse_lazy('academics:subject_list')
    permission_required = 'academics.delete_subject'
    roles_required = ['admin', 'principal']


# ============================================================================
# CLASS SUBJECT VIEWS
# ============================================================================

class ClassSubjectListView(BaseListView):
    """List all class subjects"""
    model = ClassSubject
    template_name = 'academics/class_subject_list.html'
    context_object_name = 'class_subjects'
    ordering = ['class_name', 'subject']
    search_fields = ['class_name__name', 'subject__name']
    permission_required = 'academics.view_classsubject'
    roles_required = ['admin', 'principal', 'teacher']

    def get_queryset(self):
        """Filter class subjects"""
        queryset = super().get_queryset()
        
        # Filter by class if provided
        class_id = self.request.GET.get('class_id')
        if class_id:
            queryset = queryset.filter(class_name_id=class_id)
        
        # Filter by academic year if provided
        academic_year_id = self.request.GET.get('academic_year')
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classes'] = SchoolClass.objects.filter(is_active=True)
        context['academic_years'] = AcademicYear.objects.all()
        return context


class ClassSubjectCreateView(BaseCreateView):
    """Assign subject to class"""
    model = ClassSubject
    form_class = ClassSubjectForm
    template_name = 'academics/class_subject_form.html'
    permission_required = 'academics.add_classsubject'
    roles_required = ['admin', 'principal']

    def get_success_url(self):
        return reverse_lazy('academics:class_subject_list')


class ClassSubjectUpdateView(BaseUpdateView):
    """Update class subject assignment"""
    model = ClassSubject
    form_class = ClassSubjectForm
    template_name = 'academics/class_subject_form.html'
    permission_required = 'academics.change_classsubject'
    roles_required = ['admin', 'principal']

    def get_success_url(self):
        return reverse_lazy('academics:class_subject_list')


class ClassSubjectDeleteView(BaseDeleteView):
    """Remove subject from class"""
    model = ClassSubject
    template_name = 'academics/class_subject_confirm_delete.html'
    permission_required = 'academics.delete_classsubject'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:class_subject_list')


# ============================================================================
# TIMETABLE VIEWS
# ============================================================================

class TimeTableListView(BaseListView):
    """List all timetable entries"""
    model = TimeTable
    template_name = 'academics/timetable_list.html'
    context_object_name = 'timetables'
    ordering = ['day', 'period_number']
    search_fields = ['class_name__name', 'section__name', 'subject__subject__name']
    permission_required = 'academics.view_timetable'
    roles_required = ['admin', 'principal', 'teacher']

    def get_queryset(self):
        """Filter timetable entries"""
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
        academic_year_id = self.request.GET.get('academic_year')
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        
        # Filter by day if provided
        day = self.request.GET.get('day')
        if day:
            queryset = queryset.filter(day=day)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classes'] = SchoolClass.objects.filter(is_active=True)
        context['academic_years'] = AcademicYear.objects.all()
        context['academic_years'] = AcademicYear.objects.all()
        context['days'] = TimeTable.DAY_CHOICES
        
        # Get sections based on selected class
        class_id = self.request.GET.get('class_id')
        if class_id:
            context['sections'] = Section.objects.filter(class_name_id=class_id, is_active=True)
        
        return context


class TimeTableCreateView(BaseCreateView):
    """Create new timetable entry"""
    model = TimeTable
    form_class = TimeTableForm
    template_name = 'academics/timetable_form.html'
    permission_required = 'academics.add_timetable'
    roles_required = ['admin', 'principal']


class TimeTableUpdateView(BaseUpdateView):
    """Update timetable entry"""
    model = TimeTable
    form_class = TimeTableForm
    template_name = 'academics/timetable_form.html'
    permission_required = 'academics.change_timetable'
    roles_required = ['admin', 'principal']


class TimeTableDeleteView(BaseDeleteView):
    """Delete timetable entry"""
    model = TimeTable
    template_name = 'academics/timetable_confirm_delete.html'
    permission_required = 'academics.delete_timetable'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:timetable_list')


class TimeTableByClassView(BaseTemplateView):
    """View timetable for specific class"""
    template_name = 'academics/timetable_by_class.html'
    permission_required = 'academics.view_timetable'
    roles_required = ['admin', 'principal', 'teacher', 'student', 'parent']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        class_id = self.request.GET.get('class_id')
        section_id = self.request.GET.get('section_id')
        academic_year_id = self.request.GET.get('academic_year')
        
        if class_id and section_id and academic_year_id:
            # Get timetable for the class-section
            timetable_entries = TimeTable.objects.filter(
                class_name_id=class_id,
                section_id=section_id,
                academic_year_id=academic_year_id
            ).order_by('day', 'period_number')
            
            # Organize by day
            days = {}
            for entry in timetable_entries:
                if entry.day not in days:
                    days[entry.day] = []
                days[entry.day].append(entry)
            
            context['timetable'] = days
            context['selected_class'] = SchoolClass.objects.get(id=class_id)
            context['selected_section'] = Section.objects.get(id=section_id)
            context['selected_academic_year'] = AcademicYear.objects.get(id=academic_year_id)
        
        # Get filter options
        context['classes'] = SchoolClass.objects.filter(is_active=True)
        context['academic_years'] = AcademicYear.objects.all()
        
        return context


# ============================================================================
# ATTENDANCE VIEWS
# ============================================================================

class StudentAttendanceListView(BaseListView):
    """List student attendance"""
    model = StudentAttendance
    template_name = 'academics/attendance_list.html'
    context_object_name = 'attendances'
    ordering = ['-date', 'student']
    search_fields = ['student__first_name', 'student__last_name', 'class_name__name']
    permission_required = 'academics.view_studentattendance'
    roles_required = ['admin', 'principal', 'teacher']

    def get_queryset(self):
        """Filter attendance"""
        queryset = super().get_queryset()
        
        # Filter by date if provided
        date = self.request.GET.get('date')
        if date:
            queryset = queryset.filter(date=date)
        
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
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate statistics
        attendances = context['attendances']
        total = attendances.count()
        present = attendances.filter(status__in=['PRESENT', 'LATE', 'HALF_DAY']).count()
        
        context['total_attendance'] = total
        context['present_count'] = present
        context['absent_count'] = total - present
        context['attendance_percentage'] = (present / total * 100) if total > 0 else 0
        
        # Get filter options
        context['classes'] = SchoolClass.objects.filter(is_active=True)
        context['sections'] = Section.objects.filter(is_active=True)
        
        return context


class StudentAttendanceCreateView(BaseCreateView):
    """Mark student attendance"""
    model = StudentAttendance
    form_class = StudentAttendanceForm
    template_name = 'academics/attendance_form.html'
    permission_required = 'academics.add_studentattendance'
    roles_required = ['admin', 'principal', 'teacher']


class StudentAttendanceUpdateView(BaseUpdateView):
    """Update student attendance"""
    model = StudentAttendance
    form_class = StudentAttendanceForm
    template_name = 'academics/attendance_form.html'
    permission_required = 'academics.change_studentattendance'
    roles_required = ['admin', 'principal', 'teacher']


class StudentAttendanceDeleteView(BaseDeleteView):
    """Delete attendance record"""
    model = StudentAttendance
    template_name = 'academics/attendance_confirm_delete.html'
    permission_required = 'academics.delete_studentattendance'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:attendance_list')


class BulkAttendanceView(BaseTemplateView):
    """Bulk attendance marking"""
    template_name = 'academics/bulk_attendance.html'
    permission_required = 'academics.add_studentattendance'
    roles_required = ['admin', 'principal', 'teacher']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        class_id = self.request.GET.get('class_id')
        section_id = self.request.GET.get('section_id')
        date = self.request.GET.get('date', timezone.now().date())
        
        if class_id and section_id:
            # Get students for the class-section
            from apps.students.models import Student
            students = Student.objects.filter(
                current_class_id=class_id,
                current_section_id=section_id,
                is_active=True
            ).order_by('roll_number')
            
            # Get existing attendance for the date
            existing_attendance = StudentAttendance.objects.filter(
                class_name_id=class_id,
                section_id=section_id,
                date=date
            )
            
            # Create attendance dict for template
            attendance_dict = {att.student_id: att.status for att in existing_attendance}
            
            context['students'] = students
            context['attendance_dict'] = attendance_dict
            context['selected_class'] = SchoolClass.objects.get(id=class_id)
            context['selected_section'] = Section.objects.get(id=section_id)
            context['date'] = date
        
        context['classes'] = SchoolClass.objects.filter(is_active=True)
        context['sections'] = Section.objects.filter(is_active=True)
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Process bulk attendance"""
        try:
            with transaction.atomic():
                class_id = request.POST.get('class_id')
                section_id = request.POST.get('section_id')
                date = request.POST.get('date')
                
                # Delete existing attendance for the date
                StudentAttendance.objects.filter(
                    class_name_id=class_id,
                    section_id=section_id,
                    date=date
                ).delete()
                
                # Create new attendance records
                for key, value in request.POST.items():
                    if key.startswith('status_'):
                        student_id = key.replace('status_', '')
                        
                        attendance = StudentAttendance(
                            student_id=student_id,
                            class_name_id=class_id,
                            section_id=section_id,
                            date=date,
                            status=value,
                            marked_by=request.user
                        )
                        attendance.save()
                
                messages.success(request, "Attendance marked successfully!")
                
        except Exception as e:
            messages.error(request, f"Error marking attendance: {str(e)}")
        
        return redirect('academics:bulk_attendance')


# ============================================================================
# HOLIDAY VIEWS
# ============================================================================

class HolidayListView(BaseListView):
    """List all holidays"""
    model = Holiday
    template_name = 'academics/holiday_list.html'
    context_object_name = 'holidays'
    ordering = ['-start_date']
    search_fields = ['name', 'holiday_type', 'description']
    permission_required = 'academics.view_holiday'
    roles_required = ['admin', 'principal', 'teacher', 'student', 'parent']


class HolidayDetailView(BaseDetailView):
    """View holiday details"""
    model = Holiday
    template_name = 'academics/holiday_detail.html'
    context_object_name = 'holiday'
    permission_required = 'academics.view_holiday'
    roles_required = ['admin', 'principal', 'teacher', 'student', 'parent']


class HolidayCreateView(BaseCreateView):
    """Create new holiday"""
    model = Holiday
    form_class = HolidayForm
    template_name = 'academics/holiday_form.html'
    permission_required = 'academics.add_holiday'
    roles_required = ['admin', 'principal']


class HolidayUpdateView(BaseUpdateView):
    """Update holiday"""
    model = Holiday
    form_class = HolidayForm
    template_name = 'academics/holiday_form.html'
    permission_required = 'academics.change_holiday'
    roles_required = ['admin', 'principal']


class HolidayDeleteView(BaseDeleteView):
    """Delete holiday"""
    model = Holiday
    template_name = 'academics/holiday_confirm_delete.html'
    success_url = reverse_lazy('academics:holiday_list')
    permission_required = 'academics.delete_holiday'
    roles_required = ['admin', 'principal']


# ============================================================================
# STUDY MATERIAL VIEWS
# ============================================================================

class StudyMaterialListView(BaseListView):
    """List all study materials"""
    model = StudyMaterial
    template_name = 'academics/study_material_list.html'
    context_object_name = 'study_materials'
    ordering = ['-publish_date']
    search_fields = ['title', 'description', 'class_name__name', 'subject__name']
    permission_required = 'academics.view_studymaterial'
    roles_required = ['admin', 'principal', 'teacher', 'student']

    def get_queryset(self):
        """Filter study materials"""
        queryset = super().get_queryset()
        
        # Filter by class if provided
        class_id = self.request.GET.get('class_id')
        if class_id:
            queryset = queryset.filter(class_name_id=class_id)
        
        # Filter by subject if provided
        subject_id = self.request.GET.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        
        # Only show published materials
        queryset = queryset.filter(is_published=True)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classes'] = SchoolClass.objects.filter(is_active=True)
        context['subjects'] = Subject.objects.filter(is_active=True)
        return context


class StudyMaterialDetailView(BaseDetailView):
    """View study material details"""
    model = StudyMaterial
    template_name = 'academics/study_material_detail.html'
    context_object_name = 'study_material'
    permission_required = 'academics.view_studymaterial'
    roles_required = ['admin', 'principal', 'teacher', 'student']


class StudyMaterialCreateView(BaseCreateView):
    """Upload new study material"""
    model = StudyMaterial
    form_class = StudyMaterialForm
    template_name = 'academics/study_material_form.html'
    permission_required = 'academics.add_studymaterial'
    roles_required = ['admin', 'principal', 'teacher']


class StudyMaterialUpdateView(BaseUpdateView):
    """Update study material"""
    model = StudyMaterial
    form_class = StudyMaterialForm
    template_name = 'academics/study_material_form.html'
    permission_required = 'academics.change_studymaterial'
    roles_required = ['admin', 'principal', 'teacher']


class StudyMaterialDeleteView(BaseDeleteView):
    """Delete study material"""
    model = StudyMaterial
    template_name = 'academics/study_material_confirm_delete.html'
    success_url = reverse_lazy('academics:study_material_list')
    permission_required = 'academics.delete_studymaterial'
    roles_required = ['admin', 'principal', 'teacher']


# ============================================================================
# SYLLABUS VIEWS
# ============================================================================

class SyllabusListView(BaseListView):
    """List all syllabi"""
    model = Syllabus
    template_name = 'academics/syllabus_list.html'
    context_object_name = 'syllabi'
    ordering = ['class_name', 'subject']
    search_fields = ['class_name__name', 'subject__name']
    permission_required = 'academics.view_syllabus'
    roles_required = ['admin', 'principal', 'teacher']

    def get_queryset(self):
        """Filter syllabus"""
        queryset = super().get_queryset()
        
        # Filter by class if provided
        class_id = self.request.GET.get('class_id')
        if class_id:
            queryset = queryset.filter(class_name_id=class_id)
        
        # Filter by academic year if provided
        academic_year_id = self.request.GET.get('academic_year')
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classes'] = SchoolClass.objects.filter(is_active=True)
        context['academic_years'] = AcademicYear.objects.all()
        return context


class SyllabusDetailView(BaseDetailView):
    """View syllabus details"""
    model = Syllabus
    template_name = 'academics/syllabus_detail.html'
    context_object_name = 'syllabus'
    permission_required = 'academics.view_syllabus'
    roles_required = ['admin', 'principal', 'teacher', 'student']


class SyllabusCreateView(BaseCreateView):
    """Create new syllabus"""
    model = Syllabus
    form_class = SyllabusForm
    template_name = 'academics/syllabus_form.html'
    permission_required = 'academics.add_syllabus'
    roles_required = ['admin', 'principal']


class SyllabusUpdateView(BaseUpdateView):
    """Update syllabus"""
    model = Syllabus
    form_class = SyllabusForm
    template_name = 'academics/syllabus_form.html'
    permission_required = 'academics.change_syllabus'
    roles_required = ['admin', 'principal']


class SyllabusDeleteView(BaseDeleteView):
    """Delete syllabus"""
    model = Syllabus
    template_name = 'academics/syllabus_confirm_delete.html'
    permission_required = 'academics.delete_syllabus'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:syllabus_list')


# ============================================================================
# STREAM VIEWS
# ============================================================================

class StreamListView(BaseListView):
    """List all streams"""
    model = Stream
    template_name = 'academics/stream_list.html'
    context_object_name = 'streams'
    ordering = ['name']
    search_fields = ['name', 'code']
    permission_required = 'academics.view_stream'
    roles_required = ['admin', 'principal', 'teacher']


class StreamDetailView(BaseDetailView):
    """View stream details"""
    model = Stream
    template_name = 'academics/stream_detail.html'
    context_object_name = 'stream'
    permission_required = 'academics.view_stream'
    roles_required = ['admin', 'principal', 'teacher']


class StreamCreateView(BaseCreateView):
    """Create new stream"""
    model = Stream
    form_class = StreamForm
    template_name = 'academics/stream_form.html'
    permission_required = 'academics.add_stream'
    roles_required = ['admin', 'principal']


class StreamUpdateView(BaseUpdateView):
    """Update stream"""
    model = Stream
    form_class = StreamForm
    template_name = 'academics/stream_form.html'
    permission_required = 'academics.change_stream'
    roles_required = ['admin', 'principal']


class StreamDeleteView(BaseDeleteView):
    """Delete stream"""
    model = Stream
    template_name = 'academics/stream_confirm_delete.html'
    success_url = reverse_lazy('academics:stream_list')
    permission_required = 'academics.delete_stream'
    roles_required = ['admin', 'principal']


# ============================================================================
# CLASS TEACHER VIEWS
# ============================================================================

class ClassTeacherListView(BaseListView):
    """List all class teachers"""
    model = ClassTeacher
    template_name = 'academics/class_teacher_list.html'
    context_object_name = 'class_teachers'
    ordering = ['class_name', 'section']
    search_fields = ['teacher__first_name', 'teacher__last_name', 'class_name__name']
    permission_required = 'academics.view_classteacher'
    roles_required = ['admin', 'principal']

    def get_queryset(self):
        """Filter class teachers"""
        queryset = super().get_queryset()
        
        # Filter by academic year if provided
        academic_year_id = self.request.GET.get('academic_year')
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['academic_years'] = AcademicYear.objects.all()
        return context


class ClassTeacherCreateView(BaseCreateView):
    """Assign class teacher"""
    model = ClassTeacher
    form_class = ClassTeacherForm
    template_name = 'academics/class_teacher_form.html'
    permission_required = 'academics.add_classteacher'
    roles_required = ['admin', 'principal']


class ClassTeacherUpdateView(BaseUpdateView):
    """Update class teacher assignment"""
    model = ClassTeacher
    form_class = ClassTeacherForm
    template_name = 'academics/class_teacher_form.html'
    permission_required = 'academics.change_classteacher'
    roles_required = ['admin', 'principal']


class ClassTeacherDeleteView(BaseDeleteView):
    """Remove class teacher assignment"""
    model = ClassTeacher
    template_name = 'academics/class_teacher_confirm_delete.html'
    permission_required = 'academics.delete_classteacher'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:class_teacher_list')


# ============================================================================
# GRADING SYSTEM VIEWS
# ============================================================================

class GradingSystemListView(BaseListView):
    """List all grading systems"""
    model = GradingSystem
    template_name = 'academics/grading_system_list.html'
    context_object_name = 'grading_systems'
    ordering = ['name']
    search_fields = ['name', 'code']
    permission_required = 'academics.view_gradingsystem'
    roles_required = ['admin', 'principal']


class GradingSystemDetailView(BaseDetailView):
    """View grading system details"""
    model = GradingSystem
    template_name = 'academics/grading_system_detail.html'
    context_object_name = 'grading_system'
    permission_required = 'academics.view_gradingsystem'
    roles_required = ['admin', 'principal']


class GradingSystemCreateView(BaseCreateView):
    """Create new grading system"""
    model = GradingSystem
    form_class = GradingSystemForm
    template_name = 'academics/grading_system_form.html'
    permission_required = 'academics.add_gradingsystem'
    roles_required = ['admin', 'principal']


class GradingSystemUpdateView(BaseUpdateView):
    """Update grading system"""
    model = GradingSystem
    form_class = GradingSystemForm
    template_name = 'academics/grading_system_form.html'
    permission_required = 'academics.change_gradingsystem'
    roles_required = ['admin', 'principal']


class GradingSystemDeleteView(BaseDeleteView):
    """Delete grading system"""
    model = GradingSystem
    template_name = 'academics/grading_system_confirm_delete.html'
    success_url = reverse_lazy('academics:grading_system_list')
    permission_required = 'academics.delete_gradingsystem'
    roles_required = ['admin', 'principal']


class SetDefaultGradingSystemView(BaseTemplateView):
    """Set default grading system"""
    template_name = 'academics/set_default_grading_system.html'
    permission_required = 'academics.change_gradingsystem'
    roles_required = ['admin', 'principal']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grading_systems'] = GradingSystem.objects.all()
        context['default_system'] = GradingSystem.objects.filter(is_default=True).first()
        return context
    
    def post(self, request, *args, **kwargs):
        """Set grading system as default"""
        system_id = request.POST.get('grading_system_id')
        
        try:
            with transaction.atomic():
                # Unset default from all
                GradingSystem.objects.filter(is_default=True).update(is_default=False)
                
                # Set new default
                grading_system = GradingSystem.objects.get(id=system_id)
                grading_system.is_default = True
                grading_system.save()
                
                messages.success(request, f"'{grading_system.name}' set as default grading system!")
                
        except GradingSystem.DoesNotExist:
            messages.error(request, "Grading system not found!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        
        return redirect('academics:set_default_grading_system')


# ============================================================================
# GRADE VIEWS
# ============================================================================

class GradeListView(BaseListView):
    """List all grades"""
    model = Grade
    template_name = 'academics/grade_list.html'
    context_object_name = 'grades'
    ordering = ['grading_system', 'order', 'min_percentage']
    search_fields = ['grade', 'description']
    permission_required = 'academics.view_grade'
    roles_required = ['admin', 'principal']

    def get_queryset(self):
        """Filter grades"""
        queryset = super().get_queryset()
        
        # Filter by grading system if provided
        grading_system_id = self.request.GET.get('grading_system')
        if grading_system_id:
            queryset = queryset.filter(grading_system_id=grading_system_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grading_systems'] = GradingSystem.objects.all()
        return context


class GradeCreateView(BaseCreateView):
    """Create new grade"""
    model = Grade
    form_class = GradeForm
    template_name = 'academics/grade_form.html'
    permission_required = 'academics.add_grade'
    roles_required = ['admin', 'principal']


class GradeUpdateView(BaseUpdateView):
    """Update grade"""
    model = Grade
    form_class = GradeForm
    template_name = 'academics/grade_form.html'
    permission_required = 'academics.change_grade'
    roles_required = ['admin', 'principal']


class GradeDeleteView(BaseDeleteView):
    """Delete grade"""
    model = Grade
    template_name = 'academics/grade_confirm_delete.html'
    permission_required = 'academics.delete_grade'
    roles_required = ['admin', 'principal']
    
    def get_success_url(self):
        return reverse_lazy('academics:grade_list')



class AcademicsReportsView(BaseTemplateView):
    """Academics reports"""
    template_name = 'academics/reports.html'
    permission_required = 'academics.view_academics'
    roles_required = ['admin', 'principal']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        academic_year_id = self.request.GET.get('academic_year')
        class_id = self.request.GET.get('class_id')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        # Initialize reports
        reports = {}
        
        # Attendance report
        if academic_year_id and class_id and start_date and end_date:
            reports['attendance'] = self.get_attendance_report(
                academic_year_id, class_id, start_date, end_date
            )
        
        # Class strength report
        reports['class_strength'] = self.get_class_strength_report()
        
        # Subject distribution report
        reports['subject_distribution'] = self.get_subject_distribution_report()
        
        context['reports'] = reports
        context['academic_years'] = AcademicYear.objects.all()
        context['classes'] = SchoolClass.objects.filter(is_active=True)
        
        return context
    
    def get_attendance_report(self, academic_year_id, class_id, start_date, end_date):
        """Generate attendance report"""
        attendances = StudentAttendance.objects.filter(
            class_name_id=class_id,
            date__range=[start_date, end_date]
        )
        
        # Group by student
        attendance_by_student = {}
        for attendance in attendances:
            student_id = attendance.student_id
            if student_id not in attendance_by_student:
                attendance_by_student[student_id] = {
                    'student': attendance.student,
                    'total': 0,
                    'present': 0,
                    'absent': 0
                }
            
            attendance_by_student[student_id]['total'] += 1
            if attendance.is_present:
                attendance_by_student[student_id]['present'] += 1
            else:
                attendance_by_student[student_id]['absent'] += 1
        
        # Calculate percentages
        for student_data in attendance_by_student.values():
            if student_data['total'] > 0:
                student_data['percentage'] = (student_data['present'] / student_data['total'] * 100)
            else:
                student_data['percentage'] = 0
        
        return {
            'data': list(attendance_by_student.values()),
            'total_days': (timezone.datetime.strptime(end_date, '%Y-%m-%d') - 
                          timezone.datetime.strptime(start_date, '%Y-%m-%d')).days + 1,
            'class_name': SchoolClass.objects.get(id=class_id).name
        }
    
    def get_class_strength_report(self):
        """Generate class strength report"""
        classes = SchoolClass.objects.filter(is_active=True)
        report_data = []
        
        for class_obj in classes:
            sections = class_obj.sections.filter(is_active=True)
            total_students = 0
            
            for section in sections:
                total_students += section.current_strength
            
            report_data.append({
                'class': class_obj,
                'sections': sections.count(),
                'total_students': total_students,
                'max_strength': class_obj.max_strength * sections.count(),
                'available_seats': (class_obj.max_strength * sections.count()) - total_students
            })
        
        return report_data

# ============================================================================
# AJAX VIEWS
# ============================================================================

def load_sections(request):
    """
    AJAX view to load sections for a given class
    """
    from django.http import JsonResponse
    class_id = request.GET.get('class_id')
    sections = Section.objects.none()
    
    if class_id:
        sections = Section.objects.filter(class_name_id=class_id).order_by('name')
        
        # Apply tenant filter if available
        if hasattr(request, 'tenant'):
             sections = sections.filter(tenant=request.tenant)

    # Convert to list and cast UUID to string to avoid serialization errors
    data = list(sections.values('id', 'name'))
    for item in data:
        item['id'] = str(item['id'])

    return JsonResponse(data, safe=False)


def load_subjects(request):
    """
    AJAX view to load subjects (ClassSubject) for a given class
    """
    from django.http import JsonResponse
    class_id = request.GET.get('class_id')
    subjects = ClassSubject.objects.none()
    
    if class_id:
        # We return ClassSubject IDs but display the related Subject name
        subjects = ClassSubject.objects.filter(class_name_id=class_id).order_by('subject__name')
        
        # Apply tenant filter if available
        if hasattr(request, 'tenant'):
             subjects = subjects.filter(tenant=request.tenant)
             
    # value_list explanation: we need 'id' of ClassSubject (to save FK) and 'subject__name' to display
    data = list(subjects.values('id', 'subject__name'))
    for item in data:
        item['id'] = str(item['id'])
    
    return JsonResponse(data, safe=False)
        
