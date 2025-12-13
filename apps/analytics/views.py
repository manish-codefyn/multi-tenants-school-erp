from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.utils import timezone
from .models import Report, Dashboard, KPI, ReportExecution
from apps.core.permissions.mixins import PermissionRequiredMixin
import csv
import json

class AnalyticsDashboardView(LoginRequiredMixin,  TemplateView):
    template_name = "analytics/dashboard.html"
    permission_required = "analytics.view_dashboard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get active dashboard or default
        context['dashboards'] = Dashboard.objects.filter(is_active=True)
        context['active_dashboard'] = context['dashboards'].first()
        
        # Get key metrics
        context['total_reports'] = Report.objects.filter(is_active=True).count()
        context['recent_executions'] = ReportExecution.objects.order_by('-started_at')[:5]
        context['kpis'] = KPI.objects.filter(is_active=True)[:6]
        
        return context

class ReportListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Report
    template_name = "analytics/report_list.html"
    context_object_name = "reports"
    permission_required = "analytics.view_report"

    def get_queryset(self):
        return Report.objects.filter(is_active=True).order_by('title')

class ReportDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Report
    template_name = "analytics/report_detail.html"
    context_object_name = "report"
    permission_required = "analytics.view_report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add recent executions for this report
        context['executions'] = self.object.executions.order_by('-started_at')[:10]
        return context

class ExportReportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "analytics.view_report"

    def get(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{report.title}.csv"'},
        )

        writer = csv.writer(response)
        
        # In a real scenario, we would execute the report's query or fetch data
        # For now, we'll just write some sample data based on the report configuration or just a placeholder
        writer.writerow(["Report Title", report.title])
        writer.writerow(["Generated At", timezone.now()])
        writer.writerow([])
        writer.writerow(["Column 1", "Column 2", "Column 3"])
        writer.writerow(["Data 1", "Data 2", "Data 3"])

        return response
