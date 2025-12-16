# apps/hr/urls.py
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'hr'

urlpatterns = [
    # ==================== DASHBOARD & HOME ====================
    path('', login_required(views.HRDashboardView.as_view()), name='dashboard'),
    path('dashboard/', login_required(views.HRDashboardView.as_view()), name='dashboard_alt'),
    
    # ==================== STAFF MANAGEMENT ====================
    path('staff/', include([
        path('', login_required(views.StaffListView.as_view()), name='staff_list'),
        path('import/', login_required(views.StaffImportView.as_view()), name='staff_import'),
        path('import/sample/', login_required(views.StaffImportSampleView.as_view()), name='staff_import_sample'),
        path('create/', login_required(views.StaffCreateView.as_view()), name='staff_create'),
        path('<uuid:pk>/', include([
            path('', login_required(views.StaffDetailView.as_view()), name='staff_detail'),
            path('edit/', login_required(views.StaffUpdateView.as_view()), name='staff_update'),
            path('delete/', login_required(views.StaffDeleteView.as_view()), name='staff_delete'),
            path('id-card/', login_required(views.StaffIDCardView.as_view()), name='staff_id_card'),
            
            # Staff-specific sub-pages
            path('attendance/', login_required(views.StaffAttendanceView.as_view()), name='staff_attendance'),
            path('leaves/', login_required(views.StaffLeavesView.as_view()), name='staff_leaves'),
            path('documents/', login_required(views.StaffDocumentsView.as_view()), name='staff_documents'),
            path('salary/', login_required(views.StaffSalaryView.as_view()), name='staff_salary'),
            path('performance/', login_required(views.StaffPerformanceView.as_view()), name='staff_performance'),
        ])),
        path('export/', login_required(views.StaffExportView.as_view()), name='staff_export'),
    ])),
    
    # ==================== DEPARTMENT MANAGEMENT ====================
    path('departments/', include([
        path('', login_required(views.DepartmentListView.as_view()), name='department_list'),
        path('create/', login_required(views.DepartmentCreateView.as_view()), name='department_create'),
        path('<uuid:pk>/', include([
            path('', login_required(views.DepartmentDetailView.as_view()), name='department_detail'),
            path('edit/', login_required(views.DepartmentUpdateView.as_view()), name='department_update'),
            path('delete/', login_required(views.DepartmentDeleteView.as_view()), name='department_delete'),
        ])),
    ])),
    
    # ==================== DESIGNATION MANAGEMENT ====================
    path('designations/', include([
        path('', login_required(views.DesignationListView.as_view()), name='designation_list'),
        path('create/', login_required(views.DesignationCreateView.as_view()), name='designation_create'),
        path('<uuid:pk>/', include([
            path('', login_required(views.DesignationDetailView.as_view()), name='designation_detail'),
            path('edit/', login_required(views.DesignationUpdateView.as_view()), name='designation_update'),
            path('delete/', login_required(views.DesignationDeleteView.as_view()), name='designation_delete'),
        ])),
    ])),
    
    # ==================== QUALIFICATION MANAGEMENT ====================
    path('qualifications/', include([
        path('', login_required(views.QualificationListView.as_view()), name='qualification_list'),
        path('create/', login_required(views.QualificationCreateView.as_view()), name='qualification_create'),
        path('<uuid:pk>/', include([
            path('edit/', login_required(views.QualificationUpdateView.as_view()), name='qualification_update'),
            path('delete/', login_required(views.QualificationDeleteView.as_view()), name='qualification_delete'),
        ])),
    ])),
    
    # ==================== ATTENDANCE MANAGEMENT ====================
    path('attendance/', include([
        path('', login_required(views.AttendanceListView.as_view()), name='attendance_list'),
        path('mark/', login_required(views.AttendanceBulkCreateView.as_view()), name='attendance_mark'),
        path('daily/', login_required(views.AttendanceDailyView.as_view()), name='attendance_daily'),
        path('monthly/', login_required(views.AttendanceMonthlyView.as_view()), name='attendance_monthly'),
        path('<uuid:pk>/', include([
            path('edit/', login_required(views.AttendanceUpdateView.as_view()), name='attendance_update'),
            path('delete/', login_required(views.AttendanceDeleteView.as_view()), name='attendance_delete'),
        ])),
    ])),
    
    # ==================== LEAVE MANAGEMENT ====================
    path('leaves/', include([
        path('', login_required(views.LeaveApplicationListView.as_view()), name='leave_list'),
        path('apply/', login_required(views.LeaveApplicationCreateView.as_view()), name='leave_apply'),
        path('types/', login_required(views.LeaveTypeListView.as_view()), name='leavetype_list'),
        path('types/create/', login_required(views.LeaveTypeCreateView.as_view()), name='leavetype_create'),
        path('types/<uuid:pk>/', include([
            path('edit/', login_required(views.LeaveTypeUpdateView.as_view()), name='leavetype_update'),
            path('delete/', login_required(views.LeaveTypeDeleteView.as_view()), name='leavetype_delete'),
        ])),
        path('<uuid:pk>/', include([
            path('', login_required(views.LeaveApplicationDetailView.as_view()), name='leave_detail'),
            path('edit/', login_required(views.LeaveApplicationUpdateView.as_view()), name='leave_update'),
            path('delete/', login_required(views.LeaveApplicationDeleteView.as_view()), name='leave_delete'),
            path('approve/', login_required(views.LeaveApplicationApproveView.as_view()), name='leave_approve'),
            path('cancel/', login_required(views.LeaveApplicationCancelView.as_view()), name='leave_cancel'),
        ])),
        path('balances/', login_required(views.LeaveBalanceListView.as_view()), name='leavebalance_list'),
    ])),
    
    # ==================== PAYROLL MANAGEMENT ====================
    path('payroll/', include([
        path('', login_required(views.PayrollListView.as_view()), name='payroll_list'),
        path('generate/', login_required(views.PayrollGenerateView.as_view()), name='payroll_generate'),
        path('process/', login_required(views.PayrollProcessView.as_view()), name='payroll_process'),
        path('structures/', login_required(views.SalaryStructureListView.as_view()), name='salarystructure_list'),
        path('structures/create/', login_required(views.SalaryStructureCreateView.as_view()), name='salarystructure_create'),
        path('structures/<uuid:pk>/', include([
            path('edit/', login_required(views.SalaryStructureUpdateView.as_view()), name='salarystructure_update'),
            path('delete/', login_required(views.SalaryStructureDeleteView.as_view()), name='salarystructure_delete'),
        ])),
        path('<uuid:pk>/', include([
            path('', login_required(views.PayrollDetailView.as_view()), name='payroll_detail'),
            path('edit/', login_required(views.PayrollUpdateView.as_view()), name='payroll_update'),
            path('delete/', login_required(views.PayrollDeleteView.as_view()), name='payroll_delete'),
            path('approve/', login_required(views.PayrollApproveView.as_view()), name='payroll_approve'),
            path('payslip/', login_required(views.PayrollPayslipView.as_view()), name='payroll_payslip'),
        ])),
        path('reports/', include([
            path('monthly/', login_required(views.PayrollMonthlyReportView.as_view()), name='payroll_report_monthly'),
            path('annual/', login_required(views.PayrollAnnualReportView.as_view()), name='payroll_report_annual'),
            path('department/', login_required(views.PayrollDepartmentReportView.as_view()), name='payroll_report_department'),
        ])),
    ])),
    
    # ==================== RECRUITMENT MANAGEMENT ====================
    path('recruitment/', include([
        path('', login_required(views.RecruitmentListView.as_view()), name='recruitment_list'),
        path('create/', login_required(views.RecruitmentCreateView.as_view()), name='recruitment_create'),
        path('<uuid:pk>/', include([
            path('', login_required(views.RecruitmentDetailView.as_view()), name='recruitment_detail'),
            path('edit/', login_required(views.RecruitmentUpdateView.as_view()), name='recruitment_update'),
            path('delete/', login_required(views.RecruitmentDeleteView.as_view()), name='recruitment_delete'),
            path('close/', login_required(views.RecruitmentCloseView.as_view()), name='recruitment_close'),
        ])),
        path('applications/', include([
            path('', login_required(views.JobApplicationListView.as_view()), name='jobapplication_list'),
            path('create/', login_required(views.JobApplicationCreateView.as_view()), name='jobapplication_create'),
            path('<uuid:pk>/', include([
                path('', login_required(views.JobApplicationDetailView.as_view()), name='jobapplication_detail'),
                path('edit/', login_required(views.JobApplicationUpdateView.as_view()), name='jobapplication_update'),
                path('delete/', login_required(views.JobApplicationDeleteView.as_view()), name='jobapplication_delete'),
                path('shortlist/', login_required(views.JobApplicationShortlistView.as_view()), name='jobapplication_shortlist'),
                path('interview/', login_required(views.JobApplicationInterviewView.as_view()), name='jobapplication_interview'),
                path('offer/', login_required(views.JobApplicationOfferView.as_view()), name='jobapplication_offer'),
                path('reject/', login_required(views.JobApplicationRejectView.as_view()), name='jobapplication_reject'),
            ])),
        ])),
    ])),
    
    # ==================== TRAINING & DEVELOPMENT ====================
    path('training/', include([
        path('', login_required(views.TrainingProgramListView.as_view()), name='trainingprogram_list'),
        path('create/', login_required(views.TrainingProgramCreateView.as_view()), name='trainingprogram_create'),
        path('<uuid:pk>/', include([
            path('', login_required(views.TrainingProgramDetailView.as_view()), name='trainingprogram_detail'),
            path('edit/', login_required(views.TrainingProgramUpdateView.as_view()), name='trainingprogram_update'),
            path('delete/', login_required(views.TrainingProgramDeleteView.as_view()), name='trainingprogram_delete'),
            path('register/', login_required(views.TrainingRegisterView.as_view()), name='training_register'),
            path('participants/', login_required(views.TrainingParticipantsView.as_view()), name='training_participants'),
        ])),
        path('participations/', include([
            path('', login_required(views.TrainingParticipationListView.as_view()), name='trainingparticipation_list'),
            path('create/', login_required(views.TrainingParticipationCreateView.as_view()), name='trainingparticipation_create'),
            path('<uuid:pk>/', include([
                path('edit/', login_required(views.TrainingParticipationUpdateView.as_view()), name='trainingparticipation_update'),
                path('delete/', login_required(views.TrainingParticipationDeleteView.as_view()), name='trainingparticipation_delete'),
                path('certificate/', login_required(views.TrainingCertificateView.as_view()), name='training_certificate'),
            ])),
        ])),
    ])),
    
    # ==================== PERFORMANCE MANAGEMENT ====================
    path('performance/', include([
        path('', login_required(views.PerformanceReviewListView.as_view()), name='performancereview_list'),
        path('create/', login_required(views.PerformanceReviewCreateView.as_view()), name='performancereview_create'),
        path('<uuid:pk>/', include([
            path('', login_required(views.PerformanceReviewDetailView.as_view()), name='performancereview_detail'),
            path('edit/', login_required(views.PerformanceReviewUpdateView.as_view()), name='performancereview_update'),
            path('delete/', login_required(views.PerformanceReviewDeleteView.as_view()), name='performancereview_delete'),
            path('acknowledge/', login_required(views.PerformanceAcknowledgeView.as_view()), name='performance_acknowledge'),
        ])),
        path('templates/', login_required(views.PerformanceTemplateListView.as_view()), name='performancetemplate_list'),
        path('goals/', login_required(views.PerformanceGoalListView.as_view()), name='performancegoal_list'),
        path('reports/', login_required(views.PerformanceReportView.as_view()), name='performance_report'),
    ])),
    
    # ==================== EMPLOYMENT HISTORY ====================
    path('history/', include([
        path('', login_required(views.EmploymentHistoryListView.as_view()), name='employmenthistory_list'),
        path('create/', login_required(views.EmploymentHistoryCreateView.as_view()), name='employmenthistory_create'),
        path('promotions/', login_required(views.PromotionListView.as_view()), name='promotion_list'),
        path('promotions/create/', login_required(views.PromotionCreateView.as_view()), name='promotion_create'),
        path('promotions/<uuid:pk>/', include([
            path('edit/', login_required(views.PromotionUpdateView.as_view()), name='promotion_update'),
            path('delete/', login_required(views.PromotionDeleteView.as_view()), name='promotion_delete'),
        ])),
        path('transfers/', login_required(views.TransferListView.as_view()), name='transfer_list'),
    ])),
    
    # ==================== REPORTS & ANALYTICS ====================
    path('reports/', include([
        path('staff/', login_required(views.StaffReportView.as_view()), name='report_staff'),
        path('staff/pdf/', login_required(views.StaffReportPDFView.as_view()), name='report_staff_pdf'),
        path('attendance/', login_required(views.AttendanceReportView.as_view()), name='report_attendance'),
        path('leave/', login_required(views.LeaveReportView.as_view()), name='report_leave'),
        path('turnover/', login_required(views.TurnoverReportView.as_view()), name='report_turnover'),
        path('demographic/', login_required(views.DemographicReportView.as_view()), name='report_demographic'),
        path('salary-analysis/', login_required(views.SalaryAnalysisView.as_view()), name='report_salary'),
    ])),
    
    # ==================== API ENDPOINTS ====================
    path('api/', include([
        path('staff/autocomplete/', login_required(views.StaffAutocompleteView.as_view()), name='api_staff_autocomplete'),
        path('leave/check-balance/', login_required(views.LeaveBalanceCheckView.as_view()), name='api_leave_check_balance'),
        path('attendance/daily-summary/', login_required(views.AttendanceDailySummaryView.as_view()), name='api_attendance_daily'),
        path('payroll/summary/', login_required(views.PayrollSummaryView.as_view()), name='api_payroll_summary'),
        path('dashboard/widgets/', login_required(views.HRDashboardWidgetsView.as_view()), name='api_dashboard_widgets'),
        path('reports/generate/', login_required(views.ReportGenerateView.as_view()), name='api_report_generate'),
    ])),
    
    # ==================== DOCUMENTS & UPLOADS ====================
    path('documents/', include([
        path('', login_required(views.StaffDocumentListView.as_view()), name='staffdocument_list'),
        path('upload/', login_required(views.StaffDocumentUploadView.as_view()), name='staffdocument_upload'),
        path('<uuid:pk>/', include([
            path('view/', login_required(views.StaffDocumentViewView.as_view()), name='staffdocument_view'),
            path('delete/', login_required(views.StaffDocumentDeleteView.as_view()), name='staffdocument_delete'),
            path('verify/', login_required(views.StaffDocumentVerifyView.as_view()), name='staffdocument_verify'),
        ])),
    ])),
    
    # ==================== ADDRESS MANAGEMENT ====================
    path('addresses/', include([
        path('', login_required(views.StaffAddressListView.as_view()), name='staffaddress_list'),
        path('create/', login_required(views.StaffAddressCreateView.as_view()), name='staffaddress_create'),
        path('<uuid:pk>/', include([
            path('edit/', login_required(views.StaffAddressUpdateView.as_view()), name='staffaddress_update'),
            path('delete/', login_required(views.StaffAddressDeleteView.as_view()), name='staffaddress_delete'),
        ])),
    ])),
    
    # ==================== SETTINGS & CONFIGURATION ====================
    path('settings/', include([
        path('', login_required(views.HRSettingsView.as_view()), name='hr_settings'),
        path('holidays/', login_required(views.HolidayListView.as_view()), name='holiday_list'),
        path('holidays/create/', login_required(views.HolidayCreateView.as_view()), name='holiday_create'),
        path('holidays/<uuid:pk>/edit/', login_required(views.HolidayUpdateView.as_view()), name='holiday_update'),
        path('holidays/<uuid:pk>/delete/', login_required(views.HolidayDeleteView.as_view()), name='holiday_delete'),
        path('work-schedule/', login_required(views.WorkScheduleView.as_view()), name='work_schedule'),
        path('work-schedule/create/', login_required(views.WorkScheduleCreateView.as_view()), name='work_schedule_create'),
        path('work-schedule/<uuid:pk>/edit/', login_required(views.WorkScheduleUpdateView.as_view()), name='work_schedule_update'),
        path('work-schedule/<uuid:pk>/delete/', login_required(views.WorkScheduleDeleteView.as_view()), name='work_schedule_delete'),
        path('tax-config/', login_required(views.TaxConfigView.as_view()), name='tax_config'),
        path('pf-esi/', login_required(views.PFESIConfigView.as_view()), name='pf_esi_config'),
    ])),
]