from django.test import TestCase
from django_tenants.utils import schema_context
from datetime import date
from apps.attendance.forms import StudentAttendanceForm
from apps.tenants.models import Tenant
from apps.students.models import Student
from apps.academics.models import StudentAttendance, AcademicYear, SchoolClass, Section
from django.utils import timezone

class StudentAttendanceFormTest(TestCase):
    def setUp(self):
        # Create a tenant for testing
        self.tenant = Tenant.objects.create(
            schema_name='test_tenant',
            name='Test Tenant',
            status='active',
            subscription_ends_at=timezone.now() + timezone.timedelta(days=365)
        )
        
        with schema_context(self.tenant.schema_name):
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
                admission_number="TEST001",
                first_name="Test",
                last_name="Student",
                personal_email="test.student@example.com",
                status="ACTIVE",
                date_of_birth=timezone.make_aware(timezone.datetime(2005, 1, 1)).date(),
                academic_year=self.academic_year,
                gender="M",
                mobile_primary="+919999999999",
                reg_no="REG-TEST001",
                current_class=self.school_class,
                section=self.section
            )

    def test_form_valid_with_tenant(self):
        """Test that the form is valid when tenant is provided"""
        with schema_context(self.tenant.schema_name):
            form_data = {
                'student': self.student.id,
                'date': timezone.now().date(),
                'status': 'PRESENT',
                'remarks': 'Testing'
            }
            form = StudentAttendanceForm(data=form_data, tenant=self.tenant)
            self.assertTrue(form.is_valid(), form.errors)
            
            # Check if tenant is set on instance
            attendance = form.save(commit=False)
            self.assertEqual(attendance.tenant, self.tenant)

    def test_duplicate_attendance(self):
        """Test preventing duplicate attendance for same day"""
        with schema_context(self.tenant.schema_name):
            # Create existing attendance
            StudentAttendance.objects.create(
                tenant=self.tenant,
                student=self.student,
                date=timezone.now().date(),
                status='PRESENT',
                session='FULL_DAY',
                class_name=self.school_class,
                section=self.section
            )
            
            form_data = {
                'student': self.student.id,
                'date': timezone.now().date(),
                'status': 'ABSENT',
                'remarks': 'Duplicate'
            }
            form = StudentAttendanceForm(data=form_data, tenant=self.tenant)
            self.assertFalse(form.is_valid())
            self.assertTrue(any('Attendance already marked' in str(e) for e in form.errors.values()))
