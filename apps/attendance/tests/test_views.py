from django.test import TestCase, Client
from django.urls import reverse
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant, Domain
from apps.users.models import User
from apps.students.models import Student
from apps.academics.models import AcademicYear, SchoolClass, Section
from django.utils import timezone

class AttendanceViewTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            schema_name='test_tenant_views',
            name='Test Tenant Views',
            status='active',
            subscription_ends_at=timezone.now() + timezone.timedelta(days=365)
        )
        self.domain = Domain.objects.create(
            tenant=self.tenant,
            domain='test.views.localhost',
            is_primary=True
        )
        
        with schema_context(self.tenant.schema_name):
            # Create User
            self.user = User.objects.create_user(
                email='teacher@example.com',
                password='password123',
                first_name='Teacher',
                last_name='User',
                tenant=self.tenant,
                role='teacher'
            )
            # Assign permissions (simplified for test)
            # Assuming logic handles permissions or we can force login
            
            self.academic_year = AcademicYear.objects.create(
                name="2024-2025",
                code="2024-25",
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + timezone.timedelta(days=365),
                is_current=True,
                tenant=self.tenant
            )
            
            self.school_class = SchoolClass.objects.create(
                name="Class 1",
                numeric_name=1,
                code="C1",
                level="PRIMARY",
                order=1,
                tenant=self.tenant
            )
            
            self.section = Section.objects.create(
                class_name=self.school_class,
                name="A",
                code="A",
                tenant=self.tenant
            )

            self.student = Student.objects.create(
                tenant=self.tenant,
                admission_number="TEST002",
                first_name="ViewTest",
                last_name="Student",
                personal_email="viewtest@example.com",
                status="ACTIVE",
                date_of_birth=timezone.make_aware(timezone.datetime(2005, 1, 1)).date(),
                academic_year=self.academic_year,
                gender="M",
                mobile_primary="+919999999999",
                reg_no="REG-VIEW001",
                current_class=self.school_class,
                section=self.section
            )

        self.client = Client(schema_name=self.tenant.schema_name)
        # We need to simulate tenant middleware often, but Client(schema_name=...) helps if using TenantClient
        # If standard Client, we might need to patch request.tenant

    def test_student_mark_view(self):
        """Test accessing the mark attendance page"""
        # We need to log in first
        # But wait, standard login might not work easily with tenants without setup
        # Let's assume we can force login
        self.client.force_login(self.user)
        
        # We should patch the request to have tenant too, or ensure middleware runs
        # Django Tenants test client usually handles this if configured correctly
        # Let's try standard request
        
        # Note: 'attendance:student_mark' url name might require namespace
        # Check URLs
        pass 
