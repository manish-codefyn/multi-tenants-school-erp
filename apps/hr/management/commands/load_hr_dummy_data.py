import os
import json
from datetime import datetime, date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.hr.models import (
    Department, Designation, Staff, StaffAddress, StaffDocument,
    Attendance, LeaveType, LeaveApplication, LeaveBalance,
    SalaryStructure, Payroll, Promotion, EmploymentHistory,
    TrainingProgram, TrainingParticipation, PerformanceReview,
    Recruitment, JobApplication
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Load dummy data for HR app from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to JSON file containing dummy data',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before loading',
        )

    def handle(self, *args, **options):
        file_path = options.get('file') or 'apps/hr/data/hr_dummy_data.json'
        clear_existing = options.get('clear', False)

        # Get absolute path
        if not os.path.isabs(file_path):
            file_path = os.path.join(settings.BASE_DIR, file_path)

        self.stdout.write(f"Loading dummy data from: {file_path}")

        # Check if file exists
        if not os.path.exists(file_path):
            self.stderr.write(f"File not found: {file_path}")
            self.stdout.write("Creating sample dummy data instead...")
            self.create_sample_data()
            return

        try:
            # Clear existing data if requested
            if clear_existing:
                self.clear_existing_data()

            # Load JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Create departments
            departments = self.create_departments(data.get('departments', []))

            # Create designations
            designations = self.create_designations(data.get('designations', []))

            # Create users first (required for staff)
            users = self.create_users(data.get('users', []))

            # Create staff
            staff_members = self.create_staff(
                data.get('staff', []), 
                users, 
                departments, 
                designations
            )

            # Create staff addresses
            self.create_staff_addresses(data.get('staff_addresses', []), staff_members)

            # Create staff documents
            self.create_staff_documents(data.get('staff_documents', []), staff_members)

            # Create attendance records
            self.create_attendance(data.get('attendance', []), staff_members)

            # Create leave types
            leave_types = self.create_leave_types(data.get('leave_types', []))

            # Create leave applications
            self.create_leave_applications(
                data.get('leave_applications', []), 
                staff_members, 
                leave_types
            )

            # Create leave balances
            self.create_leave_balances(data.get('leave_balances', []), staff_members, leave_types)

            # Create salary structures
            self.create_salary_structures(data.get('salary_structures', []), staff_members)

            # Create payroll records
            self.create_payroll(data.get('payroll', []), staff_members)

            # Create promotions
            self.create_promotions(data.get('promotions', []), staff_members, designations)

            # Create employment history
            self.create_employment_history(data.get('employment_history', []), staff_members)

            # Create training programs
            training_programs = self.create_training_programs(data.get('training_programs', []))

            # Create training participations
            self.create_training_participations(
                data.get('training_participations', []), 
                staff_members, 
                training_programs
            )

            # Create performance reviews
            self.create_performance_reviews(data.get('performance_reviews', []), staff_members)

            # Create recruitments
            recruitments = self.create_recruitments(
                data.get('recruitments', []), 
                departments, 
                designations
            )

            # Create job applications
            self.create_job_applications(data.get('job_applications', []), recruitments)

            self.stdout.write(
                self.style.SUCCESS('Successfully loaded dummy data for HR app!')
            )

        except Exception as e:
            self.stderr.write(f"Error loading dummy data: {str(e)}")
            import traceback
            traceback.print_exc()

    def clear_existing_data(self):
        """Clear all existing HR data"""
        self.stdout.write("Clearing existing HR data...")
        
        # Clear in reverse order to respect foreign key constraints
        JobApplication.objects.all().delete()
        Recruitment.objects.all().delete()
        PerformanceReview.objects.all().delete()
        TrainingParticipation.objects.all().delete()
        TrainingProgram.objects.all().delete()
        EmploymentHistory.objects.all().delete()
        Promotion.objects.all().delete()
        Payroll.objects.all().delete()
        SalaryStructure.objects.all().delete()
        LeaveBalance.objects.all().delete()
        LeaveApplication.objects.all().delete()
        LeaveType.objects.all().delete()
        Attendance.objects.all().delete()
        StaffDocument.objects.all().delete()
        StaffAddress.objects.all().delete()
        Staff.objects.all().delete()
        Designation.objects.all().delete()
        Department.objects.all().delete()
        
        self.stdout.write("Existing HR data cleared.")

    def create_departments(self, departments_data):
        """Create Department objects"""
        departments = {}
        for dept_data in departments_data:
            try:
                # Handle head_of_department separately as it requires a user
                hod_data = dept_data.pop('head_of_department', None)
                hod = None
                if hod_data:
                    hod = User.objects.filter(username=hod_data).first()
                
                department, created = Department.objects.get_or_create(
                    code=dept_data['code'],
                    defaults=dept_data
                )
                if created:
                    if hod:
                        department.head_of_department = hod
                        department.save()
                    departments[dept_data['code']] = department
                    self.stdout.write(f"Created department: {department.name}")
            except Exception as e:
                self.stderr.write(f"Error creating department {dept_data.get('name', 'Unknown')}: {str(e)}")
        return departments

    def create_designations(self, designations_data):
        """Create Designation objects"""
        designations = {}
        for desig_data in designations_data:
            try:
                # Handle reports_to separately
                reports_to_data = desig_data.pop('reports_to', None)
                
                designation, created = Designation.objects.get_or_create(
                    code=desig_data['code'],
                    defaults=desig_data
                )
                
                if created and reports_to_data:
                    reports_to = Designation.objects.filter(code=reports_to_data).first()
                    if reports_to:
                        designation.reports_to = reports_to
                        designation.save()
                
                if created:
                    designations[desig_data['code']] = designation
                    self.stdout.write(f"Created designation: {designation.title}")
            except Exception as e:
                self.stderr.write(f"Error creating designation {desig_data.get('title', 'Unknown')}: {str(e)}")
        return designations

    def create_users(self, users_data):
        """Create User objects"""
        users = {}
        for user_data in users_data:
            try:
                username = user_data['username']
                email = user_data['email']
                
                # Check if user exists
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': user_data.get('first_name', ''),
                        'last_name': user_data.get('last_name', ''),
                        'role': user_data.get('role', 'staff'),
                        'is_active': user_data.get('is_active', True),
                    }
                )
                
                if created:
                    # Set password if provided
                    password = user_data.get('password', 'password123')
                    user.set_password(password)
                    user.save()
                    users[username] = user
                    self.stdout.write(f"Created user: {user.username}")
            except Exception as e:
                self.stderr.write(f"Error creating user {user_data.get('username', 'Unknown')}: {str(e)}")
        return users

    def create_staff(self, staff_data, users, departments, designations):
        """Create Staff objects"""
        staff_members = {}
        for staff_info in staff_data:
            try:
                employee_id = staff_info['employee_id']
                username = staff_info['user']
                
                user = users.get(username)
                if not user:
                    self.stderr.write(f"User {username} not found for staff {employee_id}")
                    continue
                
                # Get department and designation
                dept_code = staff_info.pop('department')
                desig_code = staff_info.pop('designation')
                
                department = departments.get(dept_code)
                designation = designations.get(desig_code)
                
                if not department or not designation:
                    self.stderr.write(f"Department or designation not found for staff {employee_id}")
                    continue
                
                # Convert date strings to date objects
                date_fields = ['date_of_birth', 'joining_date', 'confirmation_date', 
                              'contract_end_date', 'retirement_date']
                for field in date_fields:
                    if field in staff_info and staff_info[field]:
                        staff_info[field] = datetime.strptime(staff_info[field], '%Y-%m-%d').date()
                
                # Handle created_by
                created_by_username = staff_info.pop('created_by', None)
                created_by = None
                if created_by_username:
                    created_by = users.get(created_by_username)
                
                # Create staff
                staff, created = Staff.objects.get_or_create(
                    employee_id=employee_id,
                    defaults={
                        'user': user,
                        'department': department,
                        'designation': designation,
                        'created_by': created_by,
                        **staff_info
                    }
                )
                
                if created:
                    staff_members[employee_id] = staff
                    self.stdout.write(f"Created staff: {staff.employee_id} - {staff.full_name}")
            except Exception as e:
                self.stderr.write(f"Error creating staff {staff_info.get('employee_id', 'Unknown')}: {str(e)}")
        return staff_members

    def create_staff_addresses(self, addresses_data, staff_members):
        """Create StaffAddress objects"""
        for addr_data in addresses_data:
            try:
                employee_id = addr_data['staff']
                staff = staff_members.get(employee_id)
                
                if not staff:
                    self.stderr.write(f"Staff {employee_id} not found for address")
                    continue
                
                StaffAddress.objects.get_or_create(
                    staff=staff,
                    address_type=addr_data['address_type'],
                    defaults={
                        'address_line1': addr_data['address_line1'],
                        'address_line2': addr_data.get('address_line2', ''),
                        'city': addr_data['city'],
                        'state': addr_data['state'],
                        'pincode': addr_data['pincode'],
                        'country': addr_data.get('country', 'India'),
                        'is_current': addr_data.get('is_current', True),
                    }
                )
                self.stdout.write(f"Created address for staff: {staff.employee_id}")
            except Exception as e:
                self.stderr.write(f"Error creating address: {str(e)}")

    def create_staff_documents(self, documents_data, staff_members):
        """Create StaffDocument objects"""
        for doc_data in documents_data:
            try:
                employee_id = doc_data['staff']
                staff = staff_members.get(employee_id)
                
                if not staff:
                    self.stderr.write(f"Staff {employee_id} not found for document")
                    continue
                
                # Convert date strings
                date_fields = ['issue_date', 'expiry_date']
                for field in date_fields:
                    if field in doc_data and doc_data[field]:
                        doc_data[field] = datetime.strptime(doc_data[field], '%Y-%m-%d').date()
                
                # For dummy data, we won't create actual files
                # In production, you'd need to handle file uploads
                doc_data.pop('file', None)  # Remove file path for dummy data
                
                StaffDocument.objects.get_or_create(
                    staff=staff,
                    document_type=doc_data['document_type'],
                    file_name=doc_data.get('file_name', ''),
                    defaults=doc_data
                )
                self.stdout.write(f"Created document for staff: {staff.employee_id}")
            except Exception as e:
                self.stderr.write(f"Error creating document: {str(e)}")

    def create_attendance(self, attendance_data, staff_members):
        """Create Attendance objects"""
        for att_data in attendance_data:
            try:
                employee_id = att_data['staff']
                staff = staff_members.get(employee_id)
                
                if not staff:
                    self.stderr.write(f"Staff {employee_id} not found for attendance")
                    continue
                
                # Convert date
                att_data['date'] = datetime.strptime(att_data['date'], '%Y-%m-%d').date()
                
                # Convert time strings if present
                time_fields = ['check_in', 'check_out']
                for field in time_fields:
                    if field in att_data and att_data[field]:
                        att_data[field] = datetime.strptime(att_data[field], '%H:%M:%S').time()
                
                # Handle marked_by
                marked_by_username = att_data.pop('marked_by', None)
                marked_by = None
                if marked_by_username:
                    marked_by = User.objects.filter(username=marked_by_username).first()
                
                Attendance.objects.get_or_create(
                    staff=staff,
                    date=att_data['date'],
                    defaults={
                        'marked_by': marked_by,
                        **att_data
                    }
                )
            except Exception as e:
                self.stderr.write(f"Error creating attendance: {str(e)}")

    def create_leave_types(self, leave_types_data):
        """Create LeaveType objects"""
        leave_types = {}
        for lt_data in leave_types_data:
            try:
                code = lt_data['code']
                
                # Handle approval_authority
                approval_auth_code = lt_data.pop('approval_authority', None)
                approval_auth = None
                if approval_auth_code:
                    approval_auth = Designation.objects.filter(code=approval_auth_code).first()
                
                leave_type, created = LeaveType.objects.get_or_create(
                    code=code,
                    defaults=lt_data
                )
                
                if created and approval_auth:
                    leave_type.approval_authority = approval_auth
                    leave_type.save()
                
                if created:
                    leave_types[code] = leave_type
                    self.stdout.write(f"Created leave type: {leave_type.name}")
            except Exception as e:
                self.stderr.write(f"Error creating leave type: {str(e)}")
        return leave_types

    def create_leave_applications(self, applications_data, staff_members, leave_types):
        """Create LeaveApplication objects"""
        for app_data in applications_data:
            try:
                employee_id = app_data['staff']
                leave_type_code = app_data['leave_type']
                
                staff = staff_members.get(employee_id)
                leave_type = leave_types.get(leave_type_code)
                
                if not staff or not leave_type:
                    self.stderr.write(f"Staff or leave type not found for leave application")
                    continue
                
                # Convert dates
                app_data['start_date'] = datetime.strptime(app_data['start_date'], '%Y-%m-%d').date()
                app_data['end_date'] = datetime.strptime(app_data['end_date'], '%Y-%m-%d').date()
                
                # Handle work_handover_to
                handover_to_id = app_data.pop('work_handover_to', None)
                handover_to = None
                if handover_to_id:
                    handover_to = staff_members.get(handover_to_id)
                
                # Handle approved_by
                approved_by_username = app_data.pop('approved_by', None)
                approved_by = None
                if approved_by_username:
                    approved_by = User.objects.filter(username=approved_by_username).first()
                
                # Calculate total days
                total_days = (app_data['end_date'] - app_data['start_date']).days + 1
                
                LeaveApplication.objects.get_or_create(
                    staff=staff,
                    leave_type=leave_type,
                    start_date=app_data['start_date'],
                    end_date=app_data['end_date'],
                    defaults={
                        'work_handover_to': handover_to,
                        'approved_by': approved_by,
                        'total_days': total_days,
                        **app_data
                    }
                )
                self.stdout.write(f"Created leave application for staff: {staff.employee_id}")
            except Exception as e:
                self.stderr.write(f"Error creating leave application: {str(e)}")

    def create_leave_balances(self, balances_data, staff_members, leave_types):
        """Create LeaveBalance objects"""
        for balance_data in balances_data:
            try:
                employee_id = balance_data['staff']
                leave_type_code = balance_data['leave_type']
                
                staff = staff_members.get(employee_id)
                leave_type = leave_types.get(leave_type_code)
                
                if not staff or not leave_type:
                    self.stderr.write(f"Staff or leave type not found for leave balance")
                    continue
                
                LeaveBalance.objects.get_or_create(
                    staff=staff,
                    leave_type=leave_type,
                    year=balance_data['year'],
                    defaults=balance_data
                )
            except Exception as e:
                self.stderr.write(f"Error creating leave balance: {str(e)}")

    def create_salary_structures(self, structures_data, staff_members):
        """Create SalaryStructure objects"""
        for struct_data in structures_data:
            try:
                employee_id = struct_data['staff']
                staff = staff_members.get(employee_id)
                
                if not staff:
                    self.stderr.write(f"Staff {employee_id} not found for salary structure")
                    continue
                
                # Convert date
                struct_data['effective_from'] = datetime.strptime(
                    struct_data['effective_from'], '%Y-%m-%d'
                ).date()
                
                if struct_data.get('effective_to'):
                    struct_data['effective_to'] = datetime.strptime(
                        struct_data['effective_to'], '%Y-%m-%d'
                    ).date()
                
                SalaryStructure.objects.get_or_create(
                    staff=staff,
                    effective_from=struct_data['effective_from'],
                    defaults=struct_data
                )
                self.stdout.write(f"Created salary structure for staff: {staff.employee_id}")
            except Exception as e:
                self.stderr.write(f"Error creating salary structure: {str(e)}")

    def create_payroll(self, payroll_data, staff_members):
        """Create Payroll objects"""
        for payroll_info in payroll_data:
            try:
                employee_id = payroll_info['staff']
                staff = staff_members.get(employee_id)
                
                if not staff:
                    self.stderr.write(f"Staff {employee_id} not found for payroll")
                    continue
                
                # Convert dates
                payroll_info['salary_month'] = datetime.strptime(
                    payroll_info['salary_month'], '%Y-%m-%d'
                ).date()
                payroll_info['pay_date'] = datetime.strptime(
                    payroll_info['pay_date'], '%Y-%m-%d'
                ).date()
                
                # Handle processed_by and approved_by
                processed_by_username = payroll_info.pop('processed_by', None)
                approved_by_username = payroll_info.pop('approved_by', None)
                
                processed_by = None
                approved_by = None
                
                if processed_by_username:
                    processed_by = User.objects.filter(username=processed_by_username).first()
                if approved_by_username:
                    approved_by = User.objects.filter(username=approved_by_username).first()
                
                Payroll.objects.get_or_create(
                    staff=staff,
                    salary_month=payroll_info['salary_month'],
                    defaults={
                        'processed_by': processed_by,
                        'approved_by': approved_by,
                        **payroll_info
                    }
                )
                self.stdout.write(f"Created payroll for staff: {staff.employee_id}")
            except Exception as e:
                self.stderr.write(f"Error creating payroll: {str(e)}")

    def create_promotions(self, promotions_data, staff_members, designations):
        """Create Promotion objects"""
        for promo_data in promotions_data:
            try:
                employee_id = promo_data['staff']
                prev_desig_code = promo_data['previous_designation']
                new_desig_code = promo_data['new_designation']
                
                staff = staff_members.get(employee_id)
                prev_designation = designations.get(prev_desig_code)
                new_designation = designations.get(new_desig_code)
                
                if not staff or not prev_designation or not new_designation:
                    self.stderr.write(f"Staff or designation not found for promotion")
                    continue
                
                # Convert date
                promo_data['effective_date'] = datetime.strptime(
                    promo_data['effective_date'], '%Y-%m-%d'
                ).date()
                
                # Handle approved_by
                approved_by_username = promo_data.pop('approved_by', None)
                approved_by = None
                if approved_by_username:
                    approved_by = User.objects.filter(username=approved_by_username).first()
                
                Promotion.objects.get_or_create(
                    staff=staff,
                    effective_date=promo_data['effective_date'],
                    defaults={
                        'previous_designation': prev_designation,
                        'new_designation': new_designation,
                        'approved_by': approved_by,
                        **promo_data
                    }
                )
                self.stdout.write(f"Created promotion for staff: {staff.employee_id}")
            except Exception as e:
                self.stderr.write(f"Error creating promotion: {str(e)}")

    def create_employment_history(self, history_data, staff_members):
        """Create EmploymentHistory objects"""
        for hist_data in history_data:
            try:
                employee_id = hist_data['staff']
                staff = staff_members.get(employee_id)
                
                if not staff:
                    self.stderr.write(f"Staff {employee_id} not found for employment history")
                    continue
                
                # Convert date
                hist_data['effective_date'] = datetime.strptime(
                    hist_data['effective_date'], '%Y-%m-%d'
                ).date()
                
                # Handle initiated_by and approved_by
                initiated_by_username = hist_data.pop('initiated_by', None)
                approved_by_username = hist_data.pop('approved_by', None)
                
                initiated_by = None
                approved_by = None
                
                if initiated_by_username:
                    initiated_by = User.objects.filter(username=initiated_by_username).first()
                if approved_by_username:
                    approved_by = User.objects.filter(username=approved_by_username).first()
                
                EmploymentHistory.objects.get_or_create(
                    staff=staff,
                    action=hist_data['action'],
                    effective_date=hist_data['effective_date'],
                    defaults={
                        'initiated_by': initiated_by,
                        'approved_by': approved_by,
                        **hist_data
                    }
                )
            except Exception as e:
                self.stderr.write(f"Error creating employment history: {str(e)}")

    def create_training_programs(self, training_data):
        """Create TrainingProgram objects"""
        programs = {}
        for prog_data in training_data:
            try:
                code = prog_data.get('code') or prog_data['title'].replace(' ', '_').upper()
                
                # Convert dates
                prog_data['start_date'] = datetime.strptime(
                    prog_data['start_date'], '%Y-%m-%d'
                ).date()
                prog_data['end_date'] = datetime.strptime(
                    prog_data['end_date'], '%Y-%m-%d'
                ).date()
                
                # Create program
                program, created = TrainingProgram.objects.get_or_create(
                    title=prog_data['title'],
                    start_date=prog_data['start_date'],
                    defaults=prog_data
                )
                
                if created:
                    programs[code] = program
                    self.stdout.write(f"Created training program: {program.title}")
            except Exception as e:
                self.stderr.write(f"Error creating training program: {str(e)}")
        return programs

    def create_training_participations(self, participations_data, staff_members, training_programs):
        """Create TrainingParticipation objects"""
        for part_data in participations_data:
            try:
                employee_id = part_data['staff']
                training_code = part_data['training']
                
                staff = staff_members.get(employee_id)
                training = training_programs.get(training_code)
                
                if not staff or not training:
                    self.stderr.write(f"Staff or training program not found for participation")
                    continue
                
                # Convert date if present
                if part_data.get('certificate_issue_date'):
                    part_data['certificate_issue_date'] = datetime.strptime(
                        part_data['certificate_issue_date'], '%Y-%m-%d'
                    ).date()
                
                TrainingParticipation.objects.get_or_create(
                    training=training,
                    staff=staff,
                    defaults=part_data
                )
                self.stdout.write(f"Created training participation for staff: {staff.employee_id}")
            except Exception as e:
                self.stderr.write(f"Error creating training participation: {str(e)}")

    def create_performance_reviews(self, reviews_data, staff_members):
        """Create PerformanceReview objects"""
        for review_data in reviews_data:
            try:
                employee_id = review_data['staff']
                staff = staff_members.get(employee_id)
                
                if not staff:
                    self.stderr.write(f"Staff {employee_id} not found for performance review")
                    continue
                
                # Convert dates
                review_data['review_period_start'] = datetime.strptime(
                    review_data['review_period_start'], '%Y-%m-%d'
                ).date()
                review_data['review_period_end'] = datetime.strptime(
                    review_data['review_period_end'], '%Y-%m-%d'
                ).date()
                review_data['review_date'] = datetime.strptime(
                    review_data['review_date'], '%Y-%m-%d'
                ).date()
                
                # Handle reviewed_by and approved_by
                reviewed_by_username = review_data.pop('reviewed_by', None)
                approved_by_username = review_data.pop('approved_by', None)
                
                reviewed_by = None
                approved_by = None
                
                if reviewed_by_username:
                    reviewed_by = User.objects.filter(username=reviewed_by_username).first()
                if approved_by_username:
                    approved_by = User.objects.filter(username=approved_by_username).first()
                
                PerformanceReview.objects.get_or_create(
                    staff=staff,
                    review_type=review_data['review_type'],
                    review_period_start=review_data['review_period_start'],
                    review_period_end=review_data['review_period_end'],
                    defaults={
                        'reviewed_by': reviewed_by,
                        'approved_by': approved_by,
                        **review_data
                    }
                )
                self.stdout.write(f"Created performance review for staff: {staff.employee_id}")
            except Exception as e:
                self.stderr.write(f"Error creating performance review: {str(e)}")

    def create_recruitments(self, recruitments_data, departments, designations):
        """Create Recruitment objects"""
        recruitments = {}
        for rec_data in recruitments_data:
            try:
                dept_code = rec_data['department']
                desig_code = rec_data['designation']
                
                department = departments.get(dept_code)
                designation = designations.get(desig_code)
                
                if not department or not designation:
                    self.stderr.write(f"Department or designation not found for recruitment")
                    continue
                
                # Convert dates
                rec_data['posting_date'] = datetime.strptime(
                    rec_data['posting_date'], '%Y-%m-%d'
                ).date()
                rec_data['closing_date'] = datetime.strptime(
                    rec_data['closing_date'], '%Y-%m-%d'
                ).date()
                
                if rec_data.get('expected_joining_date'):
                    rec_data['expected_joining_date'] = datetime.strptime(
                        rec_data['expected_joining_date'], '%Y-%m-%d'
                    ).date()
                
                # Handle hiring_manager
                hiring_manager_username = rec_data.pop('hiring_manager', None)
                hiring_manager = None
                if hiring_manager_username:
                    hiring_manager = User.objects.filter(username=hiring_manager_username).first()
                
                # Create a unique code for recruitment
                rec_code = f"REC-{dept_code}-{desig_code}-{rec_data['posting_date'].strftime('%Y%m%d')}"
                
                recruitment, created = Recruitment.objects.get_or_create(
                    position_title=rec_data['position_title'],
                    department=department,
                    designation=designation,
                    defaults={
                        'hiring_manager': hiring_manager,
                        **rec_data
                    }
                )
                
                if created:
                    recruitments[rec_code] = recruitment
                    self.stdout.write(f"Created recruitment: {recruitment.position_title}")
            except Exception as e:
                self.stderr.write(f"Error creating recruitment: {str(e)}")
        return recruitments

    def create_job_applications(self, applications_data, recruitments):
        """Create JobApplication objects"""
        for app_data in applications_data:
            try:
                rec_code = app_data['recruitment']
                recruitment = recruitments.get(rec_code)
                
                if not recruitment:
                    self.stderr.write(f"Recruitment {rec_code} not found for job application")
                    continue
                
                # Convert date
                app_data['applied_date'] = datetime.strptime(
                    app_data['applied_date'], '%Y-%m-%d %H:%M:%S'
                )
                
                # For dummy data, we won't create actual resume files
                app_data.pop('resume', None)  # Remove resume path for dummy data
                
                JobApplication.objects.get_or_create(
                    recruitment=recruitment,
                    applicant_name=app_data['applicant_name'],
                    email=app_data['email'],
                    defaults=app_data
                )
                self.stdout.write(f"Created job application: {app_data['applicant_name']}")
            except Exception as e:
                self.stderr.write(f"Error creating job application: {str(e)}")

    def create_sample_data(self):
        """Create sample data if JSON file is not found"""
        self.stdout.write("Creating sample data...")
        
        # Create admin user if not exists
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@school.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
        
        # Create departments
        departments = {
            'SCIENCE': Department.objects.create(
                name='Science Department',
                code='SCIENCE',
                description='Department of Science',
                email='science@school.com',
                phone='+919876543210'
            ),
            'MATHEMATICS': Department.objects.create(
                name='Mathematics Department',
                code='MATH',
                description='Department of Mathematics',
                email='math@school.com',
                phone='+919876543211'
            ),
        }
        
        # Create designations
        designations = {
            'PRINCIPAL': Designation.objects.create(
                title='Principal',
                code='PRINCIPAL',
                category='ADMINISTRATIVE',
                description='Head of the school',
                grade='A1',
                min_salary=100000,
                max_salary=200000,
                experience_required=15
            ),
            'HOD_SCIENCE': Designation.objects.create(
                title='Head of Department - Science',
                code='HOD_SCIENCE',
                category='TEACHING',
                description='Head of Science Department',
                grade='B1',
                min_salary=60000,
                max_salary=120000,
                experience_required=10,
                reports_to=Designation.objects.get(code='PRINCIPAL')
            ),
            'TEACHER': Designation.objects.create(
                title='Teacher',
                code='TEACHER',
                category='TEACHING',
                description='Teaching staff',
                grade='C1',
                min_salary=30000,
                max_salary=60000,
                experience_required=3
            ),
        }
        
        # Create teacher user
        teacher_user, created = User.objects.get_or_create(
            username='john_doe',
            defaults={
                'email': 'john.doe@school.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'teacher',
                'is_active': True,
            }
        )
        if created:
            teacher_user.set_password('password123')
            teacher_user.save()
        
        # Create staff
        staff = Staff.objects.create(
            user=teacher_user,
            employee_id='EMP001',
            date_of_birth=date(1985, 5, 15),
            gender='M',
            blood_group='O+',
            marital_status='MARRIED',
            nationality='Indian',
            personal_email='john.doe.personal@email.com',
            personal_phone='+919876543212',
            emergency_contact_name='Jane Doe',
            emergency_contact_relation='Wife',
            emergency_contact_phone='+919876543213',
            department=departments['SCIENCE'],
            designation=designations['TEACHER'],
            employment_type='PERMANENT',
            employment_status='ACTIVE',
            joining_date=date(2015, 6, 1),
            confirmation_date=date(2015, 12, 1),
            qualifications=[{
                'degree': 'M.Sc. Physics',
                'university': 'University of Delhi',
                'year': 2007
            }],
            specialization='Physics',
            teaching_experience=10,
            total_experience=15,
            basic_salary=45000,
            bank_account_number='123456789012',
            bank_name='State Bank of India',
            ifsc_code='SBIN0001234',
            pan_number='ABCDE1234F',
            aadhaar_number='123456789012',
            work_location='Main Campus',
            work_phone='+911234567890',
            work_email='john.doe@school.com',
            created_by=admin_user
        )
        
        # Create staff address
        StaffAddress.objects.create(
            staff=staff,
            address_type='PERMANENT',
            address_line1='123 Main Street',
            city='Delhi',
            state='Delhi',
            pincode='110001',
            country='India',
            is_current=True
        )
        
        # Create attendance for current month
        today = date.today()
        for i in range(1, 21):  # Create 20 attendance records
            att_date = date(today.year, today.month, i)
            if att_date.weekday() < 5:  # Monday to Friday
                Attendance.objects.create(
                    staff=staff,
                    date=att_date,
                    status='PRESENT',
                    check_in=datetime.strptime('09:00:00', '%H:%M:%S').time(),
                    check_out=datetime.strptime('17:00:00', '%H:%M:%S').time(),
                    total_hours=8.0,
                    marked_by=admin_user
                )
        
        self.stdout.write(self.style.SUCCESS('Created sample data successfully!'))