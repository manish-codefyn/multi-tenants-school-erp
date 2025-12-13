# attendance/views.py
import csv
import json
from datetime import datetime, date, timedelta
from calendar import monthrange
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView, ListView, FormView, View
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from apps.academics.models import  StudentAttendance, SchoolClass, Section, AcademicYear, Holiday as AcademicHoliday
from apps.hr.models import  StaffAttendance, Staff
from apps.students.models import Student
from .forms import StudentAttendanceForm, BulkAttendanceForm, AttendanceFilterForm


class AttendanceDashboardView(LoginRequiredMixin, TemplateView):
    """Attendance dashboard with statistics"""
    template_name = 'attendance/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        today = timezone.now().date()
        
        # Today's student attendance summary
        student_attendance_today = StudentAttendance.objects.filter(
            tenant=tenant,
            date=today
        )
        
        # Today's staff attendance summary
        staff_attendance_today = StaffAttendance.objects.filter(
            tenant=tenant,
            date=today
        )
        
        # Student stats
        context['student_present'] = student_attendance_today.filter(status='PRESENT').count()
        context['student_absent'] = student_attendance_today.filter(status='ABSENT').count()
        context['student_late'] = student_attendance_today.filter(status='LATE').count()
        context['student_total'] = Student.objects.filter(tenant=tenant, status='ACTIVE').count()
        
        # Staff stats
        context['staff_present'] = staff_attendance_today.filter(status='PRESENT').count()
        context['staff_absent'] = staff_attendance_today.filter(status='ABSENT').count()
        context['staff_late'] = staff_attendance_today.filter(status='LATE').count()
        context['staff_total'] = Staff.objects.filter(tenant=tenant, employment_status='ACTIVE').count()
        
        # Calculate percentages
        if context['student_total'] > 0:
            context['student_attendance_percent'] = round(
                (context['student_present'] / context['student_total']) * 100, 1
            )
        else:
            context['student_attendance_percent'] = 0
            
        if context['staff_total'] > 0:
            context['staff_attendance_percent'] = round(
                (context['staff_present'] / context['staff_total']) * 100, 1
            )
        else:
            context['staff_attendance_percent'] = 0
        
        # Recent attendance records
        context['recent_student_attendance'] = StudentAttendance.objects.filter(
            tenant=tenant
        ).select_related('student', 'class_name', 'section').order_by('-date', '-created_at')[:10]
        
        context['recent_staff_attendance'] = StaffAttendance.objects.filter(
            tenant=tenant
        ).select_related('staff').order_by('-date', '-created_at')[:10]
        
        # Upcoming holidays
        context['upcoming_holidays'] = AcademicHoliday.objects.filter(
            tenant=tenant,
            start_date__gte=today
        ).order_by('start_date')[:5]
        
        context['today'] = today
        
        return context


class StudentAttendanceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List student attendance records"""
    model = StudentAttendance
    template_name = 'attendance/student_list.html'
    permission_required = 'academics.view_attendance'
    context_object_name = 'attendance_list'
    paginate_by = 50
    
    def get_queryset(self):
        tenant = self.request.tenant
        queryset = StudentAttendance.objects.filter(
            tenant=tenant
        ).select_related('student', 'class_name', 'section', 'student__current_class')
        
        # Apply filters
        date_filter = self.request.GET.get('date')
        class_filter = self.request.GET.get('class')
        section_filter = self.request.GET.get('section')
        status_filter = self.request.GET.get('status')
        
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                queryset = queryset.filter(date=filter_date)
            except ValueError:
                pass
        
        if class_filter:
            queryset = queryset.filter(class_name_id=class_filter)
        
        if section_filter:
            queryset = queryset.filter(section_id=section_filter)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-date', 'student__first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        
        # Add filter form context
        context['filter_form'] = AttendanceFilterForm(
            self.request.GET or None,
            tenant=tenant
        )
        
        # Add available classes for quick stats
        context['classes'] = SchoolClass.objects.filter(tenant=tenant)
        context['today'] = timezone.now().date()
        
        return context


class StudentAttendanceMarkView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Mark individual student attendance"""
    template_name = 'attendance/student_mark.html'
    form_class = StudentAttendanceForm
    permission_required = 'academics.add_attendance'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.tenant
        return kwargs
    
    def form_valid(self, form):
        try:
            attendance = form.save(commit=False)
            attendance.tenant = self.request.tenant
            attendance.marked_by = self.request.user
            attendance.save()
            
            messages.success(
                self.request,
                f'Attendance marked for {attendance.student.full_name}'
            )
            return redirect('attendance:student_mark')
            
        except Exception as e:
            messages.error(self.request, f'Error marking attendance: {str(e)}')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        
        # Get today's attendance summary for quick view
        today = timezone.now().date()
        context['today_attendance'] = StudentAttendance.objects.filter(
            tenant=tenant,
            date=today
        ).select_related('student').order_by('student__first_name')
        
        context['today'] = today
        return context


class StudentBulkAttendanceMarkView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Bulk mark student attendance for a class"""
    template_name = 'attendance/student_bulk_mark.html'
    form_class = BulkAttendanceForm
    permission_required = 'academics.add_attendance'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.tenant
        return kwargs
    
    def form_valid(self, form):
        try:
            attendance_date = form.cleaned_data['date']
            class_name = form.cleaned_data['class_name']
            section = form.cleaned_data['section']
            attendance_data = form.cleaned_data['attendance_data']
            
            tenant = self.request.tenant
            created_count = 0
            updated_count = 0
            
            for student_id, status in attendance_data.items():
                try:
                    student = Student.objects.get(id=student_id, tenant=tenant)
                    
                    # Create or update attendance record
                    attendance, created = StudentAttendance.objects.update_or_create(
                        tenant=tenant,
                        student=student,
                        date=attendance_date,
                        class_name=class_name,
                        section=section,
                        defaults={
                            'status': status,
                            'marked_by': self.request.user
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                        
                except Student.DoesNotExist:
                    continue
            
            messages.success(
                self.request,
                f'Bulk attendance completed: {created_count} created, {updated_count} updated'
            )
            return redirect('attendance:student_bulk_mark')
            
        except Exception as e:
            messages.error(self.request, f'Error in bulk attendance: {str(e)}')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        
        # Get recent bulk uploads for reference
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        
        context['recent_bulk_marks'] = StudentAttendance.objects.filter(
            tenant=tenant,
            created_at__gte=week_ago
        ).values('date', 'class_name__name', 'section__name').annotate(
            total=Count('id')
        ).order_by('-date')[:10]
        
        return context


class MyAttendanceView(LoginRequiredMixin, TemplateView):
    """Student's own attendance view"""
    template_name = 'attendance/my_attendance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if user has a student profile
        student = getattr(self.request.user, 'student_profile', None)
        
        if not student:
            messages.warning(self.request, 'No student profile found')
            return context
        
        tenant = self.request.tenant
        today = timezone.now().date()
        
        # Get current month
        month_start = today.replace(day=1)
        last_day = monthrange(today.year, today.month)[1]
        month_end = today.replace(day=last_day)
        
        # Get attendance for current month
        attendance_records = StudentAttendance.objects.filter(
            tenant=tenant,
            student=student,
            date__range=[month_start, month_end]
        ).order_by('date')
        
        # Calculate statistics
        total_days = (month_end - month_start).days + 1
        present_days = attendance_records.filter(status='PRESENT').count()
        absent_days = attendance_records.filter(status='ABSENT').count()
        late_days = attendance_records.filter(status='LATE').count()
        half_days = attendance_records.filter(status='HALF_DAY').count()
        leave_days = attendance_records.filter(status='LEAVE').count()
        
        # Calculate attendance percentage
        attended_days = present_days + late_days + (half_days * 0.5)
        if total_days > 0:
            attendance_percentage = (attended_days / total_days) * 100
        else:
            attendance_percentage = 0
        
        context.update({
            'student': student,
            'attendance_records': attendance_records,
            'today': today,
            'month_start': month_start,
            'month_end': month_end,
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'half_days': half_days,
            'leave_days': leave_days,
            'attendance_percentage': round(attendance_percentage, 1),
            'current_month': today.strftime('%B %Y'),
        })
        
        return context


class StaffAttendanceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List staff attendance records"""
    model = StaffAttendance
    template_name = 'attendance/staff_list.html'
    permission_required = 'hr.view_attendance'
    context_object_name = 'attendance_list'
    paginate_by = 50
    
    def get_queryset(self):
        tenant = self.request.tenant
        queryset = StaffAttendance.objects.filter(
            tenant=tenant
        ).select_related('staff', 'staff__user')
        
        # Apply filters
        date_filter = self.request.GET.get('date')
        department_filter = self.request.GET.get('department')
        status_filter = self.request.GET.get('status')
        
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                queryset = queryset.filter(date=filter_date)
            except ValueError:
                pass
        
        if department_filter:
            queryset = queryset.filter(staff__department_id=department_filter)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-date', 'staff__user__first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        
        # Add departments for filter
        from apps.hr.models import Department
        context['departments'] = Department.objects.filter(tenant=tenant)
        
        context['today'] = timezone.now().date()
        return context


class StaffAttendanceMarkView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Mark staff attendance"""
    template_name = 'attendance/staff_mark.html'
    permission_required = 'hr.add_attendance'
    
    def get(self, request, *args, **kwargs):
        tenant = request.tenant
        today = timezone.now().date()
        
        # Get all active staff
        staff_list = Staff.objects.filter(
            tenant=tenant,
            employment_status='ACTIVE'
        ).select_related('user', 'department', 'designation')
        
        # Get today's attendance
        today_attendance = StaffAttendance.objects.filter(
            tenant=tenant,
            date=today
        ).select_related('staff')
        
        # Create attendance dict for quick lookup
        attendance_dict = {att.staff_id: att for att in today_attendance}
        
        context = {
            'staff_list': staff_list,
            'attendance_dict': attendance_dict,
            'today': today,
            'attendance_status_choices': StaffAttendance._meta.get_field('status').choices,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        try:
            tenant = request.tenant
            today = timezone.now().date()
            data = request.POST
            
            for staff_id in data.getlist('staff_ids'):
                status = data.get(f'status_{staff_id}')
                check_in = data.get(f'check_in_{staff_id}')
                check_out = data.get(f'check_out_{staff_id}')
                remarks = data.get(f'remarks_{staff_id}', '')
                
                if status:
                    try:
                        staff = Staff.objects.get(id=staff_id, tenant=tenant)
                        
                        attendance, created = StaffAttendance.objects.update_or_create(
                            tenant=tenant,
                            staff=staff,
                            date=today,
                            defaults={
                                'status': status,
                                'check_in': check_in if check_in else None,
                                'check_out': check_out if check_out else None,
                                'remarks': remarks,
                                'marked_by': request.user
                            }
                        )
                        
                    except Staff.DoesNotExist:
                        continue
            
            messages.success(request, 'Staff attendance marked successfully')
            return redirect('attendance:staff_mark')
            
        except Exception as e:
            messages.error(request, f'Error marking staff attendance: {str(e)}')
            return redirect('attendance:staff_mark')


class StaffMyAttendanceView(LoginRequiredMixin, TemplateView):
    """Staff's own attendance view"""
    template_name = 'attendance/staff_my_attendance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if user has a staff profile
        staff = getattr(self.request.user, 'staff_profile', None)
        
        if not staff:
            messages.warning(self.request, 'No staff profile found')
            return context
        
        tenant = self.request.tenant
        today = timezone.now().date()
        
        # Get current month
        month_start = today.replace(day=1)
        last_day = monthrange(today.year, today.month)[1]
        month_end = today.replace(day=last_day)
        
        # Get attendance for current month
        attendance_records = StaffAttendance.objects.filter(
            tenant=tenant,
            staff=staff,
            date__range=[month_start, month_end]
        ).order_by('date')
        
        # Calculate statistics
        total_days = (month_end - month_start).days + 1
        present_days = attendance_records.filter(status='PRESENT').count()
        absent_days = attendance_records.filter(status='ABSENT').count()
        late_days = attendance_records.filter(status='LATE').count()
        half_days = attendance_records.filter(status='HALF_DAY').count()
        leave_days = attendance_records.filter(status='LEAVE').count()
        
        # Calculate working days (exclude weekends)
        working_days = 0
        current_date = month_start
        while current_date <= month_end:
            if current_date.weekday() < 5:  # Monday to Friday
                working_days += 1
            current_date += timedelta(days=1)
        
        # Calculate attendance percentage based on working days
        attended_days = present_days + (half_days * 0.5)
        if working_days > 0:
            attendance_percentage = (attended_days / working_days) * 100
        else:
            attendance_percentage = 0
        
        # Calculate total hours worked
        total_hours = 0
        for record in attendance_records:
            if record.total_hours:
                total_hours += float(record.total_hours)
        
        context.update({
            'staff': staff,
            'attendance_records': attendance_records,
            'today': today,
            'month_start': month_start,
            'month_end': month_end,
            'working_days': working_days,
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'half_days': half_days,
            'leave_days': leave_days,
            'total_hours': round(total_hours, 2),
            'attendance_percentage': round(attendance_percentage, 1),
            'current_month': today.strftime('%B %Y'),
        })
        
        return context


class MarkAttendanceView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """General attendance marking page (choose student/staff)"""
    template_name = 'attendance/mark_attendance.html'
    permission_required = ['academics.add_attendance', 'hr.add_attendance']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        return context


class AttendanceReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Generate attendance reports"""
    template_name = 'attendance/report.html'
    permission_required = ['academics.view_attendance', 'hr.view_attendance']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        
        # Get filter parameters
        report_type = self.request.GET.get('type', 'daily')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        class_id = self.request.GET.get('class')
        department_id = self.request.GET.get('department')
        
        # Set default dates if not provided
        today = timezone.now().date()
        if not start_date:
            start_date = today.replace(day=1)  # Start of month
        if not end_date:
            end_date = today
        
        # Convert string dates to date objects
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            start_date_obj = today.replace(day=1)
            end_date_obj = today
        
        # Get report data based on type
        if report_type == 'student':
            context['report_data'] = self.get_student_report(
                tenant, start_date_obj, end_date_obj, class_id
            )
            context['classes'] = SchoolClass.objects.filter(tenant=tenant)
        elif report_type == 'staff':
            context['report_data'] = self.get_staff_report(
                tenant, start_date_obj, end_date_obj, department_id
            )
            from apps.hr.models import Department
            context['departments'] = Department.objects.filter(tenant=tenant)
        else:  # daily
            context['report_data'] = self.get_daily_report(
                tenant, start_date_obj, end_date_obj
            )
        
        context.update({
            'report_type': report_type,
            'start_date': start_date_obj,
            'end_date': end_date_obj,
            'class_id': class_id,
            'department_id': department_id,
            'today': today,
        })
        
        return context
    
    def get_daily_report(self, tenant, start_date, end_date):
        """Generate daily attendance summary"""
        report_data = []
        current_date = start_date
        
        while current_date <= end_date:
            # Student attendance for the day
            student_attendance = StudentAttendance.objects.filter(
                tenant=tenant,
                date=current_date
            )
            
            # Staff attendance for the day
            staff_attendance = StaffAttendance.objects.filter(
                tenant=tenant,
                date=current_date
            )
            
            student_present = student_attendance.filter(status='PRESENT').count()
            student_absent = student_attendance.filter(status='ABSENT').count()
            student_late = student_attendance.filter(status='LATE').count()
            student_total = Student.objects.filter(tenant=tenant, status='ACTIVE').count()
            
            staff_present = staff_attendance.filter(status='PRESENT').count()
            staff_absent = staff_attendance.filter(status='ABSENT').count()
            staff_late = staff_attendance.filter(status='LATE').count()
            staff_total = Staff.objects.filter(tenant=tenant, employment_status='ACTIVE').count()
            
            report_data.append({
                'date': current_date,
                'student_present': student_present,
                'student_absent': student_absent,
                'student_late': student_late,
                'student_total': student_total,
                'student_percent': round((student_present / student_total * 100), 1) if student_total > 0 else 0,
                'staff_present': staff_present,
                'staff_absent': staff_absent,
                'staff_late': staff_late,
                'staff_total': staff_total,
                'staff_percent': round((staff_present / staff_total * 100), 1) if staff_total > 0 else 0,
            })
            
            current_date += timedelta(days=1)
        
        return report_data
    
    def get_student_report(self, tenant, start_date, end_date, class_id=None):
        """Generate student-wise attendance report"""
        report_data = []
        
        # Get students based on filters
        students = Student.objects.filter(
            tenant=tenant,
            status='ACTIVE'
        ).select_related('current_class', 'section', 'academic_year')
        
        if class_id:
            students = students.filter(current_class_id=class_id)
        
        for student in students:
            # Get attendance records for the period
            attendance_records = StudentAttendance.objects.filter(
                tenant=tenant,
                student=student,
                date__range=[start_date, end_date]
            )
            
            present_days = attendance_records.filter(status='PRESENT').count()
            absent_days = attendance_records.filter(status='ABSENT').count()
            late_days = attendance_records.filter(status='LATE').count()
            total_days = (end_date - start_date).days + 1
            
            report_data.append({
                'student_id': student.id,
                'student_name': student.full_name,
                'admission_number': student.admission_number,
                'class': student.current_class.name if student.current_class else '',
                'section': student.section.name if student.section else '',
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'total_days': total_days,
                'attendance_percent': round((present_days / total_days * 100), 1) if total_days > 0 else 0,
            })
        
        return report_data
    
    def get_staff_report(self, tenant, start_date, end_date, department_id=None):
        """Generate staff-wise attendance report"""
        report_data = []
        
        # Get staff based on filters
        staff_list = Staff.objects.filter(
            tenant=tenant,
            employment_status='ACTIVE'
        ).select_related('user', 'department', 'designation')
        
        if department_id:
            staff_list = staff_list.filter(department_id=department_id)
        
        for staff in staff_list:
            # Get attendance records for the period
            attendance_records = StaffAttendance.objects.filter(
                tenant=tenant,
                staff=staff,
                date__range=[start_date, end_date]
            )
            
            present_days = attendance_records.filter(status='PRESENT').count()
            absent_days = attendance_records.filter(status='ABSENT').count()
            late_days = attendance_records.filter(status='LATE').count()
            total_days = (end_date - start_date).days + 1
            
            # Calculate working days (exclude weekends)
            working_days = 0
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Monday to Friday
                    working_days += 1
                current_date += timedelta(days=1)
            
            report_data.append({
                'staff_id': staff.id,
                'staff_name': staff.full_name,
                'employee_id': staff.employee_id,
                'department': staff.department.name if staff.department else '',
                'designation': staff.designation.title if staff.designation else '',
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'working_days': working_days,
                'attendance_percent': round((present_days / working_days * 100), 1) if working_days > 0 else 0,
            })
        
        return report_data


class QRCodeAttendanceView(LoginRequiredMixin, TemplateView):
    """QR Code based attendance marking"""
    template_name = 'attendance/qr_attendance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        return context


class AttendanceAnalyticsView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Attendance analytics dashboard"""
    template_name = 'attendance/analytics.html'
    permission_required = ['academics.view_attendance', 'hr.view_attendance']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        
        # Get date range (default: last 30 days)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Student attendance trends
        student_attendance = StudentAttendance.objects.filter(
            tenant=tenant,
            date__range=[start_date, end_date]
        )
        
        # Staff attendance trends
        staff_attendance = StaffAttendance.objects.filter(
            tenant=tenant,
            date__range=[start_date, end_date]
        )
        
        # Calculate daily trends
        daily_trends = []
        current_date = start_date
        
        while current_date <= end_date:
            day_student_att = student_attendance.filter(date=current_date)
            day_staff_att = staff_attendance.filter(date=current_date)
            
            student_present = day_student_att.filter(status='PRESENT').count()
            student_total = Student.objects.filter(tenant=tenant, status='ACTIVE').count()
            
            staff_present = day_staff_att.filter(status='PRESENT').count()
            staff_total = Staff.objects.filter(tenant=tenant, employment_status='ACTIVE').count()
            
            student_percent = round((student_present / student_total * 100), 1) if student_total > 0 else 0
            staff_percent = round((staff_present / staff_total * 100), 1) if staff_total > 0 else 0
            
            daily_trends.append({
                'date': current_date,
                'student_percent': student_percent,
                'staff_percent': staff_percent,
                'student_present': student_present,
                'staff_present': staff_present,
            })
            
            current_date += timedelta(days=1)
        
        # Class-wise attendance
        class_attendance = []
        classes = SchoolClass.objects.filter(tenant=tenant)
        
        for class_obj in classes:
            class_att = student_attendance.filter(class_name=class_obj)
            total_records = class_att.count()
            present_records = class_att.filter(status='PRESENT').count()
            
            if total_records > 0:
                class_rate = round((present_records / total_records) * 100, 1)
            else:
                class_rate = 0
            
            class_attendance.append({
                'class': class_obj.name,
                'rate': class_rate,
                'total': total_records,
                'present': present_records
            })
        
        # Department-wise staff attendance
        department_attendance = []
        from apps.hr.models import Department
        
        departments = Department.objects.filter(tenant=tenant)
        for dept in departments:
            dept_staff = Staff.objects.filter(department=dept, employment_status='ACTIVE')
            dept_att = staff_attendance.filter(staff__department=dept)
            
            total_records = dept_att.count()
            present_records = dept_att.filter(status='PRESENT').count()
            
            if total_records > 0:
                dept_rate = round((present_records / total_records) * 100, 1)
            else:
                dept_rate = 0
            
            department_attendance.append({
                'department': dept.name,
                'rate': dept_rate,
                'total_staff': dept_staff.count(),
                'present': present_records
            })
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'daily_trends': daily_trends,
            'class_attendance': class_attendance,
            'department_attendance': department_attendance,
            'total_student_days': student_attendance.count(),
            'total_staff_days': staff_attendance.count(),
        })
        
        return context


class AttendanceExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Export attendance data to CSV"""
    permission_required = ['academics.view_attendance', 'hr.view_attendance']
    
    def get(self, request, *args, **kwargs):
        export_type = request.GET.get('type', 'student')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Set default dates
        today = timezone.now().date()
        if not start_date:
            start_date = today.replace(day=1)
        if not end_date:
            end_date = today
        
        # Convert to date objects
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            start_date_obj = today.replace(day=1)
            end_date_obj = today
        
        if export_type == 'student':
            return self.export_student_attendance(request.tenant, start_date_obj, end_date_obj)
        else:
            return self.export_staff_attendance(request.tenant, start_date_obj, end_date_obj)
    
    def export_student_attendance(self, tenant, start_date, end_date):
        """Export student attendance as CSV"""
        response = HttpResponse(content_type='text/csv')
        filename = f"student_attendance_{start_date}_to_{end_date}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Write headers
        writer.writerow([
            'Date', 'Admission Number', 'Student Name', 'Class', 
            'Section', 'Status', 'Remarks', 'Marked By', 'Marked At'
        ])
        
        # Get attendance records
        attendance_list = StudentAttendance.objects.filter(
            tenant=tenant,
            date__range=[start_date, end_date]
        ).select_related('student', 'class_name', 'section', 'marked_by').order_by('date', 'student__first_name')
        
        for attendance in attendance_list:
            writer.writerow([
                attendance.date,
                attendance.student.admission_number,
                attendance.student.full_name,
                attendance.class_name.name if attendance.class_name else '',
                attendance.section.name if attendance.section else '',
                attendance.get_status_display(),
                attendance.remarks or '',
                attendance.marked_by.get_full_name() if attendance.marked_by else '',
                attendance.created_at.strftime('%Y-%m-%d %H:%M:%S') if attendance.created_at else '',
            ])
        
        return response
    
    def export_staff_attendance(self, tenant, start_date, end_date):
        """Export staff attendance as CSV"""
        response = HttpResponse(content_type='text/csv')
        filename = f"staff_attendance_{start_date}_to_{end_date}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Write headers
        writer.writerow([
            'Date', 'Employee ID', 'Staff Name', 'Department', 
            'Designation', 'Status', 'Check In', 'Check Out', 
            'Total Hours', 'Late Minutes', 'Remarks', 'Marked By', 'Marked At'
        ])
        
        # Get attendance records
        attendance_list = StaffAttendance.objects.filter(
            tenant=tenant,
            date__range=[start_date, end_date]
        ).select_related('staff', 'staff__department', 'staff__designation', 'marked_by').order_by('date', 'staff__user__first_name')
        
        for attendance in attendance_list:
            writer.writerow([
                attendance.date,
                attendance.staff.employee_id,
                attendance.staff.full_name,
                attendance.staff.department.name if attendance.staff.department else '',
                attendance.staff.designation.title if attendance.staff.designation else '',
                attendance.get_status_display(),
                attendance.check_in.strftime('%H:%M:%S') if attendance.check_in else '',
                attendance.check_out.strftime('%H:%M:%S') if attendance.check_out else '',
                attendance.total_hours or '',
                attendance.late_minutes,
                attendance.remarks or '',
                attendance.marked_by.get_full_name() if attendance.marked_by else '',
                attendance.created_at.strftime('%Y-%m-%d %H:%M:%S') if attendance.created_at else '',
            ])
        
        return response


class DailyAttendanceReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Daily attendance report"""
    template_name = 'attendance/daily_report.html'
    permission_required = ['academics.view_attendance', 'hr.view_attendance']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        
        # Get report date (default: today)
        report_date_str = self.request.GET.get('date')
        if report_date_str:
            try:
                report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
            except ValueError:
                report_date = timezone.now().date()
        else:
            report_date = timezone.now().date()
        
        # Get student attendance for the date
        student_attendance = StudentAttendance.objects.filter(
            tenant=tenant,
            date=report_date
        ).select_related('student', 'class_name', 'section').order_by('class_name__order', 'section__name', 'student__first_name')
        
        # Get staff attendance for the date
        staff_attendance = StaffAttendance.objects.filter(
            tenant=tenant,
            date=report_date
        ).select_related('staff', 'staff__department').order_by('staff__department__name', 'staff__user__first_name')
        
        # Group student attendance by class and section
        student_by_class = {}
        for att in student_attendance:
            class_name = att.class_name.name if att.class_name else 'Unknown'
            section_name = att.section.name if att.section else 'Unknown'
            key = f"{class_name} - {section_name}"
            
            if key not in student_by_class:
                student_by_class[key] = {
                    'class_name': class_name,
                    'section_name': section_name,
                    'students': [],
                    'present': 0,
                    'absent': 0,
                    'late': 0,
                    'total': 0
                }
            
            student_by_class[key]['students'].append(att)
            student_by_class[key]['total'] += 1
            
            if att.status == 'PRESENT':
                student_by_class[key]['present'] += 1
            elif att.status == 'ABSENT':
                student_by_class[key]['absent'] += 1
            elif att.status == 'LATE':
                student_by_class[key]['late'] += 1
        
        # Group staff attendance by department
        staff_by_department = {}
        for att in staff_attendance:
            dept_name = att.staff.department.name if att.staff.department else 'Unknown'
            
            if dept_name not in staff_by_department:
                staff_by_department[dept_name] = {
                    'department': dept_name,
                    'staff_list': [],
                    'present': 0,
                    'absent': 0,
                    'late': 0,
                    'total': 0
                }
            
            staff_by_department[dept_name]['staff_list'].append(att)
            staff_by_department[dept_name]['total'] += 1
            
            if att.status == 'PRESENT':
                staff_by_department[dept_name]['present'] += 1
            elif att.status == 'ABSENT':
                staff_by_department[dept_name]['absent'] += 1
            elif att.status == 'LATE':
                staff_by_department[dept_name]['late'] += 1
        
        context.update({
            'report_date': report_date,
            'student_by_class': student_by_class.values(),
            'staff_by_department': staff_by_department.values(),
            'total_students': Student.objects.filter(tenant=tenant, status='ACTIVE').count(),
            'total_staff': Staff.objects.filter(tenant=tenant, employment_status='ACTIVE').count(),
        })
        
        return context


class MonthlyAttendanceReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Monthly attendance report"""
    template_name = 'attendance/monthly_report.html'
    permission_required = ['academics.view_attendance', 'hr.view_attendance']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        
        # Get month and year (default: current month)
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))
        
        # Calculate date range
        month_start = date(year, month, 1)
        month_end = date(year, month, monthrange(year, month)[1])
        
        # Get student attendance for the month
        student_attendance = StudentAttendance.objects.filter(
            tenant=tenant,
            date__range=[month_start, month_end]
        )
        
        # Get staff attendance for the month
        staff_attendance = StaffAttendance.objects.filter(
            tenant=tenant,
            date__range=[month_start, month_end]
        )
        
        # Calculate student statistics
        total_students = Student.objects.filter(tenant=tenant, status='ACTIVE').count()
        student_present_days = student_attendance.filter(status='PRESENT').count()
        student_total_days = total_students * ((month_end - month_start).days + 1)
        
        # Calculate staff statistics
        total_staff = Staff.objects.filter(tenant=tenant, employment_status='ACTIVE').count()
        staff_present_days = staff_attendance.filter(status='PRESENT').count()
        
        # Calculate working days (exclude weekends)
        working_days = 0
        current_date = month_start
        while current_date <= month_end:
            if current_date.weekday() < 5:  # Monday to Friday
                working_days += 1
            current_date += timedelta(days=1)
        
        staff_total_days = total_staff * working_days
        
        context.update({
            'year': year,
            'month': month,
            'month_start': month_start,
            'month_end': month_end,
            'student_present_days': student_present_days,
            'student_total_days': student_total_days,
            'student_percentage': round((student_present_days / student_total_days * 100), 1) if student_total_days > 0 else 0,
            'staff_present_days': staff_present_days,
            'staff_total_days': staff_total_days,
            'staff_percentage': round((staff_present_days / staff_total_days * 100), 1) if staff_total_days > 0 else 0,
            'total_students': total_students,
            'total_staff': total_staff,
            'working_days': working_days,
            'month_name': month_start.strftime('%B %Y'),
        })
        
        return context


class StudentAttendanceReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Individual student attendance report"""
    template_name = 'attendance/student_report.html'
    permission_required = 'academics.view_attendance'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_id = self.kwargs.get('student_id')
        tenant = self.request.tenant
        
        # Get student
        student = get_object_or_404(Student, id=student_id, tenant=tenant)
        
        # Get date range (default: current month)
        today = timezone.now().date()
        month_start = today.replace(day=1)
        last_day = monthrange(today.year, today.month)[1]
        month_end = today.replace(day=last_day)
        
        # Get attendance records
        attendance_records = StudentAttendance.objects.filter(
            tenant=tenant,
            student=student,
            date__range=[month_start, month_end]
        ).order_by('date')
        
        # Calculate statistics
        total_days = (month_end - month_start).days + 1
        present_days = attendance_records.filter(status='PRESENT').count()
        absent_days = attendance_records.filter(status='ABSENT').count()
        late_days = attendance_records.filter(status='LATE').count()
        half_days = attendance_records.filter(status='HALF_DAY').count()
        
        # Calculate attendance percentage
        attended_days = present_days + late_days + (half_days * 0.5)
        if total_days > 0:
            attendance_percentage = (attended_days / total_days) * 100
        else:
            attendance_percentage = 0
        
        # Get class average for comparison
        if student.current_class and student.section:
            class_attendance = StudentAttendance.objects.filter(
                tenant=tenant,
                class_name=student.current_class,
                section=student.section,
                date__range=[month_start, month_end]
            )
            class_present = class_attendance.filter(status='PRESENT').count()
            class_total = class_attendance.count()
            class_percentage = round((class_present / class_total * 100), 1) if class_total > 0 else 0
        else:
            class_percentage = 0
        
        context.update({
            'student': student,
            'attendance_records': attendance_records,
            'month_start': month_start,
            'month_end': month_end,
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'half_days': half_days,
            'attendance_percentage': round(attendance_percentage, 1),
            'class_percentage': class_percentage,
            'current_month': today.strftime('%B %Y'),
        })
        
        return context