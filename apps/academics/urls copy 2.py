from django.urls import path, include
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'academics'

# Dashboard URLs
dashboard_urls = [
    path('', views.AcademicsDashboardView.as_view(), name='dashboard'),
    path('dashboard-widgets/', views.DashboardWidgetsView.as_view(), name='dashboard_widgets'),
]

# Academic Year URLs
year_urls = [
    path('', views.AcademicYearListView.as_view(), name='year_list'),
    path('create/', views.AcademicYearCreateView.as_view(), name='year_create'),
    path('<uuid:pk>/', views.AcademicYearDetailView.as_view(), name='year_detail'),
    path('<uuid:pk>/update/', views.AcademicYearUpdateView.as_view(), name='year_update'),
    path('<uuid:pk>/delete/', views.AcademicYearDeleteView.as_view(), name='year_delete'),
]

# Term URLs
term_urls = [
    path('', views.TermListView.as_view(), name='term_list'),
    path('create/', views.TermCreateView.as_view(), name='term_create'),
    path('<uuid:pk>/update/', views.TermUpdateView.as_view(), name='term_update'),
    path('<uuid:pk>/delete/', views.TermDeleteView.as_view(), name='term_delete'),
]

# Class URLs
class_urls = [
    path('', views.SchoolClassListView.as_view(), name='class_list'),
    path('create/', views.SchoolClassCreateView.as_view(), name='class_create'),
    path('<uuid:pk>/', views.SchoolClassDetailView.as_view(), name='class_detail'),
    path('<uuid:pk>/update/', views.SchoolClassUpdateView.as_view(), name='class_update'),
    path('<uuid:pk>/delete/', views.SchoolClassDeleteView.as_view(), name='class_delete'),
]

# Section URLs
section_urls = [
    path('', views.SectionListView.as_view(), name='section_list'),
    path('create/', views.SectionCreateView.as_view(), name='section_create'),
    path('<uuid:pk>/update/', views.SectionUpdateView.as_view(), name='section_update'),
    path('<uuid:pk>/delete/', views.SectionDeleteView.as_view(), name='section_delete'),
]

# Subject URLs
subject_urls = [
    path('', views.SubjectListView.as_view(), name='subject_list'),
    path('create/', views.SubjectCreateView.as_view(), name='subject_create'),
    path('<uuid:pk>/update/', views.SubjectUpdateView.as_view(), name='subject_update'),
    path('<uuid:pk>/delete/', views.SubjectDeleteView.as_view(), name='subject_delete'),
]

# Class Subject URLs
classsubject_urls = [
    path('', views.ClassSubjectListView.as_view(), name='classsubject_list'),
    path('create/', views.ClassSubjectCreateView.as_view(), name='classsubject_create'),
    path('<uuid:pk>/update/', views.ClassSubjectUpdateView.as_view(), name='classsubject_update'),
    path('<uuid:pk>/delete/', views.ClassSubjectDeleteView.as_view(), name='classsubject_delete'),
]

# Timetable URLs
timetable_urls = [
    path('', views.TimeTableListView.as_view(), name='timetable_list'),
    path('create/', views.TimeTableCreateView.as_view(), name='timetable_create'),
    path('<uuid:pk>/update/', views.TimeTableUpdateView.as_view(), name='timetable_update'),
    path('<uuid:pk>/delete/', views.TimeTableDeleteView.as_view(), name='timetable_delete'),
    path('weekly/', views.TimeTableWeeklyView.as_view(), name='timetable_weekly'),
]

# Attendance URLs
attendance_urls = [
    path('', views.AttendanceListView.as_view(), name='attendance_list'),
    path('create/', views.AttendanceCreateView.as_view(), name='attendance_create'),
    path('bulk/', views.AttendanceBulkCreateView.as_view(), name='attendance_bulk'),
    path('report/', views.AttendanceReportView.as_view(), name='attendance_report'),
    path('export-csv/', views.ExportAttendanceCSVView.as_view(), name='attendance_export_csv'),
    path('<uuid:pk>/update/', views.AttendanceUpdateView.as_view(), name='attendance_update'),
    path('<uuid:pk>/delete/', views.AttendanceDeleteView.as_view(), name='attendance_delete'),
]

# Holiday URLs
holiday_urls = [
    path('', views.HolidayListView.as_view(), name='holiday_list'),
    path('calendar/', views.HolidayCalendarView.as_view(), name='holiday_calendar'),
    path('create/', views.HolidayCreateView.as_view(), name='holiday_create'),
    path('<uuid:pk>/', views.HolidayDetailView.as_view(), name='holiday_detail'),
    path('<uuid:pk>/update/', views.HolidayUpdateView.as_view(), name='holiday_update'),
    path('<uuid:pk>/delete/', views.HolidayDeleteView.as_view(), name='holiday_delete'),
]

# Study Material URLs
studymaterial_urls = [
    path('', views.StudyMaterialListView.as_view(), name='studymaterial_list'),
    path('create/', views.StudyMaterialCreateView.as_view(), name='studymaterial_create'),
    path('<uuid:pk>/', views.StudyMaterialDetailView.as_view(), name='studymaterial_detail'),
    path('<uuid:pk>/update/', views.StudyMaterialUpdateView.as_view(), name='studymaterial_update'),
    path('<uuid:pk>/delete/', views.StudyMaterialDeleteView.as_view(), name='studymaterial_delete'),
    path('<uuid:pk>/download/', views.StudyMaterialDownloadView.as_view(), name='studymaterial_download'),
]

# Syllabus URLs
syllabus_urls = [
    path('', views.SyllabusListView.as_view(), name='syllabus_list'),
    path('create/', views.SyllabusCreateView.as_view(), name='syllabus_create'),
    path('<uuid:pk>/update/', views.SyllabusUpdateView.as_view(), name='syllabus_update'),
    path('<uuid:pk>/delete/', views.SyllabusDeleteView.as_view(), name='syllabus_delete'),
]

# House URLs
house_urls = [
    path('', views.HouseListView.as_view(), name='house_list'),
    path('create/', views.HouseCreateView.as_view(), name='house_create'),
    path('<uuid:pk>/', views.HouseDetailView.as_view(), name='house_detail'),
    path('<uuid:pk>/update/', views.HouseUpdateView.as_view(), name='house_update'),
    path('<uuid:pk>/delete/', views.HouseDeleteView.as_view(), name='house_delete'),
]

# House Points URLs
housepoints_urls = [
    path('create/', views.HousePointsCreateView.as_view(), name='housepoints_create'),
    path('<uuid:pk>/update/', views.HousePointsUpdateView.as_view(), name='housepoints_update'),
    path('<uuid:pk>/delete/', views.HousePointsDeleteView.as_view(), name='housepoints_delete'),
]

# Stream URLs
stream_urls = [
    path('', views.StreamListView.as_view(), name='stream_list'),
    path('create/', views.StreamCreateView.as_view(), name='stream_create'),
    path('<uuid:pk>/update/', views.StreamUpdateView.as_view(), name='stream_update'),
    path('<uuid:pk>/delete/', views.StreamDeleteView.as_view(), name='stream_delete'),
]

# Class Teacher URLs
classteacher_urls = [
    path('', views.ClassTeacherListView.as_view(), name='classteacher_list'),
    path('create/', views.ClassTeacherCreateView.as_view(), name='classteacher_create'),
    path('<uuid:pk>/update/', views.ClassTeacherUpdateView.as_view(), name='classteacher_update'),
    path('<uuid:pk>/delete/', views.ClassTeacherDeleteView.as_view(), name='classteacher_delete'),
]

# API URLs
api_urls = [
    path('get-sections/', views.GetSectionsByClassView.as_view(), name='get_sections'),
    path('get-subjects/', views.GetSubjectsByClassView.as_view(), name='get_subjects'),
    path('get-timetable/', views.GetTimeTableByClassSectionView.as_view(), name='get_timetable'),
    path('attendance-stats/', views.AttendanceStatisticsView.as_view(), name='attendance_stats'),
]

# Utility URLs
utility_urls = [
    path('academic-calendar/', views.AcademicCalendarView.as_view(), name='academic_calendar'),
]

urlpatterns = [
    # Dashboard
    path('dashboard/', include(dashboard_urls)),
    
    # Main URLs with app prefix
    path('academic-years/', include(year_urls)),
    path('terms/', include(term_urls)),
    path('classes/', include(class_urls)),
    path('sections/', include(section_urls)),
    path('subjects/', include(subject_urls)),
    path('class-subjects/', include(classsubject_urls)),
    path('timetable/', include(timetable_urls)),
    path('attendance/', include(attendance_urls)),
    path('holidays/', include(holiday_urls)),
    path('study-materials/', include(studymaterial_urls)),
    path('syllabus/', include(syllabus_urls)),
    path('houses/', include(house_urls)),
    path('house-points/', include(housepoints_urls)),
    path('streams/', include(stream_urls)),
    path('class-teachers/', include(classteacher_urls)),
    
    # API URLs
    path('api/', include(api_urls)),
    
    # Utility URLs
    path('utilities/', include(utility_urls)),
    
    # Redirect root to dashboard
    path('', views.AcademicsDashboardView.as_view(), name='index'),
]