from django.test import TestCase
from django_tenants.utils import schema_context
from django.utils import timezone
from apps.tenants.models import Tenant
from apps.academics.models import AcademicYear, SchoolClass, Section, Subject, ClassSubject

class AcademicsModelsTest(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            schema_name='test_academics',
            name='Test Academics Tenant',
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

    def test_academic_year_creation(self):
        """Test AcademicYear creation and string representation"""
        with schema_context(self.tenant.schema_name):
            self.assertEqual(str(self.academic_year).split('(')[0].strip(), "2024-2025")
            self.assertTrue(self.academic_year.is_current)

    def test_school_class_and_section(self):
        """Test creation of SchoolClass and Section"""
        with schema_context(self.tenant.schema_name):
            school_class = SchoolClass.objects.create(
                name="Class 1",
                numeric_name=1,
                code="C1",
                level="PRIMARY",
                order=1,
                tenant=self.tenant
            )
            
            section = Section.objects.create(
                class_name=school_class,
                name="A",
                code="A",
                tenant=self.tenant
            )
            
            self.assertEqual(str(school_class), "Class 1")
            self.assertEqual(str(section), "Class 1 - A")
            self.assertEqual(section.class_name, school_class)

    def test_subject_and_class_assignment(self):
        """Test Subject creation and assignment to class"""
        with schema_context(self.tenant.schema_name):
            subject = Subject.objects.create(
                name="Mathematics",
                code="MATH",
                subject_type="CORE",
                credit_hours=4,
                tenant=self.tenant
            )
            
            school_class = SchoolClass.objects.create(
                name="Class 10",
                numeric_name=10,
                code="C10",
                level="HIGH",
                order=10,
                tenant=self.tenant
            )
            
            class_subject = ClassSubject.objects.create(
                class_name=school_class,
                subject=subject,
                academic_year=self.academic_year,
                is_compulsory=True,
                tenant=self.tenant
            )
            
            self.assertEqual(str(subject), "Mathematics")
            self.assertEqual(class_subject.subject, subject)
            self.assertEqual(class_subject.class_name, school_class)
