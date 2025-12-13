# management/commands/load_academics_dummy.py
import random
import sys
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import models
from django_tenants.utils import schema_context, tenant_context
from apps.academics.models import (
    AcademicYear, Term, SchoolClass, Section, House, Subject,
    ClassSubject, TimeTable, Attendance, Holiday, StudyMaterial,
    Syllabus, Stream, ClassTeacher, HousePoints
)
from apps.students.models import Student
from apps.tenants.models import Tenant
from faker import Faker

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Populates the academics module with dummy data for tenants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Tenant schema name or ID to populate data for',
        )
        parser.add_argument(
            '--all-tenants',
            action='store_true',
            help='Populate data for all active tenants',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )
        parser.add_argument(
            '--academic-years',
            type=int,
            default=3,
            help='Number of academic years to create',
        )
        parser.add_argument(
            '--students-per-class',
            type=int,
            default=20,
            help='Number of students per class',
        )
        parser.add_argument(
            '--public-schema',
            action='store_true',
            help='Also populate public schema with reference data',
        )
        parser.add_argument(
            '--skip-teachers',
            action='store_true',
            help='Skip teacher creation/assignment',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO("Starting to populate academics data..."))
        
        # Temporarily patch BaseModel to skip tenant validation
        self.patch_base_model()
        
        try:
            if options['all_tenants']:
                self.populate_all_tenants(options)
            elif options['tenant']:
                self.populate_single_tenant(options)
            elif options['public_schema']:
                self.populate_public_schema(options)
            else:
                raise CommandError(
                    "Please specify --tenant, --all-tenants, or --public-schema"
                )
        finally:
            # Always restore the original BaseModel
            self.unpatch_base_model()
        
        self.stdout.write(self.style.SUCCESS("Successfully populated academics data!"))

    def patch_base_model(self):
        """Temporarily patch BaseModel.save() to skip tenant validation"""
        from apps.core.models import BaseModel
        
        self.original_save = BaseModel.save
        
        def patched_save(self, *args, **kwargs):
            # Calculate data integrity signature if not present
            if not self.data_signature and hasattr(self, 'calculate_signature'):
                self.data_signature = self.calculate_signature()
            
            # Skip tenant validation for management commands
            if not self.tenant_id:
                from django.db import connection
                from django_tenants.utils import get_tenant_model
                
                # Try to get tenant from schema context
                if connection.schema_name and connection.schema_name != 'public':
                    try:
                        TenantModel = get_tenant_model()
                        tenant = TenantModel.objects.get(
                            schema_name=connection.schema_name
                        )
                        self.tenant = tenant
                    except Exception:
                        # If we can't get tenant, skip tenant assignment
                        pass
            
            # Call the parent save method
            super(BaseModel.__bases__[-1], self).save(*args, **kwargs)
        
        BaseModel.save = patched_save
    
    def unpatch_base_model(self):
        """Restore original BaseModel.save()"""
        if hasattr(self, 'original_save'):
            from apps.core.models import BaseModel
            BaseModel.save = self.original_save

    def populate_all_tenants(self, options):
        """Populate data for all active tenants"""
        tenants = Tenant.objects.filter(is_active=True).exclude(schema_name='public')
        
        if not tenants.exists():
            self.stdout.write(self.style.WARNING("No active tenants found."))
            return
        
        for tenant in tenants:
            self.stdout.write(self.style.SUCCESS(f"\nProcessing tenant: {tenant.name}"))
            self.populate_for_tenant(tenant, options)

    def populate_single_tenant(self, options):
        """Populate data for a specific tenant"""
        tenant_identifier = options['tenant']
        
        try:
            # Try to get tenant by schema name
            tenant = Tenant.objects.get(schema_name=tenant_identifier)
        except Tenant.DoesNotExist:
            try:
                # Try to get tenant by ID
                tenant = Tenant.objects.get(id=tenant_identifier)
            except (Tenant.DoesNotExist, ValueError):
                try:
                    # Try to get tenant by name
                    tenant = Tenant.objects.get(name=tenant_identifier)
                except Tenant.DoesNotExist:
                    raise CommandError(f"Tenant '{tenant_identifier}' not found.")
        
        self.populate_for_tenant(tenant, options)

    def populate_public_schema(self, options):
        """Populate reference data in public schema"""
        self.stdout.write("Populating public schema with reference data...")
        
        with schema_context('public'):
            self.create_public_reference_data(options)

    def populate_for_tenant(self, tenant, options):
        """Populate data within a tenant's schema context"""
        self.stdout.write(f"Populating data for tenant: {tenant.name} ({tenant.schema_name})")
        
        with tenant_context(tenant):
            try:
                if options['clear']:
                    self.clear_tenant_data()
                
                # Create academic years
                academic_years = self.create_academic_years(options['academic_years'])
                
                if not academic_years:
                    self.stdout.write(self.style.WARNING("  Skipping due to no academic years created"))
                    return
                
                # Create current academic year
                current_year = academic_years[0]
                
                # Create terms for each academic year
                terms_by_year = {}
                for year in academic_years:
                    terms = self.create_terms(year)
                    terms_by_year[year.id] = terms
                
                # Create school classes
                classes = self.create_school_classes(options)
                
                if not classes:
                    self.stdout.write(self.style.WARNING("  No classes created, skipping further operations"))
                    return
                
                # Create sections for each class
                sections_by_class = {}
                for school_class in classes:
                    sections = self.create_sections(school_class, options)
                    sections_by_class[school_class.id] = sections
                
                # Create houses
                houses = self.create_houses(options)
                
                # Create subjects
                subjects = self.create_subjects(options)
                
                # Create class subjects
                class_subjects = self.create_class_subjects(classes, subjects, current_year, options)
                
                # Create streams (only if we have Class 11)
                streams = []
                class_11_exists = any(c.numeric_name == 11 for c in classes)
                if class_11_exists:
                    streams = self.create_streams(classes, subjects, options)
                
                # Create timetable
                self.create_timetable(current_year, classes, sections_by_class, class_subjects, options)
                
                # Create holidays
                self.create_holidays(academic_years, classes, options)
                
                # Create study materials
                self.create_study_materials(classes, subjects, class_subjects, options)
                
                # Create syllabus
                self.create_syllabus(classes, subjects, academic_years, options)
                
                # Create class teachers
                if not options['skip_teachers']:
                    self.create_class_teachers(classes, sections_by_class, current_year, options)
                
                # Create attendance records
                self.create_attendance_records(options['students_per_class'], classes, sections_by_class, options)
                
                # Create house points
                self.create_house_points(houses, options)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error populating tenant {tenant.name}: {str(e)}"))
                import traceback
                traceback.print_exc()
                # Don't raise - continue with next tenant
                return

    def create_public_reference_data(self, options):
        """Create reference data in public schema that can be shared across tenants"""
        self.stdout.write("Creating public reference data (if needed)...")

    def clear_tenant_data(self):
        """Clear existing data within tenant context"""
        self.stdout.write(self.style.WARNING("Clearing existing data..."))
        
        models_to_clear = [
            HousePoints, ClassTeacher, Syllabus, StudyMaterial,
            Holiday, Attendance, TimeTable, ClassSubject,
            Stream, Subject, House, Section, SchoolClass,
            Term, AcademicYear
        ]
        
        for model in models_to_clear:
            count, _ = model.objects.all().delete()
            self.stdout.write(f"  Cleared {model.__name__}: {count} records")

    def create_academic_years(self, count):
        """Create academic years"""
        self.stdout.write("Creating academic years...")
        years = []
        
        for i in range(count):
            start_year = 2022 + i
            end_year = start_year + 1
            
            name = f"Academic Year {start_year}-{end_year}"
            code = f"AY{start_year}{end_year}"
            
            # Set dates
            start_date = datetime(start_year, 4, 1).date()  # April 1st
            end_date = datetime(end_year, 3, 31).date()     # March 31st
            
            # Set current year (most recent)
            is_current = (i == 0)
            
            try:
                academic_year = AcademicYear.objects.create(
                    name=name,
                    code=code,
                    start_date=start_date,
                    end_date=end_date,
                    is_current=is_current,
                    has_terms=True
                )
                years.append(academic_year)
                self.stdout.write(f"  Created {academic_year}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Error creating academic year: {e}"))
        
        return years

    def create_terms(self, academic_year):
        """Create terms for an academic year"""
        self.stdout.write(f"Creating terms for {academic_year.name}...")
        terms = []
        
        term_data = [
            {
                'name': 'First Term',
                'term_type': 'FIRST_TERM',
                'order': 1,
                'start_date': academic_year.start_date,
                'end_date': datetime(academic_year.start_date.year, 6, 30).date(),
            },
            {
                'name': 'Second Term',
                'term_type': 'SECOND_TERM',
                'order': 2,
                'start_date': datetime(academic_year.start_date.year, 7, 1).date(),
                'end_date': datetime(academic_year.start_date.year, 9, 30).date(),
            },
            {
                'name': 'Third Term',
                'term_type': 'THIRD_TERM',
                'order': 3,
                'start_date': datetime(academic_year.start_date.year, 10, 1).date(),
                'end_date': datetime(academic_year.end_date.year, 1, 15).date(),
            },
            {
                'name': 'Annual',
                'term_type': 'ANNUAL',
                'order': 4,
                'start_date': datetime(academic_year.end_date.year, 1, 16).date(),
                'end_date': academic_year.end_date,
            }
        ]
        
        for term_info in term_data:
            # Check if term is current based on today's date
            today = timezone.now().date()
            is_current = term_info['start_date'] <= today <= term_info['end_date']
            
            try:
                term = Term.objects.create(
                    academic_year=academic_year,
                    name=term_info['name'],
                    term_type=term_info['term_type'],
                    order=term_info['order'],
                    start_date=term_info['start_date'],
                    end_date=term_info['end_date'],
                    is_current=is_current
                )
                terms.append(term)
                self.stdout.write(f"  Created {term}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Error creating term: {e}"))
        
        return terms

    def create_school_classes(self, options):
        """Create school classes from Nursery to 12th"""
        self.stdout.write("Creating school classes...")
        classes = []
        
        class_data = [
            # Pre-Primary
            {'name': 'Nursery', 'numeric_name': 0, 'code': 'NUR', 'level': 'PRE_PRIMARY', 'order': 1, 'default_pass_percentage': 0},
            {'name': 'LKG', 'numeric_name': 0, 'code': 'LKG', 'level': 'PRE_PRIMARY', 'order': 2, 'default_pass_percentage': 0},
            {'name': 'UKG', 'numeric_name': 0, 'code': 'UKG', 'level': 'PRE_PRIMARY', 'order': 3, 'default_pass_percentage': 0},
            
            # Primary (1-5)
            {'name': 'Class 1', 'numeric_name': 1, 'code': 'I', 'level': 'PRIMARY', 'order': 4, 'default_pass_percentage': 33},
            {'name': 'Class 2', 'numeric_name': 2, 'code': 'II', 'level': 'PRIMARY', 'order': 5, 'default_pass_percentage': 33},
            {'name': 'Class 3', 'numeric_name': 3, 'code': 'III', 'level': 'PRIMARY', 'order': 6, 'default_pass_percentage': 33},
            {'name': 'Class 4', 'numeric_name': 4, 'code': 'IV', 'level': 'PRIMARY', 'order': 7, 'default_pass_percentage': 33},
            {'name': 'Class 5', 'numeric_name': 5, 'code': 'V', 'level': 'PRIMARY', 'order': 8, 'default_pass_percentage': 33},
            
            # Middle (6-8)
            {'name': 'Class 6', 'numeric_name': 6, 'code': 'VI', 'level': 'MIDDLE', 'order': 9, 'default_pass_percentage': 35},
            {'name': 'Class 7', 'numeric_name': 7, 'code': 'VII', 'level': 'MIDDLE', 'order': 10, 'default_pass_percentage': 35},
            {'name': 'Class 8', 'numeric_name': 8, 'code': 'VIII', 'level': 'MIDDLE', 'order': 11, 'default_pass_percentage': 35},
            
            # High (9-10)
            {'name': 'Class 9', 'numeric_name': 9, 'code': 'IX', 'level': 'HIGH', 'order': 12, 'default_pass_percentage': 40},
            {'name': 'Class 10', 'numeric_name': 10, 'code': 'X', 'level': 'HIGH', 'order': 13, 'default_pass_percentage': 40},
            
            # Senior Secondary (11-12)
            {'name': 'Class 11', 'numeric_name': 11, 'code': 'XI', 'level': 'SENIOR', 'order': 14, 'default_pass_percentage': 40},
            {'name': 'Class 12', 'numeric_name': 12, 'code': 'XII', 'level': 'SENIOR', 'order': 15, 'default_pass_percentage': 40},
        ]
        
        # Get some teachers to assign as class teachers
        teachers = User.objects.filter(role='teacher') if not options['skip_teachers'] else []
        
        for i, class_info in enumerate(class_data):
            # Assign tuition fee based on level
            if class_info['level'] in ['PRE_PRIMARY', 'PRIMARY']:
                tuition_fee = 10000 + (i * 1000)
            elif class_info['level'] in ['MIDDLE']:
                tuition_fee = 15000 + (i * 1000)
            elif class_info['level'] in ['HIGH']:
                tuition_fee = 20000 + (i * 1000)
            else:
                tuition_fee = 25000 + (i * 1000)
            
            # Assign class teacher if available
            class_teacher = teachers[i % len(teachers)] if teachers else None
            
            try:
                school_class = SchoolClass.objects.create(
                    name=class_info['name'],
                    numeric_name=class_info['numeric_name'],
                    code=class_info['code'],
                    level=class_info['level'],
                    order=class_info['order'],
                    pass_percentage=class_info['default_pass_percentage'],
                    max_strength=40,
                    tuition_fee=tuition_fee,
                    class_teacher=class_teacher,
                    is_active=True
                )
                classes.append(school_class)
                self.stdout.write(f"  Created {school_class.name}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error creating class {class_info['name']}: {e}"))
        
        return classes

    def create_sections(self, school_class, options):
        """Create sections for a school class"""
        sections = []
        
        # Create 2-3 sections per class
        num_sections = 2 if school_class.numeric_name <= 5 else 3
        section_names = ['A', 'B', 'C']
        
        teachers = User.objects.filter(role='teacher') if not options['skip_teachers'] else []
        
        for i in range(num_sections):
            section_name = section_names[i]
            section_code = f"{school_class.code}{section_name}"
            
            # Assign section incharge
            section_incharge = teachers[(i + 1) % len(teachers)] if teachers else None
            
            try:
                section = Section.objects.create(
                    class_name=school_class,
                    name=section_name,
                    code=section_code,
                    max_strength=40,
                    section_incharge=section_incharge,
                    room_number=f"Room {school_class.numeric_name}{section_name}",
                    is_active=True
                )
                sections.append(section)
                self.stdout.write(f"    Created section {section}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"    Error creating section: {e}"))
        
        return sections

    def create_houses(self, options):
        """Create school houses"""
        self.stdout.write("Creating houses...")
        houses = []
        
        house_data = [
            {'name': 'Red House', 'code': 'RED', 'color': 'Red', 'motto': 'Courage and Strength'},
            {'name': 'Blue House', 'code': 'BLUE', 'color': 'Blue', 'motto': 'Truth and Wisdom'},
            {'name': 'Green House', 'code': 'GREEN', 'color': 'Green', 'motto': 'Growth and Harmony'},
            {'name': 'Yellow House', 'code': 'YELLOW', 'color': 'Yellow', 'motto': 'Energy and Joy'},
        ]
        
        teachers = User.objects.filter(role='teacher') if not options['skip_teachers'] else []
        
        for i, house_info in enumerate(house_data):
            house_master = teachers[i % len(teachers)] if teachers else None
            
            try:
                house = House.objects.create(
                    name=house_info['name'],
                    code=house_info['code'],
                    color=house_info['color'],
                    motto=house_info['motto'],
                    house_master=house_master,
                    total_points=random.randint(100, 500),
                    description=f"The {house_info['name']} represents {house_info['color'].lower()} values."
                )
                houses.append(house)
                self.stdout.write(f"  Created {house.name}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Error creating house: {e}"))
        
        return houses

    def create_subjects(self, options):
        """Create school subjects"""
        self.stdout.write("Creating subjects...")
        subjects = []
        
        subject_data = [
            # Core Subjects
            {'name': 'Mathematics', 'code': 'MATH', 'subject_type': 'CORE', 'subject_group': 'SCIENCE', 
             'has_practical': False, 'has_project': True, 'credit_hours': 6, 'max_marks': 100, 'default_is_scoring': True},
            
            {'name': 'Science', 'code': 'SCI', 'subject_type': 'CORE', 'subject_group': 'SCIENCE',
             'has_practical': True, 'has_project': True, 'credit_hours': 6, 'max_marks': 100, 'default_is_scoring': True},
            
            {'name': 'English', 'code': 'ENG', 'subject_type': 'CORE', 'subject_group': 'GENERAL',
             'has_practical': False, 'has_project': False, 'credit_hours': 5, 'max_marks': 100, 'default_is_scoring': True},
            
            {'name': 'Hindi', 'code': 'HIN', 'subject_type': 'LANGUAGE', 'subject_group': 'GENERAL',
             'has_practical': False, 'has_project': False, 'credit_hours': 4, 'max_marks': 100, 'default_is_scoring': True},
            
            {'name': 'Social Studies', 'code': 'SST', 'subject_type': 'CORE', 'subject_group': 'ARTS',
             'has_practical': False, 'has_project': True, 'credit_hours': 4, 'max_marks': 100, 'default_is_scoring': True},
            
            # Languages
            {'name': 'Sanskrit', 'code': 'SAN', 'subject_type': 'LANGUAGE', 'subject_group': 'GENERAL',
             'has_practical': False, 'has_project': False, 'credit_hours': 3, 'max_marks': 100, 'default_is_scoring': True},
            
            {'name': 'French', 'code': 'FRE', 'subject_type': 'LANGUAGE', 'subject_group': 'GENERAL',
             'has_practical': False, 'has_project': False, 'credit_hours': 3, 'max_marks': 100, 'default_is_scoring': True},
            
            # Science Stream Subjects
            {'name': 'Physics', 'code': 'PHY', 'subject_type': 'CORE', 'subject_group': 'SCIENCE',
             'has_practical': True, 'has_project': True, 'credit_hours': 5, 'max_marks': 100, 'default_is_scoring': True},
            
            {'name': 'Chemistry', 'code': 'CHEM', 'subject_type': 'CORE', 'subject_group': 'SCIENCE',
             'has_practical': True, 'has_project': True, 'credit_hours': 5, 'max_marks': 100, 'default_is_scoring': True},
            
            {'name': 'Biology', 'code': 'BIO', 'subject_type': 'CORE', 'subject_group': 'SCIENCE',
             'has_practical': True, 'has_project': True, 'credit_hours': 5, 'max_marks': 100, 'default_is_scoring': True},
            
            # Commerce Stream Subjects
            {'name': 'Accountancy', 'code': 'ACC', 'subject_type': 'ELECTIVE', 'subject_group': 'COMMERCE',
             'has_practical': False, 'has_project': True, 'credit_hours': 5, 'max_marks': 100, 'default_is_scoring': True},
            
            {'name': 'Business Studies', 'code': 'BST', 'subject_type': 'ELECTIVE', 'subject_group': 'COMMERCE',
             'has_practical': False, 'has_project': True, 'credit_hours': 4, 'max_marks': 100, 'default_is_scoring': True},
            
            {'name': 'Economics', 'code': 'ECO', 'subject_type': 'ELECTIVE', 'subject_group': 'COMMERCE',
             'has_practical': False, 'has_project': True, 'credit_hours': 4, 'max_marks': 100, 'default_is_scoring': True},
            
            # Arts Stream Subjects
            {'name': 'History', 'code': 'HIS', 'subject_type': 'ELECTIVE', 'subject_group': 'ARTS',
             'has_practical': False, 'has_project': True, 'credit_hours': 4, 'max_marks': 100, 'default_is_scoring': True},
            
            {'name': 'Political Science', 'code': 'POL', 'subject_type': 'ELECTIVE', 'subject_group': 'ARTS',
             'has_practical': False, 'has_project': True, 'credit_hours': 4, 'max_marks': 100, 'default_is_scoring': True},
            
            {'name': 'Geography', 'code': 'GEO', 'subject_type': 'ELECTIVE', 'subject_group': 'ARTS',
             'has_practical': True, 'has_project': True, 'credit_hours': 4, 'max_marks': 100, 'default_is_scoring': True},
            
            # Co-curricular
            {'name': 'Physical Education', 'code': 'PE', 'subject_type': 'CO_CURRICULAR', 'subject_group': 'GENERAL',
             'has_practical': True, 'has_project': False, 'credit_hours': 2, 'max_marks': 50, 'default_is_scoring': False},
            
            {'name': 'Art & Craft', 'code': 'ART', 'subject_type': 'CO_CURRICULAR', 'subject_group': 'GENERAL',
             'has_practical': True, 'has_project': False, 'credit_hours': 2, 'max_marks': 50, 'default_is_scoring': False},
            
            {'name': 'Computer Science', 'code': 'COMP', 'subject_type': 'CORE', 'subject_group': 'VOCATIONAL',
             'has_practical': True, 'has_project': True, 'credit_hours': 4, 'max_marks': 100, 'default_is_scoring': True},
        ]
        
        for subject_info in subject_data:
            try:
                subject = Subject.objects.create(
                    name=subject_info['name'],
                    code=subject_info['code'],
                    subject_type=subject_info['subject_type'],
                    subject_group=subject_info['subject_group'],
                    has_practical=subject_info['has_practical'],
                    has_project=subject_info['has_project'],
                    credit_hours=subject_info['credit_hours'],
                    max_marks=subject_info['max_marks'],
                    pass_marks=33,
                    is_scoring=subject_info['default_is_scoring'],
                    description=f"{subject_info['name']} subject for school curriculum.",
                    is_active=True
                )
                subjects.append(subject)
                self.stdout.write(f"  Created {subject.name}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Error creating subject {subject_info['name']}: {e}"))
        
        return subjects

    def create_class_subjects(self, classes, subjects, academic_year, options):
        """Create class-subject associations"""
        self.stdout.write("Creating class subjects...")
        class_subjects = []
        
        teachers = User.objects.filter(role='teacher') if not options['skip_teachers'] else []
        
        for school_class in classes:
            # Determine which subjects to assign based on class level
            if school_class.level in ['PRE_PRIMARY']:
                subject_codes = ['ENG', 'HIN', 'ART']
                periods = 3
            elif school_class.level in ['PRIMARY']:
                subject_codes = ['MATH', 'SCI', 'ENG', 'HIN', 'SST', 'ART', 'PE']
                periods = 5
            elif school_class.level in ['MIDDLE']:
                subject_codes = ['MATH', 'SCI', 'ENG', 'HIN', 'SST', 'COMP', 'PE', 'ART']
                periods = 6
            elif school_class.level in ['HIGH']:
                subject_codes = ['MATH', 'PHY', 'CHEM', 'BIO', 'ENG', 'HIN', 'COMP', 'PE']
                periods = 7
            else:  # SENIOR
                # Different streams for senior classes
                subject_codes = ['ENG', 'HIN', 'PE']
                periods = 8
            
            # Get subjects by code
            class_subjects_list = [s for s in subjects if s.code in subject_codes]
            
            for i, subject in enumerate(class_subjects_list):
                teacher = teachers[i % len(teachers)] if teachers else None
                
                # Adjust periods for co-curricular subjects
                periods_per_week = 2 if subject.subject_type in ['CO_CURRICULAR', 'EXTRA_CURRICULAR'] else periods
                
                try:
                    class_subject = ClassSubject.objects.create(
                        class_name=school_class,
                        subject=subject,
                        is_compulsory=True,
                        periods_per_week=periods_per_week,
                        teacher=teacher,
                        academic_year=academic_year
                    )
                    class_subjects.append(class_subject)
                    self.stdout.write(f"    Created {school_class.name} - {subject.name}")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"    Error creating class subject: {e}"))
        
        return class_subjects

    def create_streams(self, classes, subjects, options):
        """Create academic streams"""
        self.stdout.write("Creating streams...")
        streams = []
        
        # Find Class 11
        class_11 = None
        for school_class in classes:
            if school_class.numeric_name == 11:
                class_11 = school_class
                break
        
        if not class_11:
            self.stdout.write("  No Class 11 found, skipping stream creation")
            return streams
        
        stream_data = [
            {
                'name': 'Science Stream',
                'code': 'SCIENCE',
                'description': 'Science stream with Physics, Chemistry, and Biology',
                'subject_codes': ['PHY', 'CHEM', 'BIO', 'MATH', 'COMP']
            },
            {
                'name': 'Commerce Stream',
                'code': 'COMMERCE',
                'description': 'Commerce stream with Accountancy, Business Studies, and Economics',
                'subject_codes': ['ACC', 'BST', 'ECO', 'MATH', 'COMP']
            },
            {
                'name': 'Arts Stream',
                'code': 'ARTS',
                'description': 'Arts stream with History, Political Science, and Geography',
                'subject_codes': ['HIS', 'POL', 'GEO', 'ECO', 'COMP']
            },
        ]
        
        for stream_info in stream_data:
            try:
                stream = Stream.objects.create(
                    name=stream_info['name'],
                    code=stream_info['code'],
                    description=stream_info['description'],
                    available_from_class=class_11,
                    is_active=True
                )
                
                # Add subjects to stream
                stream_subjects = [s for s in subjects if s.code in stream_info['subject_codes']]
                stream.subjects.set(stream_subjects)
                
                streams.append(stream)
                self.stdout.write(f"  Created {stream.name}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Error creating stream: {e}"))
        
        return streams

    def create_timetable(self, academic_year, classes, sections_by_class, class_subjects, options):
        """Create timetable for each class-section"""
        self.stdout.write("Creating timetable...")
        
        days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
        period_times = [
            ('08:30', '09:15'),
            ('09:15', '10:00'),
            ('10:00', '10:45'),
            ('10:45', '11:00'),  # Break
            ('11:00', '11:45'),
            ('11:45', '12:30'),
            ('12:30', '13:15'),
            ('13:15', '14:00'),  # Lunch break on some days
        ]
        
        timetable_created = 0
        
        for school_class in classes:
            if school_class.id not in sections_by_class:
                continue
                
            sections = sections_by_class[school_class.id]
            
            for section in sections:
                # Get class subjects for this class
                class_subjects_for_class = [
                    cs for cs in class_subjects 
                    if cs.class_name == school_class
                ]
                
                if not class_subjects_for_class:
                    continue
                
                period_number = 1
                for day in days:
                    for period_idx, (start_time, end_time) in enumerate(period_times):
                        period_number = period_idx + 1
                        
                        # Skip creating timetable for break periods
                        if period_idx == 3:  # Break period
                            continue
                        elif period_idx == 7 and school_class.level in ['PRE_PRIMARY', 'PRIMARY']:  # Lunch/early dismissal
                            continue
                        
                        # Get random subject for this period
                        class_subject = random.choice(class_subjects_for_class)
                        
                        # Determine period type
                        if period_idx == 0:
                            period_type = 'ASSEMBLY'
                        elif class_subject.subject.has_practical and random.random() > 0.7:
                            period_type = 'PRACTICAL'
                        else:
                            period_type = 'LECTURE'
                        
                        # Determine room
                        if period_type == 'PRACTICAL':
                            room = f"Lab {random.randint(1, 5)}"
                        else:
                            room = section.room_number
                        
                        try:
                            TimeTable.objects.create(
                                class_name=school_class,
                                section=section,
                                academic_year=academic_year,
                                day=day,
                                period_number=period_number,
                                start_time=start_time,
                                end_time=end_time,
                                subject=class_subject,
                                teacher=class_subject.teacher,
                                room=room,
                                period_type=period_type
                            )
                            timetable_created += 1
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"    Error creating timetable entry: {e}"))
        
        self.stdout.write(f"  Created {timetable_created} timetable entries")

    def create_holidays(self, academic_years, classes, options):
        """Create holiday records"""
        self.stdout.write("Creating holidays...")
        
        holiday_data = [
            {
                'name': 'Republic Day',
                'holiday_type': 'NATIONAL',
                'description': 'Indian Republic Day Celebration',
            },
            {
                'name': 'Independence Day',
                'holiday_type': 'NATIONAL',
                'description': 'Indian Independence Day Celebration',
            },
            {
                'name': 'Diwali Break',
                'holiday_type': 'RELIGIOUS',
                'description': 'Diwali Festival Holidays',
            },
            {
                'name': 'Christmas',
                'holiday_type': 'RELIGIOUS',
                'description': 'Christmas Celebration',
            },
            {
                'name': 'Annual Sports Day',
                'holiday_type': 'EVENT',
                'description': 'School Sports Day',
            },
            {
                'name': 'Mid-term Break',
                'holiday_type': 'SCHOOL',
                'description': 'Mid-term vacation',
            },
            {
                'name': 'Final Examinations',
                'holiday_type': 'EXAM',
                'description': 'Year-end examinations',
            },
        ]
        
        for academic_year in academic_years:
            year = academic_year.start_date.year
            
            holiday_dates = [
                (f"{year}-01-26", f"{year}-01-26"),  # Republic Day
                (f"{year}-08-15", f"{year}-08-15"),  # Independence Day
                (f"{year}-10-20", f"{year}-10-25"),  # Diwali (example dates)
                (f"{year}-12-25", f"{year}-12-25"),  # Christmas
                (f"{year}-02-15", f"{year}-02-15"),  # Sports Day
                (f"{year}-06-01", f"{year}-06-07"),  # Mid-term break
                (f"{year}-03-01", f"{year}-03-15"),  # Final exams
            ]
            
            for i, holiday_info in enumerate(holiday_data):
                start_date_str, end_date_str = holiday_dates[i]
                
                try:
                    holiday = Holiday.objects.create(
                        name=f"{holiday_info['name']} {year}",
                        holiday_type=holiday_info['holiday_type'],
                        start_date=start_date_str,
                        end_date=end_date_str,
                        description=holiday_info['description'],
                        academic_year=academic_year
                    )
                    
                    # Add affected classes
                    if holiday_info['name'] == 'Annual Sports Day':
                        holiday.affected_classes.set(classes[:5])  # Only primary classes
                    elif holiday_info['name'] == 'Final Examinations':
                        holiday.affected_classes.set(classes[5:])  # Classes 6-12
                    else:
                        holiday.affected_classes.set(classes)  # All classes
                    
                    self.stdout.write(f"  Created holiday: {holiday.name}")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  Error creating holiday: {e}"))

    def create_study_materials(self, classes, subjects, class_subjects, options):
        """Create study materials"""
        self.stdout.write("Creating study materials...")
        
        teachers = User.objects.filter(role='teacher') if not options['skip_teachers'] else []
        material_types = ['NOTE', 'PRESENTATION', 'WORKSHEET', 'ASSIGNMENT', 'REFERENCE']
        
        materials_created = 0
        
        for i in range(min(10, len(classes) * 2)):  # Create up to 10 study materials
            school_class = random.choice(classes)
            subject = random.choice(subjects)
            teacher = random.choice(teachers) if teachers else None
            
            # Find corresponding class subject
            class_subject = next(
                (cs for cs in class_subjects 
                 if cs.class_name == school_class and cs.subject == subject),
                None
            )
            
            if not class_subject:
                continue
            
            material_type = random.choice(material_types)
            
            try:
                StudyMaterial.objects.create(
                    title=f"{subject.name} {material_type.lower().capitalize()} for {school_class.name}",
                    material_type=material_type,
                    description=f"This is a {material_type.lower()} for {subject.name} class {school_class.name}.",
                    class_name=school_class,
                    subject=subject,
                    file_size=random.randint(1000, 100000),  # 1KB to 100KB
                    uploaded_by=teacher,
                    is_published=True,
                    publish_date=timezone.now() - timedelta(days=random.randint(1, 30))
                )
                materials_created += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Error creating study material: {e}"))
        
        self.stdout.write(f"  Created {materials_created} study materials")

    def create_syllabus(self, classes, subjects, academic_years, options):
        """Create syllabus for classes"""
        self.stdout.write("Creating syllabus...")
        
        syllabus_created = 0
        
        for academic_year in academic_years:
            for school_class in classes[:3]:  # Create syllabus for first 3 classes only
                # Get subjects for this class level
                if school_class.level in ['PRE_PRIMARY']:
                    subject_codes = ['ENG', 'HIN', 'ART']
                elif school_class.level in ['PRIMARY']:
                    subject_codes = ['MATH', 'SCI', 'ENG', 'HIN', 'SST']
                elif school_class.level in ['MIDDLE']:
                    subject_codes = ['MATH', 'SCI', 'ENG', 'HIN', 'SST', 'COMP']
                elif school_class.level in ['HIGH']:
                    subject_codes = ['MATH', 'PHY', 'CHEM', 'BIO', 'ENG', 'HIN', 'COMP']
                else:
                    subject_codes = ['ENG', 'HIN', 'MATH', 'PHY', 'CHEM', 'BIO', 'ACC', 'BST', 'ECO']
                
                class_subjects = [s for s in subjects if s.code in subject_codes]
                
                for subject in class_subjects[:2]:  # Create syllabus for first 2 subjects
                    topics = []
                    
                    # Generate topics based on subject
                    for unit in range(1, 3):  # Reduced units for performance
                        topics.append({
                            'unit': f"Unit {unit}",
                            'title': f"Introduction to {subject.name} Unit {unit}",
                            'subtopics': [
                                f"Topic {unit}.1: Basics",
                                f"Topic {unit}.2: Advanced Concepts"
                            ],
                            'duration_weeks': random.randint(2, 4)
                        })
                    
                    assessment_pattern = {
                        'theory': 70,
                        'practical': 20 if subject.has_practical else 0,
                        'project': 10 if subject.has_project else 0,
                        'internal_assessment': 20,
                        'total': 100
                    }
                    
                    try:
                        Syllabus.objects.create(
                            class_name=school_class,
                            subject=subject,
                            academic_year=academic_year,
                            topics=topics,
                            recommended_books=f"1. Textbook for {subject.name}\n2. Reference Book for {subject.name}",
                            reference_materials=f"Online resources, educational videos",
                            assessment_pattern=assessment_pattern
                        )
                        syllabus_created += 1
                        self.stdout.write(f"    Created syllabus for {school_class.name} - {subject.name}")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"    Error creating syllabus: {e}"))
        
        self.stdout.write(f"  Created {syllabus_created} syllabus records")

    def create_class_teachers(self, classes, sections_by_class, academic_year, options):
        """Create class teacher assignments"""
        self.stdout.write("Creating class teachers...")
        
        teachers = User.objects.filter(role='teacher')
        
        if not teachers.exists():
            self.stdout.write(self.style.WARNING("  No teachers found. Skipping class teacher creation."))
            return
        
        assignments_created = 0
        
        for school_class in classes:
            if school_class.id not in sections_by_class:
                continue
                
            sections = sections_by_class[school_class.id]
            
            for section in sections:
                # Assign a teacher to this class-section
                teacher = teachers[random.randint(0, len(teachers)-1)]
                
                try:
                    ClassTeacher.objects.create(
                        class_name=school_class,
                        section=section,
                        teacher=teacher,
                        academic_year=academic_year,
                        start_date=academic_year.start_date,
                        is_active=True
                    )
                    assignments_created += 1
                    self.stdout.write(f"    Assigned {teacher} as class teacher for {school_class.name} {section.name}")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"    Error assigning class teacher: {e}"))
        
        self.stdout.write(f"  Created {assignments_created} class teacher assignments")

    def create_attendance_records(self, students_per_class, classes, sections_by_class, options):
        """Create attendance records"""
        self.stdout.write("Creating attendance records...")
        
        # Get or create students
        students = self.get_or_create_students(students_per_class, classes, sections_by_class, options)
        
        if not students:
            self.stdout.write(self.style.WARNING("  No students found. Skipping attendance creation."))
            return
        
        teachers = User.objects.filter(role='teacher') if not options['skip_teachers'] else []
        attendance_statuses = ['PRESENT', 'ABSENT', 'LATE', 'HALF_DAY', 'LEAVE']
        
        attendance_created = 0
        
        # Create attendance for last 3 days (reduced for performance)
        for i in range(3):
            date = timezone.now().date() - timedelta(days=i)
            
            # Skip weekends
            if date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                continue
            
            for student in students[:10]:  # Limit to first 10 students for performance
                # Random attendance status with 85% present rate
                if random.random() < 0.85:
                    status = 'PRESENT'
                else:
                    status = random.choice(['ABSENT', 'LATE', 'HALF_DAY', 'LEAVE'])
                
                teacher = random.choice(teachers) if teachers else None
                
                try:
                    Attendance.objects.create(
                        student=student,
                        date=date,
                        status=status,
                        class_name=student.current_class,
                        section=student.section,
                        session='FULL_DAY',
                        remarks='' if status == 'PRESENT' else f'{status.lower().capitalize()} due to personal reasons',
                        marked_by=teacher
                    )
                    attendance_created += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"    Error creating attendance record: {e}"))
        
        self.stdout.write(f"  Created {attendance_created} attendance records")

    def get_or_create_students(self, students_per_class, classes, sections_by_class, options):
        """Get existing students or create dummy ones"""
        students = Student.objects.all()
        
        if not students.exists():
            self.stdout.write(self.style.WARNING("  No existing students found. Creating dummy students..."))
            students = []
            
            # Create parent users first
            parent_users = []
            for i in range(min(3, len(classes))):  # Create 3 parent users
                try:
                    parent_user = User.objects.create(
                        username=f'parent{i+1}',
                        email=f'parent{i+1}@example.com',
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        role='parent',
                        is_active=True
                    )
                    parent_user.set_password('password123')
                    parent_user.save()
                    parent_users.append(parent_user)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"    Error creating parent user: {e}"))
            
            # Create students
            for school_class in classes[:3]:  # Create students for first 3 classes only
                if school_class.id not in sections_by_class:
                    continue
                    
                sections = sections_by_class[school_class.id]
                
                for section in sections:
                    for i in range(min(students_per_class, 3)):  # Max 3 per section for testing
                        parent = random.choice(parent_users) if parent_users else None
                        
                        try:
                            student = Student.objects.create(
                                admission_number=f'ADM{random.randint(1000, 9999)}',
                                first_name=fake.first_name(),
                                last_name=fake.last_name(),
                                date_of_birth=fake.date_of_birth(minimum_age=5, maximum_age=18),
                                gender=random.choice(['MALE', 'FEMALE']),
                                current_class=school_class,
                                section=section,
                                admission_date=timezone.now().date() - timedelta(days=random.randint(30, 365)),
                                father=parent,
                                mother=parent,
                                address=fake.address(),
                                is_active=True
                            )
                            students.append(student)
                            self.stdout.write(f"    Created student: {student}")
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"    Error creating student: {e}"))
        
        return list(students)

    def create_house_points(self, houses, options):
        """Create house points records"""
        self.stdout.write("Creating house points...")
        
        teachers = User.objects.filter(role='teacher') if not options['skip_teachers'] else []
        activities = [
            'Sports Day - First Place',
            'Annual Day Performance',
            'Science Exhibition',
            'Debate Competition',
            'Art Competition',
            'Cleanliness Drive',
        ]
        
        points_created = 0
        
        for house in houses:
            for i in range(3):  # Create 3 points records per house
                awarded_by = random.choice(teachers) if teachers else None
                
                try:
                    HousePoints.objects.create(
                        house=house,
                        points=random.randint(5, 50),
                        activity=random.choice(activities),
                        description=f"Awarded for excellent performance in {random.choice(activities)}",
                        date_awarded=timezone.now().date() - timedelta(days=random.randint(1, 365)),
                        awarded_by=awarded_by
                    )
                    points_created += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"    Error creating house points: {e}"))
            
            # Update total points
            try:
                total_points = house.points_records.aggregate(models.Sum('points'))['points__sum'] or 0
                house.total_points = total_points
                house.save()
                self.stdout.write(f"  Created points for {house.name} (Total: {total_points} points)")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Error updating house points: {e}"))
        
        self.stdout.write(f"  Created {points_created} house points records")