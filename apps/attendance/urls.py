# attendance/urls.py
from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Dashboard
    path('', views.AttendanceDashboardView.as_view(), name='dashboard'),
    
    # Student Attendance
    path('students/', views.StudentAttendanceListView.as_view(), name='student_list'),
    path('students/mark/', views.StudentAttendanceMarkView.as_view(), name='student_mark'),
    path('students/bulk-mark/', views.StudentBulkAttendanceMarkView.as_view(), name='student_bulk_mark'),
    path('api/students/', views.get_students_by_class, name='api_get_students'),
    path('students/my-attendance/', views.MyAttendanceView.as_view(), name='my_attendance'),
    path('students/<int:student_id>/report/', views.StudentAttendanceReportView.as_view(), name='student_report'),
    
    # Staff Attendance
    path('staff/', views.StaffAttendanceListView.as_view(), name='staff_list'),
    path('staff/mark/', views.StaffAttendanceMarkView.as_view(), name='staff_mark'),
    path('api/staff/', views.get_staff_by_department, name='api_get_staff'),
    path('api/verify-face/', views.verify_face_attendance, name='api_verify_face'),
    path('api/verify-student-face/', views.verify_student_face_attendance, name='api_verify_student_face'),
    path('staff/my-attendance/', views.StaffMyAttendanceView.as_view(), name='staff_my_attendance'),
    
    # General
    path('mark/', views.MarkAttendanceView.as_view(), name='mark_attendance'),
    path('report/', views.AttendanceReportView.as_view(), name='report'),
    path('qr-scan/', views.QRCodeAttendanceView.as_view(), name='qr_attendance'),
    
    # Analytics & Reports
    path('analytics/', views.AttendanceAnalyticsView.as_view(), name='analytics'),
    path('export/', views.AttendanceExportView.as_view(), name='export'),
    path('daily-report/', views.DailyAttendanceReportView.as_view(), name='daily_report'),
    path('monthly-report/', views.MonthlyAttendanceReportView.as_view(), name='monthly_report'),
]