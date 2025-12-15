"""
Academic Management URLs
"""
from django.urls import path
from apps.academics import views

app_name = 'academics'

urlpatterns = [
    # ============================================================================
    # DASHBOARD AND REPORTS
    # ============================================================================
    path('dashboard/', views.AcademicsDashboardView.as_view(), name='dashboard'),
    path('reports/', views.AcademicsReportsView.as_view(), name='reports'),
    
    # ============================================================================
    # ACADEMIC YEAR URLs
    # ============================================================================
    path('academic-years/', views.AcademicYearListView.as_view(), name='academic_year_list'),
    path('academic-years/<uuid:pk>/', views.AcademicYearDetailView.as_view(), name='academic_year_detail'),
    path('academic-years/create/', views.AcademicYearCreateView.as_view(), name='academic_year_create'),
    path('academic-years/<uuid:pk>/update/', views.AcademicYearUpdateView.as_view(), name='academic_year_update'),
    path('academic-years/<uuid:pk>/delete/', views.AcademicYearDeleteView.as_view(), name='academic_year_delete'),
    path('academic-years/set-current/', views.SetCurrentAcademicYearView.as_view(), name='set_current_academic_year'),
    
    # ============================================================================
    # TERM URLs
    # ============================================================================
    path('terms/', views.TermListView.as_view(), name='term_list'),
    path('terms/<uuid:pk>/', views.TermDetailView.as_view(), name='term_detail'),
    path('terms/create/', views.TermCreateView.as_view(), name='term_create'),
    path('terms/<uuid:pk>/update/', views.TermUpdateView.as_view(), name='term_update'),
    path('terms/<uuid:pk>/delete/', views.TermDeleteView.as_view(), name='term_delete'),
    path('terms/set-current/', views.SetCurrentTermView.as_view(), name='set_current_term'),
    
    # ============================================================================
    # SCHOOL CLASS URLs
    # ============================================================================
    path('classes/', views.SchoolClassListView.as_view(), name='class_list'),
    path('classes/<uuid:pk>/', views.SchoolClassDetailView.as_view(), name='class_detail'),
    path('classes/create/', views.SchoolClassCreateView.as_view(), name='class_create'),
    path('classes/<uuid:pk>/update/', views.SchoolClassUpdateView.as_view(), name='class_update'),
    path('classes/<uuid:pk>/delete/', views.SchoolClassDeleteView.as_view(), name='class_delete'),
    
    # ============================================================================
    # SECTION URLs
    # ============================================================================
    path('sections/', views.SectionListView.as_view(), name='section_list'),
    path('sections/<uuid:pk>/', views.SectionDetailView.as_view(), name='section_detail'),
    path('sections/create/', views.SectionCreateView.as_view(), name='section_create'),
    path('sections/<uuid:pk>/update/', views.SectionUpdateView.as_view(), name='section_update'),
    path('sections/<uuid:pk>/delete/', views.SectionDeleteView.as_view(), name='section_delete'),
    
    # ============================================================================
    # HOUSE URLs
    # ============================================================================
    path('houses/', views.HouseListView.as_view(), name='house_list'),
    path('houses/<uuid:pk>/', views.HouseDetailView.as_view(), name='house_detail'),
    path('houses/create/', views.HouseCreateView.as_view(), name='house_create'),
    path('houses/<uuid:pk>/update/', views.HouseUpdateView.as_view(), name='house_update'),
    path('houses/<uuid:pk>/delete/', views.HouseDeleteView.as_view(), name='house_delete'),
    
    # ============================================================================
    # HOUSE POINTS URLs
    # ============================================================================
    path('house-points/', views.HousePointsListView.as_view(), name='house_points_list'),
    path('house-points/create/', views.HousePointsCreateView.as_view(), name='house_points_create'),
    path('house-points/<uuid:pk>/delete/', views.HousePointsDeleteView.as_view(), name='house_points_delete'),
    
    # ============================================================================
    # SUBJECT URLs
    # ============================================================================
    path('subjects/', views.SubjectListView.as_view(), name='subject_list'),
    path('subjects/<uuid:pk>/', views.SubjectDetailView.as_view(), name='subject_detail'),
    path('subjects/create/', views.SubjectCreateView.as_view(), name='subject_create'),
    path('subjects/<uuid:pk>/update/', views.SubjectUpdateView.as_view(), name='subject_update'),
    path('subjects/<uuid:pk>/delete/', views.SubjectDeleteView.as_view(), name='subject_delete'),
    
    # ============================================================================
    # CLASS SUBJECT URLs
    # ============================================================================
    path('class-subjects/', views.ClassSubjectListView.as_view(), name='class_subject_list'),
    path('class-subjects/create/', views.ClassSubjectCreateView.as_view(), name='class_subject_create'),
    path('class-subjects/<uuid:pk>/update/', views.ClassSubjectUpdateView.as_view(), name='class_subject_update'),
    path('class-subjects/<uuid:pk>/delete/', views.ClassSubjectDeleteView.as_view(), name='class_subject_delete'),
    
    # ============================================================================
    # TIMETABLE URLs
    # ============================================================================
    path('timetable/', views.TimeTableListView.as_view(), name='timetable_list'),
    path('timetable/create/', views.TimeTableCreateView.as_view(), name='timetable_create'),
    path('timetable/<uuid:pk>/update/', views.TimeTableUpdateView.as_view(), name='timetable_update'),
    path('timetable/<uuid:pk>/delete/', views.TimeTableDeleteView.as_view(), name='timetable_delete'),
    path('timetable/by-class/', views.TimeTableByClassView.as_view(), name='timetable_by_class'),
    
    # ============================================================================
    # ATTENDANCE URLs
    # ============================================================================
    path('attendance/', views.StudentAttendanceListView.as_view(), name='attendance_list'),
    path('attendance/create/', views.StudentAttendanceCreateView.as_view(), name='attendance_create'),
    path('attendance/<uuid:pk>/update/', views.StudentAttendanceUpdateView.as_view(), name='attendance_update'),
    path('attendance/<uuid:pk>/delete/', views.StudentAttendanceDeleteView.as_view(), name='attendance_delete'),
    path('attendance/bulk/', views.BulkAttendanceView.as_view(), name='bulk_attendance'),
    
    # ============================================================================
    # HOLIDAY URLs
    # ============================================================================
    path('holidays/', views.HolidayListView.as_view(), name='holiday_list'),
    path('holidays/<uuid:pk>/', views.HolidayDetailView.as_view(), name='holiday_detail'),
    path('holidays/create/', views.HolidayCreateView.as_view(), name='holiday_create'),
    path('holidays/<uuid:pk>/update/', views.HolidayUpdateView.as_view(), name='holiday_update'),
    path('holidays/<uuid:pk>/delete/', views.HolidayDeleteView.as_view(), name='holiday_delete'),
    
    # ============================================================================
    # STUDY MATERIAL URLs
    # ============================================================================
    path('study-materials/', views.StudyMaterialListView.as_view(), name='study_material_list'),
    path('study-materials/<uuid:pk>/', views.StudyMaterialDetailView.as_view(), name='study_material_detail'),
    path('study-materials/create/', views.StudyMaterialCreateView.as_view(), name='study_material_create'),
    path('study-materials/<uuid:pk>/update/', views.StudyMaterialUpdateView.as_view(), name='study_material_update'),
    path('study-materials/<uuid:pk>/delete/', views.StudyMaterialDeleteView.as_view(), name='study_material_delete'),
    
    # ============================================================================
    # SYLLABUS URLs
    # ============================================================================
    path('syllabus/', views.SyllabusListView.as_view(), name='syllabus_list'),
    path('syllabus/<uuid:pk>/', views.SyllabusDetailView.as_view(), name='syllabus_detail'),
    path('syllabus/create/', views.SyllabusCreateView.as_view(), name='syllabus_create'),
    path('syllabus/<uuid:pk>/update/', views.SyllabusUpdateView.as_view(), name='syllabus_update'),
    path('syllabus/<uuid:pk>/delete/', views.SyllabusDeleteView.as_view(), name='syllabus_delete'),
    
    # ============================================================================
    # STREAM URLs
    # ============================================================================
    path('streams/', views.StreamListView.as_view(), name='stream_list'),
    path('streams/<uuid:pk>/', views.StreamDetailView.as_view(), name='stream_detail'),
    path('streams/create/', views.StreamCreateView.as_view(), name='stream_create'),
    path('streams/<uuid:pk>/update/', views.StreamUpdateView.as_view(), name='stream_update'),
    path('streams/<uuid:pk>/delete/', views.StreamDeleteView.as_view(), name='stream_delete'),
    
    # ============================================================================
    # CLASS TEACHER URLs
    # ============================================================================
    path('class-teachers/', views.ClassTeacherListView.as_view(), name='class_teacher_list'),
    path('class-teachers/create/', views.ClassTeacherCreateView.as_view(), name='class_teacher_create'),
    path('class-teachers/<uuid:pk>/update/', views.ClassTeacherUpdateView.as_view(), name='class_teacher_update'),
    path('class-teachers/<uuid:pk>/delete/', views.ClassTeacherDeleteView.as_view(), name='class_teacher_delete'),
    
    # ============================================================================
    # GRADING SYSTEM URLs
    # ============================================================================
    path('grading-systems/', views.GradingSystemListView.as_view(), name='grading_system_list'),
    path('grading-systems/<uuid:pk>/', views.GradingSystemDetailView.as_view(), name='grading_system_detail'),
    path('grading-systems/create/', views.GradingSystemCreateView.as_view(), name='grading_system_create'),
    path('grading-systems/<uuid:pk>/update/', views.GradingSystemUpdateView.as_view(), name='grading_system_update'),
    path('grading-systems/<uuid:pk>/delete/', views.GradingSystemDeleteView.as_view(), name='grading_system_delete'),
    path('grading-systems/set-default/', views.SetDefaultGradingSystemView.as_view(), name='set_default_grading_system'),
    
    # ============================================================================
    # GRADE URLs
    # ============================================================================
    path('grades/', views.GradeListView.as_view(), name='grade_list'),
    path('grades/create/', views.GradeCreateView.as_view(), name='grade_create'),
    path('grades/<uuid:pk>/update/', views.GradeUpdateView.as_view(), name='grade_update'),
    path('grades/<uuid:pk>/delete/', views.GradeDeleteView.as_view(), name='grade_delete'),
    
    # ============================================================================
    # AJAX ENDPOINTS
    # ============================================================================
    path('ajax/load-sections/', views.load_sections, name='ajax_load_sections'),
    path('ajax/load-subjects/', views.load_subjects, name='ajax_load_subjects'),
    path('api/students-by-class-section/', views.BulkAttendanceView.as_view(), name='api_students_by_class_section'),
]