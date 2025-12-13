from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Q
from django.utils import timezone
from apps.core.utils.tenant import get_current_tenant
from apps.students.models import Student
from apps.users.models import User
from apps.academics.models import SchoolClass
from apps.finance.models import Invoice, Payment
from apps.library.models import Book, BookIssue
from apps.hostel.models import Hostel, HostelAllocation
from apps.hr.models import Staff
from apps.inventory.models import Item
from apps.transportation.models import Vehicle, Route
from apps.events.models import Event
from apps.exams.models import Exam
from apps.security.models import SecurityIncident, AuditLog
from django.shortcuts import render



class MasterDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/master_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        # Students Statistics
        context['total_students'] = Student.objects.filter(tenant=tenant).count()
        context['active_students'] = Student.objects.filter(tenant=tenant, status='ACTIVE').count()
        context['alumni'] = Student.objects.filter(tenant=tenant, status='ALUMNI').count()
        
        # Users Statistics
        context['total_users'] = User.objects.filter(tenant=tenant).count()
        context['active_users'] = User.objects.filter(tenant=tenant, is_active=True).count()
        context['staff_count'] = Staff.objects.filter(tenant=tenant, is_active=True).count()
        
        # Academics Statistics
        context['total_courses'] = Course.objects.filter(tenant=tenant).count()
        context['total_classes'] = Class.objects.filter(tenant=tenant).count()
        
        # Finance Statistics
        context['total_invoices'] = Invoice.objects.filter(tenant=tenant).count()
        context['total_revenue'] = Payment.objects.filter(tenant=tenant).aggregate(
            total=Sum('amount')
        )['total'] or 0
        context['pending_invoices'] = Invoice.objects.filter(
            tenant=tenant, status='PENDING'
        ).count()
        
        # Library Statistics
        context['total_books'] = Book.objects.filter(tenant=tenant).count()
        context['books_issued'] = BookIssue.objects.filter(
            tenant=tenant, return_date__isnull=True
        ).count()
        
        # Hostel Statistics
        context['total_hostels'] = Hostel.objects.filter(tenant=tenant).count()
        context['hostel_allocations'] = HostelAllocation.objects.filter(
            tenant=tenant, is_active=True
        ).count()
        
        # Inventory Statistics
        context['total_items'] = Item.objects.filter(tenant=tenant, is_active=True).count()
        context['low_stock_items'] = Item.objects.filter(
            tenant=tenant, is_active=True, current_stock__lte=10
        ).count()
        
        # Transportation Statistics
        context['total_vehicles'] = Vehicle.objects.filter(tenant=tenant, is_active=True).count()
        context['total_routes'] = Route.objects.filter(tenant=tenant, is_active=True).count()
        
        # Events Statistics
        context['upcoming_events'] = Event.objects.filter(
            tenant=tenant, start_date__gte=timezone.now()
        ).count()
        
        # Exams Statistics
        context['upcoming_exams'] = Exam.objects.filter(
            tenant=tenant, start_date__gte=timezone.now()
        ).count()
        
        # Security Statistics
        context['open_incidents'] = SecurityIncident.objects.filter(
            tenant=tenant, status='OPEN'
        ).count()
        context['recent_audits'] = AuditLog.objects.filter(tenant=tenant).count()
        
        # Chart Data - Student Status Distribution
        student_status = Student.objects.filter(tenant=tenant).values('status').annotate(
            count=Count('id')
        )
        context['student_status_labels'] = [item['status'] for item in student_status]
        context['student_status_data'] = [item['count'] for item in student_status]
        
        # Chart Data - User Roles Distribution
        user_roles = User.objects.filter(tenant=tenant).values('role').annotate(
            count=Count('id')
        )
        context['user_roles_labels'] = [item['role'] for item in user_roles]
        context['user_roles_data'] = [item['count'] for item in user_roles]
        
        # Recent Activities (last 10 audit logs)
        context['recent_activities'] = AuditLog.objects.filter(
            tenant=tenant
        ).order_by('-created_at')[:10]
        
        return context

# ============================================
# CUSTOM ERROR VIEWS
# ============================================



def custom_page_not_found_view(request, exception):
    """Custom 404 error handler"""
    return render(request, 'errors/404.html', status=404)

def custom_error_view(request):
    """Custom 500 error handler"""
    return render(request, 'errors/500.html', status=500)

def custom_permission_denied_view(request, exception):
    """Custom 403 error handler"""
    return render(request, 'errors/403.html', status=403)

def custom_bad_request_view(request, exception):
    """Custom 400 error handler"""
    return render(request, 'errors/400.html', status=400)
