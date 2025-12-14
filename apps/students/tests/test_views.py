from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.students.views import StudentRegistrationStep1View
from apps.students.models import Student
from apps.students.forms import StudentForm
from apps.tenants.models import Tenant, Domain
from apps.academics.models import AcademicYear, SchoolClass, Section
from datetime import date

User = get_user_model()

class StudentRegistrationStep1ViewTest(TestCase):
    def setUp(self):
        # Create a tenant
        self.tenant = Tenant.objects.create(
            name="Test School",
            schema_name="test_school",
            subdomain="test-school",
            status="active",
            auto_create_schema=False
        )
        
        # Create a domain
        self.domain = Domain.objects.create(
            tenant=self.tenant,
            domain="test-school.com",
            is_primary=True
        )
        
        # Create academic year
        self.academic_year = AcademicYear.objects.create(
            name="2024-2025",
            code="AY2425",
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            tenant=self.tenant
        )
        
        # Create class and section
        self.school_class = SchoolClass.objects.create(
            name="Class 1",
            numeric_name=1,
            code="C1",
            level="PRIMARY",
            order=1,
            tenant=self.tenant
        )
        
        self.section = Section.objects.create(
            name="A",
            code="A",
            class_name=self.school_class,
            tenant=self.tenant
        )
        
        # Create a user
        self.user = User.objects.create_user(
            username='staff',
            email='staff@test-school.com',
            password='password'
        )

        self.factory = RequestFactory()

    def test_form_valid_sets_object_and_redirects(self):
        """
        Verify that form_valid sets self.object so get_success_url can use it.
        """
        url = reverse('students:registration_step1')
        
        form_data = {
            'first_name': 'Test',
            'last_name': 'Student',
            'date_of_birth': '2015-01-01',
            'gender': 'MALE',
            'admission_date': date.today(),
            'academic_year': self.academic_year.id,
            'current_class': self.school_class.id,
            'section': self.section.id,
            'personal_email': 'test.student@example.com',
            # Add other required fields if any, based on StudentForm
        }

        request = self.factory.post(url, data=form_data)
        request.user = self.user
        request.tenant = self.tenant
        request._messages = [] # Mock messages

        # Add message middleware mock storage
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        view = StudentRegistrationStep1View()
        view.setup(request)
        view.object = None # Ensure it's None initially

        # Validate form
        form = StudentForm(data=form_data, tenant=self.tenant)
        # Note: If form is invalid, we might need to debug valid data requirements
        # But we assume basic data is fine.
        if not form.is_valid():
            self.fail(f"Form is invalid: {form.errors}")
            
        # Call form_valid
        response = view.form_valid(form)
        
        # Check if self.object is set
        self.assertIsNotNone(view.object)
        self.assertIsInstance(view.object, Student)
        
        # Check redirection
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('students:registration_step2', kwargs={'student_id': view.object.id})
        self.assertEqual(response.url, expected_url)
