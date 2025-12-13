from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('dashboard/', views.TeacherDashboardView.as_view(), name='teacher-dashboard'),
    
    # Academic Year URLs
    path('academic-years/', views.AcademicYearListView.as_view(), name='academic_year_list'),
    path('academic-years/create/', views.AcademicYearCreateView.as_view(), name='academic_year_create'),
    path('academic-years/<uuid:pk>/update/', views.AcademicYearUpdateView.as_view(), name='academic_year_update'),
    path('academic-years/<uuid:pk>/delete/', views.AcademicYearDeleteView.as_view(), name='academic_year_delete'),

    # Term URLs
    path('terms/', views.TermListView.as_view(), name='term_list'),
    path('terms/create/', views.TermCreateView.as_view(), name='term_create'),
    path('terms/<uuid:pk>/update/', views.TermUpdateView.as_view(), name='term_update'),
    path('terms/<uuid:pk>/delete/', views.TermDeleteView.as_view(), name='term_delete'),

    # Class URLs
    path('classes/', views.SchoolClassListView.as_view(), name='class_list'),
    path('classes/create/', views.SchoolClassCreateView.as_view(), name='class_create'),
    path('classes/<uuid:pk>/update/', views.SchoolClassUpdateView.as_view(), name='class_update'),
    path('classes/<uuid:pk>/delete/', views.SchoolClassDeleteView.as_view(), name='class_delete'),

    # Section URLs
    path('sections/', views.SectionListView.as_view(), name='section_list'),
    path('sections/create/', views.SectionCreateView.as_view(), name='section_create'),
    path('sections/<uuid:pk>/update/', views.SectionUpdateView.as_view(), name='section_update'),
    path('sections/<uuid:pk>/delete/', views.SectionDeleteView.as_view(), name='section_delete'),

    # Subject URLs
    path('subjects/', views.SubjectListView.as_view(), name='subject_list'),
    path('subjects/create/', views.SubjectCreateView.as_view(), name='subject_create'),
    path('subjects/<uuid:pk>/update/', views.SubjectUpdateView.as_view(), name='subject_update'),
    path('subjects/<uuid:pk>/delete/', views.SubjectDeleteView.as_view(), name='subject_delete'),

    # Staff/Teacher URLs
    path('schedule/', views.ScheduleView.as_view(), name='schedule'),
    path('attendance/', views.AttendanceView.as_view(), name='attendance'),
    path('grading/', views.GradingView.as_view(), name='grading'),
    path('assignments/', views.AssignmentsView.as_view(), name='assignments'),
    
    # Student URLs
    path('my-courses/', views.StudentCoursesView.as_view(), name='my_courses'),
    path('my-grades/', views.StudentGradesView.as_view(), name='my_grades'),
    path('my-attendance/', views.StudentAttendanceView.as_view(), name='my_attendance'),
    path('my-assignments/', views.StudentAssignmentsView.as_view(), name='my_assignments'),
    path('timetable/', views.TimetableView.as_view(), name='timetable'),
]
