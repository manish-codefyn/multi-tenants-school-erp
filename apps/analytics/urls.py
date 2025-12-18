from django.urls import path, include
from . import views

app_name = 'analytics'

urlpatterns = [
    # Main Dashboards
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    path('audit/', views.AuditDashboardView.as_view(), name='audit_dashboard'),
    
    # Reports
    path('reports/', include([
        path('', views.ReportListView.as_view(), name='report_list'),
        path('create/', views.ReportCreateView.as_view(), name='report_create'),
        path('<uuid:pk>/', include([
            path('', views.ReportDetailView.as_view(), name='report_detail'),
            path('update/', views.ReportUpdateView.as_view(), name='report_update'),
            path('delete/', views.ReportDeleteView.as_view(), name='report_delete'),
            path('generate/', views.ReportGenerateView.as_view(), name='report_generate'),
        ])),
    ])),
    
    # KPIs
    path('kpis/', include([
        path('', views.KPIListView.as_view(), name='kpi_list'),
        path('create/', views.KPICreateView.as_view(), name='kpi_create'),
        path('<uuid:pk>/', include([
            path('', views.KPIDetailView.as_view(), name='kpi_detail'),
            path('update/', views.KPIUpdateView.as_view(), name='kpi_update'),
            path('delete/', views.KPIDeleteView.as_view(), name='kpi_delete'),
        ])),
    ])),
    
    # Data Sources
    path('data-sources/', include([
        path('', views.DataSourceListView.as_view(), name='datasource_list'),
        path('create/', views.DataSourceCreateView.as_view(), name='datasource_create'),
        path('<uuid:pk>/', include([
            path('', views.DataSourceDetailView.as_view(), name='datasource_detail'),
            path('update/', views.DataSourceUpdateView.as_view(), name='datasource_update'),
            path('delete/', views.DataSourceDeleteView.as_view(), name='datasource_delete'),
        ])),
    ])),
    
    # Dashboards
    path('dashboards/', include([
        path('', views.DashboardListView.as_view(), name='dashboard_list'),
        path('create/', views.DashboardCreateView.as_view(), name='dashboard_create'),
        path('<uuid:pk>/', include([
            path('', views.DashboardDetailView.as_view(), name='dashboard_detail'),
            path('update/', views.DashboardUpdateView.as_view(), name='dashboard_update'),
            path('delete/', views.DashboardDeleteView.as_view(), name='dashboard_delete'),
        ])),
    ])),
    
    # Widgets
    path('widgets/', include([
        path('create/', views.DashboardWidgetCreateView.as_view(), name='widget_create'),
        path('<uuid:pk>/', include([
            path('update/', views.DashboardWidgetUpdateView.as_view(), name='widget_update'),
            path('delete/', views.DashboardWidgetDeleteView.as_view(), name='widget_delete'),
        ])),
    ])),
    
    # Audit Reports
    path('audit/reports/', include([
        path('', views.AuditAnalysisReportListView.as_view(), name='audit_report_list'),
        path('create/', views.AuditAnalysisReportCreateView.as_view(), name='audit_report_create'),
        path('<uuid:pk>/', include([
            path('', views.AuditAnalysisReportDetailView.as_view(), name='audit_report_detail'),
            path('update/', views.AuditAnalysisReportUpdateView.as_view(), name='audit_report_update'),
            path('delete/', views.AuditAnalysisReportDeleteView.as_view(), name='audit_report_delete'),
        ])),
    ])),
    
    # Audit Patterns
    path('audit/patterns/', include([
        path('', views.AuditPatternListView.as_view(), name='audit_pattern_list'),
        path('create/', views.AuditPatternCreateView.as_view(), name='audit_pattern_create'),
        path('<uuid:pk>/', include([
            path('', views.AuditPatternDetailView.as_view(), name='audit_pattern_detail'),
            path('update/', views.AuditPatternUpdateView.as_view(), name='audit_pattern_update'),
            path('delete/', views.AuditPatternDeleteView.as_view(), name='audit_pattern_delete'),
        ])),
    ])),
    
    # Audit Alerts
    path('audit/alerts/', include([
        path('', views.AuditAlertListView.as_view(), name='audit_alert_list'),
        path('create/', views.AuditAlertCreateView.as_view(), name='audit_alert_create'),
        path('<uuid:pk>/', include([
            path('', views.AuditAlertDetailView.as_view(), name='audit_alert_detail'),
            path('update/', views.AuditAlertUpdateView.as_view(), name='audit_alert_update'),
            path('delete/', views.AuditAlertDeleteView.as_view(), name='audit_alert_delete'),
        ])),
    ])),
    
    # Predictive Models
    path('models/', include([
        path('', views.PredictiveModelListView.as_view(), name='prediction_list'),
        path('create/', views.PredictiveModelCreateView.as_view(), name='model_create'),
        path('<uuid:pk>/', include([
            path('', views.PredictiveModelDetailView.as_view(), name='model_detail'),
            path('update/', views.PredictiveModelUpdateView.as_view(), name='model_update'),
            path('delete/', views.PredictiveModelDeleteView.as_view(), name='model_delete'),
        ])),
    ])),
    
    # Student Performance Analytics
    path('student-performance/', include([
        path('', views.StudentPerformanceListView.as_view(), name='student_performance_list'),
        path('create/', views.StudentPerformanceCreateView.as_view(), name='student_performance_create'),
        path('<uuid:pk>/', include([
            path('', views.StudentPerformanceDetailView.as_view(), name='student_performance_detail'),
            path('update/', views.StudentPerformanceUpdateView.as_view(), name='student_performance_update'),
            path('delete/', views.StudentPerformanceDeleteView.as_view(), name='student_performance_delete'),
        ])),
    ])),
    
    # Institutional Analytics
    path('institutional/', include([
        path('', views.InstitutionalAnalyticsListView.as_view(), name='institutional_list'),
        path('create/', views.InstitutionalAnalyticsCreateView.as_view(), name='institutional_create'),
        path('<uuid:pk>/', include([
            path('', views.InstitutionalAnalyticsDetailView.as_view(), name='institutional_detail'),
            path('update/', views.InstitutionalAnalyticsUpdateView.as_view(), name='institutional_update'),
            path('delete/', views.InstitutionalAnalyticsDeleteView.as_view(), name='institutional_delete'),
        ])),
    ])),
    
    # API Endpoints
    path('api/kpi-values/', views.KPIValueListView.as_view(), name='api_kpi_values'),
    
    # History
    path('history/', include([
        path('executions/', views.ReportExecutionListView.as_view(), name='execution_list'),
    ])),
    
    # Audit Metrics
    path('audit/metrics/', include([
        path('', views.AuditMetricListView.as_view(), name='audit_metric_list'),
        path('create/', views.AuditMetricCreateView.as_view(), name='audit_metric_create'),
        path('<uuid:pk>/', include([
            path('update/', views.AuditMetricUpdateView.as_view(), name='audit_metric_update'),
            path('delete/', views.AuditMetricDeleteView.as_view(), name='audit_metric_delete'),
        ])),
    ])),
]