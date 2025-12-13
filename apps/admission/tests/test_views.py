from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date
from apps.admission.models import AdmissionCycle, AdmissionProgram
from apps.academics.models import AcademicYear
from apps.tenants.models import Tenant

class AdmissionViewTests(TestCase):
    def setUp(self):
        # Create tenant
        self.tenant = Tenant.objects.create(name="Test School", schema_name="test_school", domain_url="test.school.com")
        
        # Create academic year
        self.academic_year = AcademicYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            code="AY2425"
        )
        
        # Create active admission cycle
        self.cycle = AdmissionCycle.objects.create(
            name="Admission 2024",
            academic_year=self.academic_year,
            code="ADM2024",
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
            status="ACTIVE",
            tenant=self.tenant,
            is_active=True
        )

    def test_landing_view(self):
        """Test admission landing page"""
        response = self.client.get(reverse('admission:landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admission 2024")

    def test_apply_view_loads(self):
        """Test application form loads"""
        response = self.client.get(reverse('admission:apply'))
        self.assertEqual(response.status_code, 200)

    def test_status_check_view(self):
        """Test status check view"""
        response = self.client.get(reverse('admission:check_status'))
        self.assertEqual(response.status_code, 200)
