from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from apps.students.models import Student
from apps.academics.models import Attendance, SchoolClass, Section
from .forms import AttendanceFilterForm

class AttendanceDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'attendance/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        context['total_present'] = Attendance.objects.filter(date=today, status='PRESENT').count()
        context['total_absent'] = Attendance.objects.filter(date=today, status='ABSENT').count()
        return context

class MarkAttendanceView(LoginRequiredMixin, TemplateView):
    template_name = 'attendance/mark_attendance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = AttendanceFilterForm(self.request.GET or None)
        context['filter_form'] = form

        if form.is_valid():
            date = form.cleaned_data['date']
            school_class = form.cleaned_data['school_class']
            section = form.cleaned_data['section']
            session = form.cleaned_data['session']
            
            students = Student.objects.filter(
                current_class=school_class,
                current_section=section,
                is_active=True
            ).order_by('first_name')
            
            attendance_records = Attendance.objects.filter(
                date=date,
                class_name=school_class,
                section=section,
                session=session
            ).select_related('student')
            
            attendance_dict = {att.student_id: att.status for att in attendance_records}
            
            student_list = []
            for student in students:
                student_list.append({
                    'student': student,
                    'status': attendance_dict.get(student.id, 'PRESENT') # Default to PRESENT
                })
            
            context['students'] = student_list
            context['selected_date'] = date
            context['selected_class'] = school_class
            context['selected_section'] = section
            context['selected_session'] = session
            
        return context

    def post(self, request, *args, **kwargs):
        form = AttendanceFilterForm(request.GET) # Re-validate to ensure context
        if not form.is_valid():
             messages.error(request, "Invalid parameters. Please select class/section first.")
             return redirect('attendance:mark_attendance')
             
        date = form.cleaned_data['date']
        school_class = form.cleaned_data['school_class']
        section = form.cleaned_data['section']
        session = form.cleaned_data['session']
        
        students = Student.objects.filter(
            current_class=school_class,
            current_section=section,
            is_active=True
        )
        
        count = 0
        for student in students:
            status = request.POST.get(f'student_{student.id}')
            if status:
                Attendance.objects.update_or_create(
                    student=student,
                    date=date,
                    session=session,
                    defaults={
                        'status': status,
                        'class_name': school_class,
                        'section': section,
                        'marked_by': request.user if request.user.is_authenticated else None
                    }
                )
                count += 1
        
        messages.success(request, f"Attendance marked for {count} students.")
        return redirect(f"{request.path}?{request.GET.urlencode()}")

class AttendanceReportView(LoginRequiredMixin, TemplateView):
    template_name = 'attendance/report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Simple Get-based filter
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        class_id = self.request.GET.get('class_id')
        section_id = self.request.GET.get('section_id')
        
        context['classes'] = SchoolClass.objects.all()
        context['sections'] = Section.objects.all()
        
        if class_id and section_id and date_from and date_to:
            attendance_qs = Attendance.objects.filter(
                class_name_id=class_id,
                section_id=section_id,
                date__range=[date_from, date_to]
            ).select_related('student').order_by('date', 'student__first_name')
            
            # Group by student and date? 
            # Or structure for a grid: Rows = Students, Cols = Dates
            
            # Get all students for this class/section
            students = Student.objects.filter(
                current_class_id=class_id,
                current_section_id=section_id
            ).order_by('first_name')
            
            # Get all dates in range
            # Calculate dates between date_from and date_to
            from datetime import datetime, timedelta
            d1 = datetime.strptime(date_from, "%Y-%m-%d").date()
            d2 = datetime.strptime(date_to, "%Y-%m-%d").date()
            delta = d2 - d1
            
            dates = [d1 + timedelta(days=i) for i in range(delta.days + 1)]
            
            report_data = []
            for student in students:
                student_row = {'student': student, 'attendance': {}}
                for d in dates:
                    # Find status for this date
                    # This is N*M queries if not optimized. Optimized:
                    pass
                report_data.append(student_row)
            
            # Optimization: Fetch all attendance and map
            att_map = {(a.student_id, a.date): a.status for a in attendance_qs}
            
            final_report = []
            for student in students:
                res = {'student': student, 'statuses': []}
                for d in dates:
                    res['statuses'].append(att_map.get((student.id, d), '-'))
                final_report.append(res)
                
            context['report_data'] = final_report
            context['dates'] = dates
            context['selected_class'] = int(class_id)
            context['selected_section'] = int(section_id)
            context['date_from'] = date_from
            context['date_to'] = date_to

        return context

class QRCodeAttendanceView(LoginRequiredMixin, TemplateView):
    template_name = 'attendance/qr_attendance.html'

    def post(self, request, *args, **kwargs):
        reg_no = request.POST.get('reg_no')
        if not reg_no:
            return JsonResponse({'status': 'error', 'message': 'No Registration Number provided'}, status=400)
        
        try:
            student = Student.objects.get(reg_no=reg_no, is_active=True)
            today = timezone.now().date()
            
            # Auto-determine class/section from student
            school_class = student.current_class
            section = student.current_section
            
            if not school_class or not section:
                 return JsonResponse({'status': 'error', 'message': 'Student not assigned to class/section'}, status=400)

            # Mark attendance
            # Check if already marked
            attendance, created = Attendance.objects.get_or_create(
                student=student,
                date=today,
                defaults={
                    'status': 'PRESENT',
                    'class_name': school_class,
                    'section': section,
                    'session': 'FULL_DAY', # Default
                    'marked_by': request.user if request.user.is_authenticated else None,
                    'remarks': f'Marked via QR Scan at {timezone.now().time()}'
                }
            )
            
            if not created:
                # Update if absent/late? Or just notify?
                # Let's update to Present if it was Absent
                if attendance.status != 'PRESENT':
                    attendance.status = 'PRESENT'
                    attendance.remarks += f' | Updated via QR at {timezone.now().time()}'
                    attendance.save()
                    message = f"Attendance updated to PRESENT for {student.first_name}"
                else:
                    message = f"Attendance already marked for {student.first_name}"
            else:
                message = f"Attendance marked for {student.first_name}"
                
            return JsonResponse({
                'status': 'success',
                'message': message,
                'student': {
                    'name': f"{student.first_name} {student.last_name}",
                    'reg_no': student.reg_no,
                    'class': f"{school_class.name} - {section.name}",
                    'photo_url': student.photo.url if student.photo else None
                }
            })
            
        except Student.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': f'Student with Reg No {reg_no} not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

