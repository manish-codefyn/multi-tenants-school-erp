"""
Audit Log Analyzer for pattern detection and reporting
"""

import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from django.utils import timezone
from django.db.models import Count, Q, Avg, Max, Min, F, Window
from django.db.models.functions import TruncHour, TruncDay, TruncWeek, TruncMonth

from apps.core.utils.audit import AuditLog


class AuditAnalyzer:
    """Main analyzer class for audit logs"""
    
    def __init__(self, tenant_id=None):
        self.tenant_id = tenant_id
        self.base_query = AuditLog.objects.all()
        
        if tenant_id:
            self.base_query = self.base_query.filter(tenant_id=tenant_id)
    
    def get_user_activity_summary(self, days=7, top_n=10):
        """Get summary of user activity"""
        since = timezone.now() - timedelta(days=days)
        
        # User activity stats
        user_stats = (
            self.base_query
            .filter(timestamp__gte=since)
            .values('user_email', 'user')
            .annotate(
                total_actions=Count('id'),
                last_activity=Max('timestamp'),
                distinct_resources=Count('resource_type', distinct=True),
                create_count=Count('id', filter=Q(action='CREATE')),
                update_count=Count('id', filter=Q(action='UPDATE')),
                delete_count=Count('id', filter=Q(action__in=['DELETE', 'SOFT_DELETE']))
            )
            .order_by('-total_actions')[:top_n]
        )
        
        # Hourly distribution
        hourly_dist = (
            self.base_query
            .filter(timestamp__gte=since)
            .annotate(hour=TruncHour('timestamp'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
        )
        
        # Action distribution
        action_dist = (
            self.base_query
            .filter(timestamp__gte=since)
            .values('action')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        return {
            'period_days': days,
            'total_events': self.base_query.filter(timestamp__gte=since).count(),
            'active_users': self.base_query.filter(timestamp__gte=since).values('user').distinct().count(),
            'top_users': list(user_stats),
            'hourly_distribution': list(hourly_dist),
            'action_distribution': list(action_dist),
            'generated_at': timezone.now().isoformat()
        }
    
    def detect_anomalies(self, hours=24, threshold=3):
        """Detect anomalous activity patterns"""
        since = timezone.now() - timedelta(hours=hours)
        
        anomalies = []
        
        # 1. Detect failed login spikes
        failed_logins = (
            self.base_query
            .filter(
                timestamp__gte=since,
                action='LOGIN_FAILED'
            )
            .values('user_ip')
            .annotate(count=Count('id'))
            .filter(count__gte=threshold)
        )
        
        for entry in failed_logins:
            anomalies.append({
                'type': 'FAILED_LOGIN_SPIKE',
                'severity': 'HIGH',
                'ip_address': entry['user_ip'],
                'failed_attempts': entry['count'],
                'time_window_hours': hours,
                'description': f'Multiple failed login attempts from IP {entry["user_ip"]}'
            })
        
        # 2. Detect unusual time activity
        unusual_hours = self._detect_unusual_hours(since)
        anomalies.extend(unusual_hours)
        
        # 3. Detect bulk operations
        bulk_ops = self._detect_bulk_operations(since, threshold)
        anomalies.extend(bulk_ops)
        
        return anomalies
    
    def _detect_unusual_hours(self, since):
        """Detect activity during unusual hours"""
        anomalies = []
        
        # Define business hours (e.g., 9 AM to 6 PM)
        business_hours = range(9, 18)
        
        unusual_activity = (
            self.base_query
            .filter(timestamp__gte=since)
            .annotate(hour=F('timestamp__hour'))
            .exclude(hour__in=business_hours)
            .filter(action__in=['DELETE', 'SOFT_DELETE', 'UPDATE'])
            .values('user_email', 'hour', 'action')
            .annotate(count=Count('id'))
            .filter(count__gte=3)
            .order_by('-count')
        )
        
        for entry in unusual_activity:
            anomalies.append({
                'type': 'UNUSUAL_HOUR_ACTIVITY',
                'severity': 'MEDIUM',
                'user': entry['user_email'],
                'action': entry['action'],
                'hour': entry['hour'],
                'count': entry['count'],
                'description': f'User {entry["user_email"]} performed {entry["count"]} {entry["action"]} actions during unusual hours'
            })
        
        return anomalies
    
    def _detect_bulk_operations(self, since, threshold):
        """Detect bulk operations"""
        anomalies = []
        
        bulk_ops = (
            self.base_query
            .filter(timestamp__gte=since)
            .filter(action__in=['DELETE', 'SOFT_DELETE', 'CREATE'])
            .annotate(time_window=Window(
                expression=Count('id'),
                partition_by=['user_email', 'action'],
                order_by=F('timestamp').asc(),
                frame=Window.RANGE(start=-timedelta(minutes=5), end=0)
            ))
            .filter(time_window__gte=threshold)
            .distinct('user_email', 'action')
            .values('user_email', 'action')
            .annotate(count=Count('id'))
        )
        
        for entry in bulk_ops:
            anomalies.append({
                'type': 'BULK_OPERATION',
                'severity': 'MEDIUM',
                'user': entry['user_email'],
                'action': entry['action'],
                'count': entry['count'],
                'time_window_minutes': 5,
                'description': f'User {entry["user_email"]} performed {entry["count"]} {entry["action"]} operations in a short time window'
            })
        
        return anomalies
    
    def generate_compliance_report(self, start_date, end_date):
        """Generate compliance audit report"""
        logs = self.base_query.filter(
            timestamp__range=[start_date, end_date]
        )
        
        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'summary': {
                'total_events': logs.count(),
                'unique_users': logs.values('user').distinct().count(),
                'unique_resources': logs.values('resource_type').distinct().count(),
            },
            'user_activity': self._get_user_compliance_activity(logs),
            'data_changes': self._get_data_change_summary(logs),
            'security_events': self._get_security_events(logs),
            'access_patterns': self._get_access_patterns(logs),
            'compliance_checks': self._run_compliance_checks(logs),
            'recommendations': [],
            'generated_at': timezone.now().isoformat()
        }
        
        return report
    
    def _get_user_compliance_activity(self, logs):
        """Get user activity for compliance"""
        user_stats = (
            logs.values('user_email')
            .annotate(
                total_actions=Count('id'),
                last_login=Max('timestamp', filter=Q(action='LOGIN')),
                password_changes=Count('id', filter=Q(action='PASSWORD_CHANGE')),
                permission_changes=Count('id', filter=Q(action='PERMISSION_CHANGE'))
            )
            .order_by('-total_actions')
        )
        
        return list(user_stats)
    
    def _get_data_change_summary(self, logs):
        """Get summary of data changes"""
        changes = (
            logs.filter(action__in=['CREATE', 'UPDATE', 'DELETE', 'SOFT_DELETE'])
            .values('resource_type')
            .annotate(
                creates=Count('id', filter=Q(action='CREATE')),
                updates=Count('id', filter=Q(action='UPDATE')),
                deletes=Count('id', filter=Q(action__in=['DELETE', 'SOFT_DELETE']))
            )
            .order_by('-creates')
        )
        
        return list(changes)
    
    def _get_security_events(self, logs):
        """Get security-related events"""
        security_events = logs.filter(
            severity__in=['WARNING', 'ERROR', 'CRITICAL']
        ).values('action', 'severity', 'resource_type').annotate(
            count=Count('id')
        ).order_by('-severity', '-count')
        
        return list(security_events)
    
    def _get_access_patterns(self, logs):
        """Get access patterns"""
        patterns = logs.filter(
            action__in=['READ', 'LOGIN', 'API_CALL']
        ).values(
            'user_email', 'resource_type', 'request_path'
        ).annotate(
            count=Count('id'),
            avg_duration=Avg('duration_ms'),
            last_access=Max('timestamp')
        ).order_by('-count')[:20]
        
        return list(patterns)
    
    def _run_compliance_checks(self, logs):
        """Run compliance checks"""
        checks = []
        
        # Check 1: Regular user activity
        inactive_users = self._find_inactive_users(logs)
        if inactive_users:
            checks.append({
                'check': 'USER_INACTIVITY',
                'status': 'WARNING',
                'description': f'Found {len(inactive_users)} inactive users',
                'details': inactive_users
            })
        
        # Check 2: Unusual deletion patterns
        unusual_deletions = self._find_unusual_deletions(logs)
        if unusual_deletions:
            checks.append({
                'check': 'UNUSUAL_DELETIONS',
                'status': 'WARNING',
                'description': 'Unusual deletion patterns detected',
                'details': unusual_deletions
            })
        
        # Check 3: Missing audit trails
        missing_trails = self._check_missing_audit_trails(logs)
        if missing_trails:
            checks.append({
                'check': 'MISSING_AUDIT_TRAILS',
                'status': 'ERROR',
                'description': 'Missing audit trails for critical operations',
                'details': missing_trails
            })
        
        return checks
    
    def _find_inactive_users(self, logs):
        """Find users with no recent activity"""
        active_users = logs.filter(
            timestamp__gte=timezone.now() - timedelta(days=30)
        ).values_list('user_email', flat=True).distinct()
        
        # Compare with all users (you might need to get this from User model)
        # For now, return empty list
        return []
    
    def _find_unusual_deletions(self, logs):
        """Find unusual deletion patterns"""
        unusual = []
        
        bulk_deletions = (
            logs.filter(action__in=['DELETE', 'SOFT_DELETE'])
            .values('user_email', 'resource_type')
            .annotate(count=Count('id'))
            .filter(count__gte=10)
        )
        
        for entry in bulk_deletions:
            unusual.append({
                'user': entry['user_email'],
                'resource': entry['resource_type'],
                'deletions': entry['count'],
                'description': f'Bulk deletion of {entry["count"]} {entry["resource_type"]} records'
            })
        
        return unusual
    
    def _check_missing_audit_trails(self, logs):
        """Check for missing audit trails"""
        # This would compare actual operations with expected audit trails
        # For now, return empty list
        return []
    

class RealTimeMonitor:
    """Real-time monitoring of audit logs"""
    
    def __init__(self, tenant_id=None):
        self.analyzer = AuditAnalyzer(tenant_id)
        self.alerts = []
        self.last_check = timezone.now()
    
    def check_for_alerts(self):
        """Check for new alerts based on recent activity"""
        since = self.last_check
        now = timezone.now()
        
        # Get recent logs
        recent_logs = self.analyzer.base_query.filter(
            timestamp__range=[since, now]
        )
        
        # Check for anomalies
        anomalies = self.analyzer.detect_anomalies(hours=1, threshold=5)
        
        # Generate alerts for new anomalies
        new_alerts = []
        for anomaly in anomalies:
            alert = {
                'type': anomaly['type'],
                'severity': anomaly.get('severity', 'MEDIUM'),
                'title': anomaly['description'],
                'details': anomaly,
                'timestamp': now,
                'is_new': True
            }
            new_alerts.append(alert)
        
        # Update last check time
        self.last_check = now
        
        return new_alerts
    
    def get_realtime_metrics(self):
        """Get real-time metrics dashboard"""
        now = timezone.now()
        
        metrics = {
            'current_minute': self.analyzer.base_query.filter(
                timestamp__gte=now - timedelta(minutes=1)
            ).count(),
            'current_hour': self.analyzer.base_query.filter(
                timestamp__gte=now - timedelta(hours=1)
            ).count(),
            'current_day': self.analyzer.base_query.filter(
                timestamp__gte=now - timedelta(days=1)
            ).count(),
            'active_users_now': self.analyzer.base_query.filter(
                timestamp__gte=now - timedelta(minutes=5)
            ).values('user').distinct().count(),
            'failed_logins_hour': self.analyzer.base_query.filter(
                timestamp__gte=now - timedelta(hours=1),
                action='LOGIN_FAILED'
            ).count(),
            'alerts_active': len([a for a in self.alerts if a.get('is_new', False)]),
            'last_updated': now.isoformat()
        }
        
        return metrics