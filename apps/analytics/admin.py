from django.contrib import admin
from .models import (
    DataSource, KPI, KPIValue, Report, ReportExecution,
    Dashboard, DashboardWidget
)

@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type', 'status', 'sync_frequency', 'last_sync')
    list_filter = ('source_type', 'status', 'sync_frequency')
    search_fields = ('name',)

@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'calculation_frequency', 'is_active')
    list_filter = ('category', 'calculation_frequency', 'is_active')
    search_fields = ('name', 'code')

@admin.register(KPIValue)
class KPIValueAdmin(admin.ModelAdmin):
    list_display = ('kpi', 'value', 'period_start', 'period_end', 'period_type')
    list_filter = ('period_type', 'kpi')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'access_level', 'is_active', 'is_scheduled')
    list_filter = ('report_type', 'access_level', 'is_active', 'is_scheduled')
    search_fields = ('title',)

@admin.register(ReportExecution)
class ReportExecutionAdmin(admin.ModelAdmin):
    list_display = ('report', 'executed_by', 'status', 'started_at', 'completed_at')
    list_filter = ('status', 'report')
    search_fields = ('report__title', 'executed_by__email')

@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ('title', 'layout_type', 'is_public', 'is_active')
    list_filter = ('layout_type', 'is_public', 'is_active')
    search_fields = ('title',)

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ('title', 'dashboard', 'widget_type')
    list_filter = ('widget_type', 'dashboard')
    search_fields = ('title',)
