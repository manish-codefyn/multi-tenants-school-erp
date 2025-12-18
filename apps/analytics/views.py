import logging
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, Sum, Avg, Max, Min
from django.db import models
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from apps.core.views import (
    BaseView, BaseListView, BaseDetailView, BaseCreateView, 
    BaseUpdateView, BaseDeleteView, BaseTemplateView
)
from apps.core.utils.tenant import get_current_tenant
from apps.core.utils.audit import audit_log

from .models import (
    # Analytics models
    Report, KPIModel, DataSource, Dashboard, DashboardWidget,
    ReportExecution, KPIValue, PredictiveModel,
    StudentPerformanceAnalytics, InstitutionalAnalytics,
    
    # Audit models
    AuditAnalysisReport, AuditPattern, AuditAlert, AuditDashboard,
    AuditMetric, AuditMetricValue
)

from .forms import (
    # Analytics forms
    ReportForm, KPIForm, DataSourceForm, DashboardForm, DashboardWidgetForm,
    ReportExecutionForm, KPIValueForm, PredictiveModelForm,
    StudentPerformanceAnalyticsForm, InstitutionalAnalyticsForm,
    
    # Audit forms
    AuditAnalysisReportForm, AuditPatternForm, AuditAlertForm,
    AuditDashboardForm, AuditMetricForm, AuditMetricValueForm
)

logger = logging.getLogger(__name__)


# ==================== ANALYTICS DASHBOARD VIEWS ====================

class AnalyticsDashboardView(BaseTemplateView):
    """Main analytics dashboard"""
    template_name = 'analytics/dashboard.html'
    permission_required = 'analytics.view_analytics'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        # KPIModel Statistics
        kpi_queryset = KPIModel.objects.filter(tenant=tenant)
        context['total_kpis'] = kpi_queryset.count()
        context['active_kpis'] = kpi_queryset.filter(is_active=True).count()
        
        # Report Statistics
        context['total_reports'] = Report.objects.filter(tenant=tenant).count()
        context['scheduled_reports'] = Report.objects.filter(
            tenant=tenant, is_scheduled=True
        ).count()
        
        # Dashboard Statistics
        context['total_dashboards'] = Dashboard.objects.filter(tenant=tenant).count()
        context['public_dashboards'] = Dashboard.objects.filter(
            tenant=tenant, is_public=True
        ).count()
        
        # Recent Activity
        context['recent_reports'] = Report.objects.filter(
            tenant=tenant
        ).select_related('data_source').order_by('-created_at')[:5]
        
        context['recent_kpis'] = KPIModel.objects.filter(
            tenant=tenant
        ).order_by('-last_calculated')[:5]
        
        context['recent_alerts'] = AuditAlert.objects.filter(
            tenant=tenant, status='NEW'
        ).order_by('-created_at')[:5]
        
        # Performance metrics
        context['data_sources'] = DataSource.objects.filter(
            tenant=tenant
        ).annotate(
            kpi_count=Count('kpis'),
            model_count=Count('predictive_models')
        )[:5]
        
        return context


# ==================== AUDIT DASHBOARD VIEWS ====================

class AuditDashboardView(BaseTemplateView):
    """Main audit dashboard"""
    template_name = 'analytics/dashboard.html'
    permission_required = 'audit.view_audit'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        # Audit Statistics
        context['total_reports'] = AuditAnalysisReport.objects.filter(
            tenant=tenant
        ).count()
        
        context['active_patterns'] = AuditPattern.objects.filter(
            tenant=tenant, is_active=True
        ).count()
        
        # Alert Statistics
        alerts = AuditAlert.objects.filter(tenant=tenant)
        context['total_alerts'] = alerts.count()
        context['new_alerts'] = alerts.filter(status='NEW').count()
        context['critical_alerts'] = alerts.filter(severity='CRITICAL').count()
        
        # Metric Statistics
        context['total_metrics'] = AuditMetric.objects.filter(
            tenant=tenant
        ).count()
        
        # Recent Activity
        context['recent_alerts'] = alerts.select_related(
            'pattern', 'assigned_to'
        ).order_by('-created_at')[:10]
        
        context['recent_reports'] = AuditAnalysisReport.objects.filter(
            tenant=tenant
        ).order_by('-created_at')[:5]
        
        # Pattern Statistics
        context['patterns_by_severity'] = AuditPattern.objects.filter(
            tenant=tenant
        ).values('severity').annotate(count=Count('id')).order_by('severity')
        
        return context


# ==================== REPORT VIEWS ====================

class ReportListView(BaseListView):
    model = Report
    template_name = 'analytics/report/list.html'
    context_object_name = 'reports'
    permission_required = 'analytics.view_report'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        report_type = self.request.GET.get('report_type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
            
        access_level = self.request.GET.get('access_level')
        if access_level:
            queryset = queryset.filter(access_level=access_level)
            
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
            
        is_scheduled = self.request.GET.get('is_scheduled')
        if is_scheduled == 'true':
            queryset = queryset.filter(is_scheduled=True)
        elif is_scheduled == 'false':
            queryset = queryset.filter(is_scheduled=False)
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
            
        return queryset

class ReportDetailView(BaseDetailView):
    model = Report
    template_name = 'analytics/report/detail.html'
    context_object_name = 'report'
    permission_required = 'analytics.view_report'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.object
        
        # Get recent executions
        context['recent_executions'] = report.executions.order_by('-started_at')[:10]
        
        # Get related KPIs if any
        context['related_kpis'] = KPIModel.objects.filter(
            tenant=get_current_tenant(),
            calculation_query__icontains=report.title
        )[:5]
        
        return context

class ReportCreateView(BaseCreateView):
    model = Report
    form_class = ReportForm
    template_name = 'analytics/report/form.html'
    permission_required = 'analytics.add_report'
    success_url = reverse_lazy('analytics:report_list')

class ReportUpdateView(BaseUpdateView):
    model = Report
    form_class = ReportForm
    template_name = 'analytics/report/form.html'
    permission_required = 'analytics.change_report'
    success_url = reverse_lazy('analytics:report_list')

class ReportDeleteView(BaseDeleteView):
    model = Report
    template_name = 'analytics/common/confirm_delete.html'
    permission_required = 'analytics.delete_report'
    success_url = reverse_lazy('analytics:report_list')


# ==================== KPIModel VIEWS ====================

class KPIListView(BaseListView):
    model = KPIModel
    template_name = 'analytics/kpi/list.html'
    context_object_name = 'kpis'
    permission_required = 'analytics.view_kpi'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('data_source')
        
        # Apply filters
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
            
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
            
        frequency = self.request.GET.get('calculation_frequency')
        if frequency:
            queryset = queryset.filter(calculation_frequency=frequency)
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )
            
        return queryset

class KPIDetailView(BaseDetailView):
    model = KPIModel
    template_name = 'analytics/kpi/list.html'
    context_object_name = 'KPIModel'
    permission_required = 'analytics.view_kpi'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        KPIModel = self.object
        
        # Get historical values
        context['historical_values'] = KPIModel.historical_values.order_by('-period_end')[:20]
        
        # Get trend data
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        context['trend_data'] = KPIModel.historical_values.filter(
            period_end__gte=thirty_days_ago
        ).order_by('period_end')
        
        # Get related reports
        context['related_reports'] = Report.objects.filter(
            tenant=get_current_tenant(),
            config__icontains=KPIModel.code
        )[:5]
        
        return context

class KPICreateView(BaseCreateView):
    model = KPIModel
    form_class = KPIForm
    template_name = 'analytics/kpi/form.html'
    permission_required = 'analytics.add_kpi'
    success_url = reverse_lazy('analytics:kpi_list')

class KPIUpdateView(BaseUpdateView):
    model = KPIModel
    form_class = KPIForm
    template_name = 'analytics/kpi/form.html'
    permission_required = 'analytics.change_kpi'
    success_url = reverse_lazy('analytics:kpi_list')

class KPIDeleteView(BaseDeleteView):
    model = KPIModel
    template_name = 'analytics/common/confirm_delete.html'
    permission_required = 'analytics.delete_kpi'
    success_url = reverse_lazy('analytics:kpi_list')


# ==================== DATA SOURCE VIEWS ====================

class DataSourceListView(BaseListView):
    model = DataSource
    template_name = 'analytics/datasource/list.html'
    context_object_name = 'data_sources'
    permission_required = 'analytics.view_datasource'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        source_type = self.request.GET.get('source_type')
        if source_type:
            queryset = queryset.filter(source_type=source_type)
            
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
            
        return queryset

class DataSourceDetailView(BaseDetailView):
    model = DataSource
    template_name = 'analytics/datasource/detail.html'
    context_object_name = 'data_source'
    permission_required = 'analytics.view_datasource'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data_source = self.object
        
        # Get related KPIs
        context['kpis'] = data_source.kpis.filter(is_active=True)
        
        # Get related models
        context['predictive_models'] = data_source.predictive_models.all()
        
        # Get sync history
        context['recent_syncs'] = []
        # Add sync history logic here
        
        return context

class DataSourceCreateView(BaseCreateView):
    model = DataSource
    form_class = DataSourceForm
    template_name = 'analytics/datasource/form.html'
    permission_required = 'analytics.add_datasource'
    success_url = reverse_lazy('analytics:datasource_list')

class DataSourceUpdateView(BaseUpdateView):
    model = DataSource
    form_class = DataSourceForm
    template_name = 'analytics/datasource/form.html'
    permission_required = 'analytics.change_datasource'
    success_url = reverse_lazy('analytics:datasource_list')

class DataSourceDeleteView(BaseDeleteView):
    model = DataSource
    template_name = 'analytics/common/confirm_delete.html'
    permission_required = 'analytics.delete_datasource'
    success_url = reverse_lazy('analytics:datasource_list')


# ==================== DASHBOARD VIEWS ====================

class DashboardListView(BaseListView):
    model = Dashboard
    template_name = 'analytics/dashboard/list.html'
    context_object_name = 'dashboards'
    permission_required = 'analytics.view_dashboard'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        is_public = self.request.GET.get('is_public')
        if is_public == 'true':
            queryset = queryset.filter(is_public=True)
        elif is_public == 'false':
            queryset = queryset.filter(is_public=False)
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
            
        return queryset

class DashboardDetailView(BaseDetailView):
    model = Dashboard
    template_name = 'analytics/dashboard/detail.html'
    context_object_name = 'dashboard'
    permission_required = 'analytics.view_dashboard'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dashboard = self.object
        
        # Get widgets
        context['widgets'] = dashboard.widgets.all().select_related(
            'data_source', 'kpi'
        )
        
        return context

class DashboardCreateView(BaseCreateView):
    model = Dashboard
    form_class = DashboardForm
    template_name = 'analytics/dashboard/form.html'
    permission_required = 'analytics.add_dashboard'
    success_url = reverse_lazy('analytics:dashboard_list')

class DashboardUpdateView(BaseUpdateView):
    model = Dashboard
    form_class = DashboardForm
    template_name = 'analytics/dashboard/form.html'
    permission_required = 'analytics.change_dashboard'
    success_url = reverse_lazy('analytics:dashboard_list')

class DashboardDeleteView(BaseDeleteView):
    model = Dashboard
    template_name = 'analytics/common/confirm_delete.html'
    permission_required = 'analytics.delete_dashboard'
    success_url = reverse_lazy('analytics:dashboard_list')


# ==================== AUDIT ANALYSIS REPORT VIEWS ====================

class AuditAnalysisReportListView(BaseListView):
    model = AuditAnalysisReport
    template_name = 'analytics/audit/report_list.html'
    context_object_name = 'reports'
    permission_required = 'audit.view_auditanalysisreport'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('generated_by')
        
        # Apply filters
        report_type = self.request.GET.get('report_type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
            
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
            
        return queryset

class AuditAnalysisReportDetailView(BaseDetailView):
    model = AuditAnalysisReport
    template_name = 'analytics/audit/report_list.html'
    context_object_name = 'report'
    permission_required = 'audit.view_auditanalysisreport'

class AuditAnalysisReportCreateView(BaseCreateView):
    model = AuditAnalysisReport
    form_class = AuditAnalysisReportForm
    template_name = 'analytics/audit/report_form.html'
    permission_required = 'audit.add_auditanalysisreport'
    success_url = reverse_lazy('analytics:audit_report_list')

    def form_valid(self, form):
        form.instance.generated_by = self.request.user
        return super().form_valid(form)

class AuditAnalysisReportUpdateView(BaseUpdateView):
    model = AuditAnalysisReport
    form_class = AuditAnalysisReportForm
    template_name = 'analytics/audit/report_form.html'
    permission_required = 'audit.change_auditanalysisreport'
    success_url = reverse_lazy('analytics:audit_report_list')

class AuditAnalysisReportDeleteView(BaseDeleteView):
    model = AuditAnalysisReport
    template_name = 'analytics/common/confirm_delete.html'
    permission_required = 'audit.delete_auditanalysisreport'
    success_url = reverse_lazy('analytics:audit_report_list')


# ==================== AUDIT PATTERN VIEWS ====================

class AuditPatternListView(BaseListView):
    model = AuditPattern
    template_name = 'analytics/audit/pattern_list.html'
    context_object_name = 'patterns'
    permission_required = 'audit.view_auditpattern'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        pattern_type = self.request.GET.get('pattern_type')
        if pattern_type:
            queryset = queryset.filter(pattern_type=pattern_type)
            
        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
            
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
            
        return queryset

class AuditPatternDetailView(BaseDetailView):
    model = AuditPattern
    template_name = 'analytics/audit/pattern_list.html'
    context_object_name = 'pattern'
    permission_required = 'audit.view_auditpattern'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pattern = self.object
        
        # Get related alerts
        context['alerts'] = pattern.alerts.all().select_related(
            'assigned_to', 'acknowledged_by', 'resolved_by'
        ).order_by('-created_at')[:10]
        
        return context

class AuditPatternCreateView(BaseCreateView):
    model = AuditPattern
    form_class = AuditPatternForm
    template_name = 'analytics/audit/pattern_form.html'
    permission_required = 'audit.add_auditpattern'
    success_url = reverse_lazy('analytics:audit_pattern_list')

class AuditPatternUpdateView(BaseUpdateView):
    model = AuditPattern
    form_class = AuditPatternForm
    template_name = 'analytics/audit/pattern_form.html'
    permission_required = 'audit.change_auditpattern'
    success_url = reverse_lazy('analytics:audit_pattern_list')

class AuditPatternDeleteView(BaseDeleteView):
    model = AuditPattern
    template_name = 'analytics/common/confirm_delete.html'
    permission_required = 'audit.delete_auditpattern'
    success_url = reverse_lazy('analytics:audit_pattern_list')


# ==================== AUDIT ALERT VIEWS ====================

class AuditAlertListView(BaseListView):
    model = AuditAlert
    template_name = 'analytics/audit/alert_list.html'
    context_object_name = 'alerts'
    permission_required = 'audit.view_auditalert'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'pattern', 'assigned_to', 'acknowledged_by', 'resolved_by'
        )
        
        # Apply filters
        alert_type = self.request.GET.get('alert_type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
            
        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
            
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        assigned_to = self.request.GET.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
            
        return queryset

class AuditAlertDetailView(BaseDetailView):
    model = AuditAlert
    template_name = 'analytics/audit/alert_list.html'
    context_object_name = 'alert'
    permission_required = 'audit.view_auditalert'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        alert = self.object
        
        # Get related logs
        context['related_logs'] = alert.related_logs.all()[:20]
        
        return context

class AuditAlertCreateView(BaseCreateView):
    model = AuditAlert
    form_class = AuditAlertForm
    template_name = 'analytics/audit/alert_list.html'
    permission_required = 'audit.add_auditalert'
    success_url = reverse_lazy('analytics:audit_alert_list')

class AuditAlertUpdateView(BaseUpdateView):
    model = AuditAlert
    form_class = AuditAlertForm
    template_name = 'analytics/audit/alert_list.html'
    permission_required = 'audit.change_auditalert'
    success_url = reverse_lazy('analytics:audit_alert_list')

class AuditAlertDeleteView(BaseDeleteView):
    model = AuditAlert
    template_name = 'analytics/common/confirm_delete.html'
    permission_required = 'audit.delete_auditalert'
    success_url = reverse_lazy('analytics:audit_alert_list')


# ==================== API VIEWS FOR AJAX CALLS ====================

class KPIValueListView(BaseListView):
    """API endpoint for KPIModel values"""
    model = KPIValue
    permission_required = 'analytics.view_kpivalue'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('kpi', 'academic_year', 'class_name', 'subject')
        
        kpi_id = self.request.GET.get('kpi_id')
        if kpi_id:
            queryset = queryset.filter(kpi_id=kpi_id)
            
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(
                period_end__gte=start_date,
                period_end__lte=end_date
            )
            
        return queryset.order_by('period_end')
    
    def get(self, request, *args, **kwargs):
        data = list(self.get_queryset().values(
            'period_start', 'period_end', 'value',
            'kpi__name', 'academic_year__name', 'class_name__name', 'subject__name'
        )[:100])  # Limit to 100 records
        return JsonResponse({'data': data})


class ReportGenerateView(BaseView):
    """Generate report on demand"""
    permission_required = 'analytics.generate_report'
    
    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk, tenant=get_current_tenant())
        
        # Create execution record
        execution = ReportExecution.objects.create(
            report=report,
            executed_by=request.user,
            parameters=request.POST.get('parameters', {}),
            started_at=timezone.now()
        )
        
        try:
            # Generate report (simplified - implement actual logic)
            execution.complete_execution({
                'status': 'success',
                'message': 'Report generated successfully',
                'generated_at': timezone.now().isoformat()
            })
            
            messages.success(request, f"Report '{report.title}' generated successfully.")
            return redirect('analytics:report_detail', pk=report.pk)
            
        except Exception as e:
            logger.error(f"Failed to generate report {report.pk}: {str(e)}")
            execution.fail_execution(str(e))
            messages.error(request, f"Failed to generate report: {str(e)}")
            return redirect('analytics:report_detail', pk=report.pk)


# ==================== WIDGET VIEWS ====================

class DashboardWidgetCreateView(BaseCreateView):
    model = DashboardWidget
    form_class = DashboardWidgetForm
    template_name = 'analytics/dashboard/widget_form.html'
    permission_required = 'analytics.add_dashboardwidget'
    
    def get_success_url(self):
        return reverse_lazy('analytics:dashboard_detail', kwargs={'pk': self.object.dashboard.pk})

class DashboardWidgetUpdateView(BaseUpdateView):
    model = DashboardWidget
    form_class = DashboardWidgetForm
    template_name = 'analytics/dashboard/widget_form.html'
    permission_required = 'analytics.change_dashboardwidget'
    
    def get_success_url(self):
        return reverse_lazy('analytics:dashboard_detail', kwargs={'pk': self.object.dashboard.pk})

class DashboardWidgetDeleteView(BaseDeleteView):
    model = DashboardWidget
    template_name = 'analytics/common/confirm_delete.html'
    permission_required = 'analytics.delete_dashboardwidget'
    
    def get_success_url(self):
        return reverse_lazy('analytics:dashboard_detail', kwargs={'pk': self.object.dashboard.pk})


# ==================== PREDICTIVE MODEL VIEWS ====================

class PredictiveModelListView(BaseListView):
    model = PredictiveModel
    template_name = 'analytics/prediction/model_list.html'
    context_object_name = 'models'
    permission_required = 'analytics.view_predictivemodel'
    paginate_by = 20

class PredictiveModelDetailView(BaseDetailView):
    model = PredictiveModel
    template_name = 'analytics/prediction/model_list.html'
    context_object_name = 'model'
    permission_required = 'analytics.view_predictivemodel'

class PredictiveModelCreateView(BaseCreateView):
    model = PredictiveModel
    form_class = PredictiveModelForm
    template_name = 'analytics/prediction/model_form.html'
    permission_required = 'analytics.add_predictivemodel'
    success_url = reverse_lazy('analytics:prediction_list')

class PredictiveModelUpdateView(BaseUpdateView):
    model = PredictiveModel
    form_class = PredictiveModelForm
    template_name = 'analytics/prediction/model_form.html'
    permission_required = 'analytics.change_predictivemodel'
    success_url = reverse_lazy('analytics:prediction_list')

class PredictiveModelDeleteView(BaseDeleteView):
    model = PredictiveModel
    template_name = 'analytics/common/confirm_delete.html'
    permission_required = 'analytics.delete_predictivemodel'
    success_url = reverse_lazy('analytics:prediction_list')


# ==================== STUDENT PERFORMANCE ANALYTICS VIEWS ====================

class StudentPerformanceListView(BaseListView):
    model = StudentPerformanceAnalytics
    template_name = 'analytics/student/performance_list.html'
    context_object_name = 'analytics'
    permission_required = 'analytics.view_studentperformanceanalytics'
    paginate_by = 20

class StudentPerformanceDetailView(BaseDetailView):
    model = StudentPerformanceAnalytics
    template_name = 'analytics/student/performance_list.html'
    context_object_name = 'analytics'
    permission_required = 'analytics.view_studentperformanceanalytics'

class StudentPerformanceCreateView(BaseCreateView):
    model = StudentPerformanceAnalytics
    form_class = StudentPerformanceAnalyticsForm
    template_name = 'analytics/student/performance_form.html'
    permission_required = 'analytics.add_studentperformanceanalytics'
    success_url = reverse_lazy('analytics:student_performance_list')

class StudentPerformanceUpdateView(BaseUpdateView):
    model = StudentPerformanceAnalytics
    form_class = StudentPerformanceAnalyticsForm
    template_name = 'analytics/student/performance_form.html'
    permission_required = 'analytics.change_studentperformanceanalytics'
    success_url = reverse_lazy('analytics:student_performance_list')

class StudentPerformanceDeleteView(BaseDeleteView):
    model = StudentPerformanceAnalytics
    template_name = 'analytics/common/confirm_delete.html'
    permission_required = 'analytics.delete_studentperformanceanalytics'
    success_url = reverse_lazy('analytics:student_performance_list')


# ==================== INSTITUTIONAL ANALYTICS VIEWS ====================

class InstitutionalAnalyticsListView(BaseListView):
    model = InstitutionalAnalytics
    template_name = 'analytics/institution/analytics_list.html'
    context_object_name = 'analytics'
    permission_required = 'analytics.view_institutionalanalytics'
    paginate_by = 20

class InstitutionalAnalyticsDetailView(BaseDetailView):
    model = InstitutionalAnalytics
    template_name = 'analytics/institution/analytics_list.html'
    context_object_name = 'analytics'
    permission_required = 'analytics.view_institutionalanalytics'

class InstitutionalAnalyticsCreateView(BaseCreateView):
    model = InstitutionalAnalytics
    form_class = InstitutionalAnalyticsForm
    template_name = 'analytics/institution/analytics_form.html'
    permission_required = 'analytics.add_institutionalanalytics'
    success_url = reverse_lazy('analytics:institutional_list')

class InstitutionalAnalyticsUpdateView(BaseUpdateView):
    model = InstitutionalAnalytics
    form_class = InstitutionalAnalyticsForm
    template_name = 'analytics/institution/analytics_form.html'
    permission_required = 'analytics.change_institutionalanalytics'
    success_url = reverse_lazy('analytics:institutional_list')

class InstitutionalAnalyticsDeleteView(BaseDeleteView):
    model = InstitutionalAnalytics
    template_name = 'analytics/common/confirm_delete.html'
    permission_required = 'analytics.delete_institutionalanalytics'
    success_url = reverse_lazy('analytics:institutional_list')


# ==================== HISTORY VIEWS ====================

class ReportExecutionListView(BaseListView):
    model = ReportExecution
    template_name = 'analytics/history/execution_list.html'
    context_object_name = 'executions'
    permission_required = 'analytics.view_reportexecution'
    paginate_by = 50

    def get_queryset(self):
        return super().get_queryset().select_related('report', 'executed_by').order_by('-started_at')


# ==================== AUDIT METRIC VIEWS ====================

class AuditMetricListView(BaseListView):
    model = AuditMetric
    template_name = 'analytics/audit/metric_list.html'
    context_object_name = 'metrics'
    permission_required = 'analytics.view_auditmetric'
    paginate_by = 20

class AuditMetricCreateView(BaseCreateView):
    model = AuditMetric
    form_class = AuditMetricForm
    template_name = 'analytics/audit/metric_form.html'
    permission_required = 'analytics.add_auditmetric'
    success_url = reverse_lazy('analytics:audit_metric_list')

class AuditMetricUpdateView(BaseUpdateView):
    model = AuditMetric
    form_class = AuditMetricForm
    template_name = 'analytics/audit/metric_form.html'
    permission_required = 'analytics.change_auditmetric'
    success_url = reverse_lazy('analytics:audit_metric_list')

class AuditMetricDeleteView(BaseDeleteView):
    model = AuditMetric
    template_name = 'analytics/common/confirm_delete.html'
    permission_required = 'analytics.delete_auditmetric'
    success_url = reverse_lazy('analytics:audit_metric_list')