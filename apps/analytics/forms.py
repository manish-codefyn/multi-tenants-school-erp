from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import json

from apps.core.forms import TenantAwareModelForm
from .models import (
    Report, KPIModel, DataSource, Dashboard, DashboardWidget,
    AuditAnalysisReport, AuditPattern, AuditAlert, AuditDashboard,
    AuditMetric, AuditMetricValue, ReportExecution, KPIValue,
    PredictiveModel, StudentPerformanceAnalytics, InstitutionalAnalytics
)


# ==================== ANALYTICS FORMS ====================

class ReportForm(TenantAwareModelForm):
    """Form for creating and updating reports"""
    
    class Meta:
        model = Report
        fields = [
            'title', 'description', 'report_type', 'config',
            'filters', 'parameters', 'chart_config', 'access_level', 'allowed_roles',
            'is_scheduled', 'schedule_frequency', 'schedule_time',
            'is_active', 'is_template'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'config': forms.Textarea(attrs={'rows': 5, 'class': 'form-control font-monospace'}),
            'filters': forms.Textarea(attrs={'rows': 3, 'class': 'form-control font-monospace'}),
            'parameters': forms.Textarea(attrs={'rows': 3, 'class': 'form-control font-monospace'}),
            'chart_config': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'allowed_roles': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'schedule_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
        labels = {
            'config': _('Configuration (JSON)'),
            'filters': _('Filters (JSON)'),
            'parameters': _('Parameters (JSON)'),
            'chart_config': _('Chart Config (JSON)'),
            'allowed_roles': _('Allowed Roles (JSON array)'),
        }
    
    def clean_chart_config(self):
        chart_config = self.cleaned_data.get('chart_config')
        if chart_config:
            try:
                if isinstance(chart_config, str):
                    json.loads(chart_config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for chart configuration'))
        return chart_config
    
    def clean_config(self):
        config = self.cleaned_data.get('config')
        if config:
            try:
                json.loads(config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for configuration'))
        return config
    
    def clean_filters(self):
        filters = self.cleaned_data.get('filters')
        if filters:
            try:
                json.loads(filters)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for filters'))
        return filters
    
    def clean_parameters(self):
        parameters = self.cleaned_data.get('parameters')
        if parameters:
            try:
                json.loads(parameters)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for parameters'))
        return parameters
    
    def clean_allowed_roles(self):
        allowed_roles = self.cleaned_data.get('allowed_roles')
        if allowed_roles:
            try:
                json.loads(allowed_roles)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for allowed roles'))
        return allowed_roles


class KPIForm(TenantAwareModelForm):
    """Form for creating and updating KPIs"""
    
    class Meta:
        model = KPIModel
        fields = [
            'name', 'code', 'category', 'description',
            'data_source', 'calculation_query', 'calculation_frequency',
            'target_value', 'min_threshold', 'max_threshold',
            'direction', 'unit', 'format_string', 'decimal_places',
            'chart_config', 'color_scheme', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., STUDENT_ATTENDANCE_RATE'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'calculation_query': forms.Textarea(attrs={'rows': 8, 'class': 'form-control font-monospace'}),
            'target_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., %, students, hours'}),
            'format_string': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 0.00%'}),
            'chart_config': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
        }

    def clean_chart_config(self):
        chart_config = self.cleaned_data.get('chart_config')
        if chart_config:
            try:
                if isinstance(chart_config, str):
                    json.loads(chart_config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for chart configuration'))
        return chart_config
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.strip().upper().replace(' ', '_')
            # Check if code is already used (excluding current instance)
            qs = KPIModel.objects.filter(code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('A KPI with this code already exists'))
        return code


class DataSourceForm(TenantAwareModelForm):
    """Form for creating and updating data sources"""
    
    class Meta:
        model = DataSource
        fields = [
            'name', 'description', 'source_type',
            'connection_string', 'config', 'credentials',
            'sync_frequency', 'chart_config', 'status', 'schema_version',
            'is_public', 'tags'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'connection_string': forms.Textarea(attrs={'rows': 3, 'class': 'form-control font-monospace'}),
            'config': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'credentials': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'chart_config': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'tags': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
        labels = {
            'config': _('Configuration (JSON)'),
            'credentials': _('Credentials (JSON - encrypted)'),
            'chart_config': _('Chart Config (JSON)'),
            'tags': _('Tags (JSON array)'),
        }

    def clean_chart_config(self):
        chart_config = self.cleaned_data.get('chart_config')
        if chart_config:
            try:
                if isinstance(chart_config, str):
                    json.loads(chart_config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for chart configuration'))
        return chart_config
    
    def clean_config(self):
        config = self.cleaned_data.get('config')
        if config:
            try:
                json.loads(config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for configuration'))
        return config
    
    def clean_credentials(self):
        credentials = self.cleaned_data.get('credentials')
        if credentials:
            try:
                json.loads(credentials)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for credentials'))
        return credentials
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        if tags:
            try:
                json.loads(tags)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for tags'))
        return tags


class DashboardForm(TenantAwareModelForm):
    """Form for creating and updating dashboards"""
    
    class Meta:
        model = Dashboard
        fields = [
            'title', 'description', 'layout_type',
            'config', 'filters', 'chart_config', 'theme',
            'is_public', 'allowed_roles', 'is_template',
            'is_active', 'refresh_interval'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'config': forms.Textarea(attrs={'rows': 5, 'class': 'form-control font-monospace'}),
            'filters': forms.Textarea(attrs={'rows': 3, 'class': 'form-control font-monospace'}),
            'chart_config': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'allowed_roles': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'refresh_interval': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'seconds'}),
        }
        labels = {
            'config': _('Configuration (JSON)'),
            'filters': _('Global Filters (JSON)'),
            'chart_config': _('Chart Config (JSON)'),
            'allowed_roles': _('Allowed Roles (JSON array)'),
        }

    def clean_chart_config(self):
        chart_config = self.cleaned_data.get('chart_config')
        if chart_config:
            try:
                if isinstance(chart_config, str):
                    json.loads(chart_config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for chart configuration'))
        return chart_config
    
    def clean_config(self):
        config = self.cleaned_data.get('config')
        if config:
            try:
                json.loads(config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for configuration'))
        return config
    
    def clean_filters(self):
        filters = self.cleaned_data.get('filters')
        if filters:
            try:
                json.loads(filters)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for filters'))
        return filters
    
    def clean_allowed_roles(self):
        allowed_roles = self.cleaned_data.get('allowed_roles')
        if allowed_roles:
            try:
                json.loads(allowed_roles)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for allowed roles'))
        return allowed_roles


class DashboardWidgetForm(TenantAwareModelForm):
    """Form for adding widgets to a dashboard"""
    
    class Meta:
        model = DashboardWidget
        fields = [
            'dashboard', 'title', 'widget_type', 'chart_config',
            'config', 'data_source', 'kpi',
            'position_x', 'position_y', 'width', 'height',
            'color_scheme', 'custom_css',
            'refresh_interval', 'is_interactive', 'drill_down_enabled'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'config': forms.Textarea(attrs={'rows': 6, 'class': 'form-control font-monospace'}),
            'chart_config': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'custom_css': forms.Textarea(attrs={'rows': 3, 'class': 'form-control font-monospace'}),
            'position_x': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'position_y': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'color_scheme': forms.TextInput(attrs={'class': 'form-control'}),
            'refresh_interval': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
        labels = {
            'config': _('Configuration (JSON)'),
            'chart_config': _('Chart Config (JSON)'),
            'custom_css': _('Custom CSS'),
        }

    def clean_chart_config(self):
        chart_config = self.cleaned_data.get('chart_config')
        if chart_config:
            try:
                if isinstance(chart_config, str):
                    json.loads(chart_config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for chart configuration'))
        return chart_config
    
    def clean_config(self):
        config = self.cleaned_data.get('config')
        if config:
            try:
                json.loads(config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for configuration'))
        return config
    
    def clean(self):
        cleaned_data = super().clean()
        width = cleaned_data.get('width')
        if width and width > 12:
            raise ValidationError({'width': _('Width cannot be greater than 12 (grid system)')})
        return cleaned_data


# ==================== AUDIT FORMS ====================

class AuditAnalysisReportForm(TenantAwareModelForm):
    """Form for audit analysis reports"""
    
    class Meta:
        model = AuditAnalysisReport
        fields = [
            'name', 'report_type', 'format',
            'start_date', 'end_date', 'filter_type', 'chart_config',
            'status', 'expires_at', 'is_archived'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'chart_config': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
        }
        labels = {
            'chart_config': _('Chart Config (JSON)'),
        }

    def clean_chart_config(self):
        chart_config = self.cleaned_data.get('chart_config')
        if chart_config:
            try:
                if isinstance(chart_config, str):
                    json.loads(chart_config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for chart configuration'))
        return chart_config

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # filter_type is used instead of filters
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError(_('End date must be after start date'))
            if start_date > timezone.now():
                raise ValidationError(_('Start date cannot be in the future'))
        
        expires_at = cleaned_data.get('expires_at')
        if expires_at and expires_at < timezone.now():
            raise ValidationError(_('Expiration date cannot be in the past'))
        
        return cleaned_data


class AuditPatternForm(TenantAwareModelForm):
    """Form for audit patterns"""
    
    class Meta:
        model = AuditPattern
        fields = [
            'name', 'pattern_type', 'description', 'severity',
            'detection_rules', 'chart_config', 'threshold', 'time_window_minutes',
            'recommended_action', 'is_active', 'is_auto_remediate'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'detection_rules': forms.Textarea(attrs={'rows': 6, 'class': 'form-control font-monospace'}),
            'chart_config': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'time_window_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
        labels = {
            'detection_rules': _('Detection Rules (JSON)'),
            'chart_config': _('Chart Config (JSON)'),
            'time_window_minutes': _('Time Window (minutes)'),
        }

    def clean_chart_config(self):
        chart_config = self.cleaned_data.get('chart_config')
        if chart_config:
            try:
                if isinstance(chart_config, str):
                    json.loads(chart_config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for chart configuration'))
        return chart_config
    
    def clean_detection_rules(self):
        detection_rules = self.cleaned_data.get('detection_rules')
        if detection_rules:
            try:
                json.loads(detection_rules)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for detection rules'))
        return detection_rules
    
    pass
    
    def clean_threshold(self):
        threshold = self.cleaned_data.get('threshold')
        if threshold is not None and threshold <= 0:
            raise ValidationError(_('Threshold must be greater than 0'))
        return threshold


class AuditAlertForm(TenantAwareModelForm):
    """Form for audit alerts"""
    
    class Meta:
        model = AuditAlert
        fields = [
            'alert_type', 'pattern', 'title', 'description',
            'details', 'chart_config', 'severity', 'status', 'assigned_to',
            'resolution_notes', 'auto_remediation_notes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'details': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'chart_config': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'resolution_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'auto_remediation_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'details': _('Details (JSON)'),
            'chart_config': _('Chart Config (JSON)'),
        }

    def clean_chart_config(self):
        chart_config = self.cleaned_data.get('chart_config')
        if chart_config:
            try:
                if isinstance(chart_config, str):
                    json.loads(chart_config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for chart configuration'))
        return chart_config
    
    def clean_details(self):
        details = self.cleaned_data.get('details')
        if details:
            try:
                json.loads(details)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for details'))
        return details


class AuditDashboardForm(TenantAwareModelForm):
    """Form for audit dashboards"""
    
    class Meta:
        model = AuditDashboard
        fields = [
            'name', 'description', 'layout_config', 'widget_configs', 'chart_config',
            'is_shared', 'shared_with_users', 'shared_with_groups',
            'is_default', 'refresh_interval_minutes', 'owner'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'layout_config': forms.Textarea(attrs={'rows': 5, 'class': 'form-control font-monospace'}),
            'widget_configs': forms.Textarea(attrs={'rows': 6, 'class': 'form-control font-monospace'}),
            'chart_config': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'shared_with_users': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
            'shared_with_groups': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
            'refresh_interval_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
        labels = {
            'layout_config': _('Layout Configuration (JSON)'),
            'widget_configs': _('Widget Configurations (JSON array)'),
            'chart_config': _('Chart Config (JSON)'),
            'refresh_interval_minutes': _('Refresh Interval (minutes)'),
        }

    def clean_chart_config(self):
        chart_config = self.cleaned_data.get('chart_config')
        if chart_config:
            try:
                if isinstance(chart_config, str):
                    json.loads(chart_config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for chart configuration'))
        return chart_config
    
    def clean_layout_config(self):
        layout_config = self.cleaned_data.get('layout_config')
        if layout_config:
            try:
                json.loads(layout_config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for layout configuration'))
        return layout_config
    
    def clean_widget_configs(self):
        widget_configs = self.cleaned_data.get('widget_configs')
        if widget_configs:
            try:
                json.loads(widget_configs)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for widget configurations'))
        return widget_configs


class AuditMetricForm(TenantAwareModelForm):
    """Form for audit metrics"""
    
    class Meta:
        model = AuditMetric
        fields = [
            'name', 'metric_type', 'description',
            'query_filter', 'group_by_fields', 'aggregation_field', 'chart_config',
            'calculation_schedule', 'warning_threshold', 'critical_threshold'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'query_filter': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'group_by_fields': forms.Textarea(attrs={'rows': 3, 'class': 'form-control font-monospace'}),
            'chart_config': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'aggregation_field': forms.TextInput(attrs={'class': 'form-control'}),
            'warning_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'critical_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'query_filter': _('Query Filter (JSON)'),
            'group_by_fields': _('Group By Fields (JSON array)'),
            'chart_config': _('Chart Config (JSON)'),
        }

    def clean_chart_config(self):
        chart_config = self.cleaned_data.get('chart_config')
        if chart_config:
            try:
                if isinstance(chart_config, str):
                    json.loads(chart_config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for chart configuration'))
        return chart_config
    
    def clean_query_filter(self):
        query_filter = self.cleaned_data.get('query_filter')
        if query_filter:
            try:
                json.loads(query_filter)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for query filter'))
        return query_filter
    
    def clean_group_by_fields(self):
        group_by_fields = self.cleaned_data.get('group_by_fields')
        if group_by_fields:
            try:
                json.loads(group_by_fields)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for group by fields'))
        return group_by_fields
    
    def clean(self):
        cleaned_data = super().clean()
        warning = cleaned_data.get('warning_threshold')
        critical = cleaned_data.get('critical_threshold')
        
        if warning is not None and critical is not None:
            if warning >= critical:
                raise ValidationError(_('Warning threshold must be less than critical threshold'))
        
        return cleaned_data


class AuditMetricValueForm(TenantAwareModelForm):
    """Form for audit metric values"""
    
    class Meta:
        model = AuditMetricValue
        fields = [
            'metric', 'tenant', 'value', 'timestamp',
            'period_start', 'period_end', 'period_type',
            'sample_count', 'min_value', 'max_value', 'avg_value'
        ]
        widgets = {
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'timestamp': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'period_start': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'period_end': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'period_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'hour, day, week, month'}),
            'sample_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'min_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'avg_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        period_start = cleaned_data.get('period_start')
        period_end = cleaned_data.get('period_end')
        timestamp = cleaned_data.get('timestamp')
        
        if period_start and period_end and period_start >= period_end:
            raise ValidationError(_('Period end must be after period start'))
        
        if timestamp and period_end and timestamp > period_end:
            raise ValidationError(_('Timestamp cannot be after period end'))
        
        # Validate min/max/avg consistency
        min_val = cleaned_data.get('min_value')
        max_val = cleaned_data.get('max_value')
        avg_val = cleaned_data.get('avg_value')
        
        if min_val is not None and max_val is not None and min_val > max_val:
            raise ValidationError(_('Minimum value cannot be greater than maximum value'))
        
        if avg_val is not None:
            if min_val is not None and avg_val < min_val:
                raise ValidationError(_('Average value cannot be less than minimum value'))
            if max_val is not None and avg_val > max_val:
                raise ValidationError(_('Average value cannot be greater than maximum value'))
        
        return cleaned_data


# ==================== EXECUTION & HISTORY FORMS ====================

class ReportExecutionForm(TenantAwareModelForm):
    """Form for report executions"""
    
    class Meta:
        model = ReportExecution
        fields = [
            'report', 'parameters', 'chart_config', 'status',
            'error_message', 'stack_trace', 'executed_by',
            'output_format', 'output_file'
        ]
        widgets = {
            'parameters': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'chart_config': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'error_message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'stack_trace': forms.Textarea(attrs={'rows': 5, 'class': 'form-control font-monospace'}),
            'output_file': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'parameters': _('Parameters (JSON)'),
            'chart_config': _('Chart Config (JSON)'),
            'stack_trace': _('Stack Trace'),
        }

    def clean_chart_config(self):
        chart_config = self.cleaned_data.get('chart_config')
        if chart_config:
            try:
                if isinstance(chart_config, str):
                    json.loads(chart_config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for chart configuration'))
        return chart_config
    
    def clean_parameters(self):
        parameters = self.cleaned_data.get('parameters')
        if parameters:
            try:
                json.loads(parameters)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for parameters'))
        return parameters


class KPIValueForm(TenantAwareModelForm):
    """Form for KPI values"""
    
    class Meta:
        model = KPIValue
        fields = [
            'kpi', 'value', 'period_start', 'period_end', 'period_type',
            'academic_year', 'class_name', 'subject',
            'data_points', 'confidence_level', 'notes'
        ]
        widgets = {
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'period_start': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'period_end': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'period_type': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control'}
            ),
            'data_points': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'confidence_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': '0.01'}),
        }
        labels = {
            'kpi': _("KPI"),
            'value': _("KPI Value"),
            'period_start': _("Period Start"),
            'period_end': _("Period End"),
            'period_type': _("Period Type"),
            'academic_year': _("Academic Year"),
            'class_name': _("Class"),
            'subject': _("Subject"),
            'data_points': _("Data Points Count"),
            'confidence_level': _("Confidence Level (%)"),
            'notes': _("Notes"),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('period_start')
        end = cleaned_data.get('period_end')
        confidence = cleaned_data.get('confidence_level')
        data_points = cleaned_data.get('data_points')

        if start and end and start >= end:
            raise ValidationError(
                _("Period end must be greater than period start.")
            )

        if confidence is not None:
            if confidence < 0 or confidence > 100:
                raise ValidationError(
                    _("Confidence level must be between 0 and 100.")
                )
        
        if data_points is not None and data_points < 1:
            raise ValidationError(
                _("Data points count must be at least 1.")
            )

        return cleaned_data


# ==================== ADVANCED ANALYTICS FORMS ====================

class PredictiveModelForm(TenantAwareModelForm):
    """Form for predictive models"""
    
    class Meta:
        model = PredictiveModel
        fields = [
            'name', 'description', 'model_type', 'algorithm',
            'hyperparameters', 'feature_columns', 'target_column', 'chart_config',
            'training_data_source', 'training_query', 'status',
            'accuracy', 'precision', 'recall', 'f1_score'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'hyperparameters': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'feature_columns': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'chart_config': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'target_column': forms.TextInput(attrs={'class': 'form-control'}),
            'training_query': forms.Textarea(attrs={'rows': 6, 'class': 'form-control font-monospace'}),
            'accuracy': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001', 'min': 0, 'max': 1}),
            'precision': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001', 'min': 0, 'max': 1}),
            'recall': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001', 'min': 0, 'max': 1}),
            'f1_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001', 'min': 0, 'max': 1}),
        }
        labels = {
            'hyperparameters': _('Hyperparameters (JSON)'),
            'feature_columns': _('Feature Columns (JSON array)'),
            'chart_config': _('Chart Config (JSON)'),
        }

    def clean_chart_config(self):
        chart_config = self.cleaned_data.get('chart_config')
        if chart_config:
            try:
                if isinstance(chart_config, str):
                    json.loads(chart_config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for chart configuration'))
        return chart_config
    
    def clean_hyperparameters(self):
        hyperparameters = self.cleaned_data.get('hyperparameters')
        if hyperparameters:
            try:
                json.loads(hyperparameters)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for hyperparameters'))
        return hyperparameters
    
    def clean_feature_columns(self):
        feature_columns = self.cleaned_data.get('feature_columns')
        if feature_columns:
            try:
                json.loads(feature_columns)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for feature columns'))
        return feature_columns
    
    def clean(self):
        cleaned_data = super().clean()
        accuracy = cleaned_data.get('accuracy')
        precision = cleaned_data.get('precision')
        recall = cleaned_data.get('recall')
        f1_score = cleaned_data.get('f1_score')
        
        for field in [accuracy, precision, recall, f1_score]:
            if field is not None and (field < 0 or field > 1):
                raise ValidationError(_('Performance scores must be between 0 and 1'))
        
        return cleaned_data


class StudentPerformanceAnalyticsForm(TenantAwareModelForm):
    """Form for student performance analytics"""
    
    class Meta:
        model = StudentPerformanceAnalytics
        fields = [
            'student', 'academic_year',
            'overall_percentage', 'class_rank', 'total_students',
            'subject_performance', 'strong_subjects', 'weak_subjects', 'chart_config',
            'attendance_percentage', 'total_present', 'total_absent', 'total_leave',
            'participation_score', 'discipline_incidents', 'awards_count',
            'performance_trend', 'growth_percentage',
            'at_risk_score', 'predicted_performance', 'recommendation'
        ]
        widgets = {
            'overall_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'class_rank': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'total_students': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'subject_performance': forms.Textarea(attrs={'rows': 5, 'class': 'form-control font-monospace'}),
            'strong_subjects': forms.Textarea(attrs={'rows': 3, 'class': 'form-control font-monospace'}),
            'weak_subjects': forms.Textarea(attrs={'rows': 3, 'class': 'form-control font-monospace'}),
            'chart_config': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
            'attendance_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'total_present': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'total_absent': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'total_leave': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'participation_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'discipline_incidents': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'awards_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'growth_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'at_risk_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'predicted_performance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'recommendation': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
        labels = {
            'subject_performance': _('Subject Performance (JSON)'),
            'strong_subjects': _('Strong Subjects (JSON array)'),
            'weak_subjects': _('Weak Subjects (JSON array)'),
            'chart_config': _('Chart Config (JSON)'),
        }

    def clean_chart_config(self):
        chart_config = self.cleaned_data.get('chart_config')
        if chart_config:
            try:
                if isinstance(chart_config, str):
                    json.loads(chart_config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for chart configuration'))
        return chart_config
    
    def clean_subject_performance(self):
        subject_performance = self.cleaned_data.get('subject_performance')
        if subject_performance:
            try:
                json.loads(subject_performance)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for subject performance'))
        return subject_performance
    
    def clean_strong_subjects(self):
        strong_subjects = self.cleaned_data.get('strong_subjects')
        if strong_subjects:
            try:
                json.loads(strong_subjects)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for strong subjects'))
        return strong_subjects
    
    def clean_weak_subjects(self):
        weak_subjects = self.cleaned_data.get('weak_subjects')
        if weak_subjects:
            try:
                json.loads(weak_subjects)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for weak subjects'))
        return weak_subjects
    
    def clean(self):
        cleaned_data = super().clean()
        class_rank = cleaned_data.get('class_rank')
        total_students = cleaned_data.get('total_students')
        
        if class_rank is not None and total_students is not None:
            if class_rank > total_students:
                raise ValidationError(_('Class rank cannot be greater than total students'))
        
        # Validate percentages are between 0 and 100
        percent_fields = ['overall_percentage', 'attendance_percentage', 'participation_score', 'at_risk_score', 'predicted_performance']
        for field in percent_fields:
            value = cleaned_data.get(field)
            if value is not None and (value < 0 or value > 100):
                raise ValidationError({field: _('Value must be between 0 and 100')})
        
        return cleaned_data


class InstitutionalAnalyticsForm(TenantAwareModelForm):
    """Form for institutional analytics"""
    
    class Meta:
        model = InstitutionalAnalytics
        fields = [
            'academic_year',
            'total_students', 'male_students', 'female_students', 'other_gender_students',
            'total_revenue', 'total_expenses', 'fee_collection_percentage',
            'total_staff', 'student_teacher_ratio',
            'average_attendance', 'pass_percentage', 'chart_config'
        ]
        widgets = {
            'total_students': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'male_students': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'female_students': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'other_gender_students': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'total_revenue': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'min': 0}),
            'total_expenses': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'min': 0}),
            'fee_collection_percentage': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'min': 0, 'max': 100}),
            'total_staff': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'student_teacher_ratio': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'min': 0}),
            'average_attendance': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'min': 0, 'max': 100}),
            'pass_percentage': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'min': 0, 'max': 100}),
            'chart_config': forms.Textarea(attrs={'rows': 4, 'class': 'form-control font-monospace'}),
        }
        labels = {
            'academic_year': _("Academic Year"),
            'total_students': _("Total Students"),
            'male_students': _("Male Students"),
            'female_students': _("Female Students"),
            'other_gender_students': _("Other Gender Students"),
            'total_revenue': _("Total Revenue"),
            'total_expenses': _("Total Expenses"),
            'fee_collection_percentage': _("Fee Collection Percentage (%)"),
            'total_staff': _("Total Staff"),
            'student_teacher_ratio': _("Student–Teacher Ratio"),
            'average_attendance': _("Average Attendance (%)"),
            'pass_percentage': _("Pass Percentage (%)"),
            'chart_config': _('Chart Config (JSON)'),
        }

    def clean_chart_config(self):
        chart_config = self.cleaned_data.get('chart_config')
        if chart_config:
            try:
                if isinstance(chart_config, str):
                    json.loads(chart_config)
            except json.JSONDecodeError:
                raise ValidationError(_('Invalid JSON format for chart configuration'))
        return chart_config
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate student demographics
        total_students = cleaned_data.get('total_students', 0)
        male_students = cleaned_data.get('male_students', 0)
        female_students = cleaned_data.get('female_students', 0)
        other_gender_students = cleaned_data.get('other_gender_students', 0)
        
        gender_sum = male_students + female_students + other_gender_students
        if gender_sum > total_students:
            raise ValidationError(_('Sum of gender-specific students cannot exceed total students'))
        
        # Validate financial metrics
        total_revenue = cleaned_data.get('total_revenue')
        total_expenses = cleaned_data.get('total_expenses')
        
        if total_revenue is not None and total_revenue < 0:
            raise ValidationError({'total_revenue': _('Total revenue cannot be negative')})
        
        if total_expenses is not None and total_expenses < 0:
            raise ValidationError({'total_expenses': _('Total expenses cannot be negative')})
        
        # Validate percentages
        percent_fields = ['fee_collection_percentage', 'average_attendance', 'pass_percentage']
        for field in percent_fields:
            value = cleaned_data.get(field)
            if value is not None and (value < 0 or value > 100):
                raise ValidationError({field: _('Value must be between 0 and 100')})
        
        # Validate student-teacher ratio
        ratio = cleaned_data.get('student_teacher_ratio')
        if ratio is not None and ratio < 0:
            raise ValidationError({'student_teacher_ratio': _('Student-teacher ratio cannot be negative')})
        
        return cleaned_data
