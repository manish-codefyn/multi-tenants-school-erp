from django.test import TestCase
from django_tenants.utils import schema_context
from datetime import date
from apps.academics.forms import AcademicYearForm, SchoolClassForm, SectionForm
from apps.tenants.models import Tenant
from apps.academics.models import AcademicYear, SchoolClass, Section
from django.utils import timezone

class AcademicsFormsTest(TestCase):
    def setUp(self):
        # Create a tenant for testing
        self.tenant = Tenant.objects.create(
            schema_name='test_academics_forms',
            name='Test Academics Forms Tenant',
            status='active',
            subscription_ends_at=timezone.now() + timezone.timedelta(days=365)
        )

    def test_academic_year_form_dates(self):
        """Test AcademicYearForm validates end_date > start_date"""
        with schema_context(self.tenant.schema_name):
            form_data = {
                'name': '2024-2025',
                'code': 'AY2425',
                'start_date': timezone.now().date(),
                'end_date': timezone.now().date() + timezone.timedelta(days=365),
                'is_current': True,
                'has_terms': True
            }
            form = AcademicYearForm(data=form_data)
            self.assertTrue(form.is_valid())
            
            # Invalid dates
            form_data['end_date'] = form_data['start_date'] - timezone.timedelta(days=1)
            form = AcademicYearForm(data=form_data)
            self.assertFalse(form.is_valid())
            self.assertIn('End date must be after start date', form.errors.get('__all__', []) + form.non_field_errors())

    def test_school_class_form(self):
        """Test SchoolClassForm validation"""
        with schema_context(self.tenant.schema_name):
            form_data = {
                'name': 'Class 1',
                'numeric_name': 1,
                'code': 'C1',
                'level': 'PRIMARY',
                'order': 1,
                'pass_percentage': 33.00,
                'max_strength': 40,
                'tuition_fee': 1000.00,
                'is_active': True
            }
            form = SchoolClassForm(data=form_data)
            self.assertTrue(form.is_valid(), form.errors)

    def test_section_form(self):
        """Test SectionForm validation"""
        with schema_context(self.tenant.schema_name):
            # Need a class first
            school_class = SchoolClass.objects.create(
                name="Class 1",
                numeric_name=1,
                code="C1",
                level="PRIMARY",
                order=1,
                tenant=self.tenant
            )
            
            form_data = {
                'name': 'A',
                'code': 'A',
                'class_name': school_class.id,
                'max_strength': 40,
                'is_active': True
            }
            # We need to pass request to form to filter querysets if it uses request.tenant
            # But here we are Mocking request or form init logic might handle it
            # The form uses get_current_tenant() if request is passed.
            # Let's try without request first, keys should be enough if queryset allows
            # But the form __init__ filters queryset based on tenant if request is present
            # If request is NOT present, it might use all objects or empty
            
            # Let's check SectionForm __init__ again
            # if self.request: ...
            
            # Since we are not passing request in this simple test, standard validation applies on existing FK
            form = SectionForm(data=form_data)
            self.assertTrue(form.is_valid(), form.errors)
