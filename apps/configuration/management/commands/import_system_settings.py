import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from django.db import connection
from apps.configuration.models import SystemSetting
from apps.core.utils.tenant import get_current_tenant

# Try to import your tenant model
try:
    from apps.tenants.models import Tenant
    HAS_TENANT_MODEL = True
except ImportError:
    HAS_TENANT_MODEL = False


class Command(BaseCommand):
    """
    Django management command to import initial system settings from JSON data.
    """
    
    help = 'Import initial system settings from JSON data file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='apps/configurations/data/system_settings.json',
            help='Path to JSON file containing system settings'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate import without actually saving to database'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing system settings before import'
        )
        parser.add_argument(
            '--skip-validation',
            action='store_true',
            dest='skip_validation',
            help='Skip validation during import (use with caution)'
        )
        parser.add_argument(
            '--tenant',
            type=str,
            help='Tenant ID or domain to associate settings with'
        )
        parser.add_argument(
            '--skip-tenant-check',
            action='store_true',
            dest='skip_tenant_check',
            help='Skip tenant requirement (for system-wide settings)'
        )
    
    def handle(self, *args, **options):
        # Get file path
        file_path = options['file']
        dry_run = options['dry_run']
        clear_existing = options['clear']
        skip_validation = options['skip_validation']
        tenant_identifier = options['tenant']
        skip_tenant_check = options['skip_tenant_check']
        
        self.stdout.write(self.style.HTTP_INFO(f"Starting system settings import from: {file_path}"))
        
        # Check if file exists
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            # Try alternative paths
            alternative_paths = [
                'apps/configuration/data/system_settings.json',
                'data/system_settings.json',
                './system_settings.json'
            ]
            
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    file_path = alt_path
                    self.stdout.write(self.style.WARNING(f"Using alternative path: {file_path}"))
                    break
            else:
                self.stdout.write(self.style.WARNING(f"Looking for file in: {os.path.abspath('.')}"))
                return
        
        # Handle tenant context
        tenant = None
        if tenant_identifier and HAS_TENANT_MODEL:
            try:
                # Try to get tenant by ID or domain
                if tenant_identifier.isdigit():
                    tenant = Tenant.objects.get(id=int(tenant_identifier))
                else:
                    tenant = Tenant.objects.get(domain=tenant_identifier)
                self.stdout.write(self.style.SUCCESS(f"Using tenant: {tenant.name} ({tenant.domain})"))
            except Tenant.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Tenant not found: {tenant_identifier}"))
                # Create a default tenant if needed
                if self.stdout.isatty():
                    create = input("Create default tenant? (y/n): ")
                    if create.lower() == 'y':
                        tenant = self.create_default_tenant()
        
        # Load JSON data
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"Invalid JSON file: {str(e)}"))
            return
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error reading file: {str(e)}"))
            return
        
        if not isinstance(data, list):
            self.stderr.write(self.style.ERROR("JSON data should be a list of settings"))
            return
        
        # Clear existing settings if requested
        if clear_existing:
            if not dry_run:
                if tenant:
                    count, _ = SystemSetting.objects.filter(tenant=tenant).delete()
                else:
                    count, _ = SystemSetting.objects.all().delete()
                self.stdout.write(self.style.WARNING(f"Cleared {count} existing system settings"))
            else:
                self.stdout.write(self.style.WARNING("Would clear existing system settings (dry run)"))
        
        # Process each setting
        imported_count = 0
        updated_count = 0
        error_count = 0
        
        with transaction.atomic():
            # Create a savepoint for dry-run rollback
            sid = transaction.savepoint() if dry_run else None
            
            for index, setting_data in enumerate(data, 1):
                try:
                    key = setting_data.get('key')
                    if not key:
                        self.stderr.write(self.style.WARNING(f"Setting at index {index} has no key, skipping"))
                        error_count += 1
                        continue
                    
                    self.stdout.write(f"Processing: {key} ({index}/{len(data)})")
                    
                    # Check if setting already exists
                    if tenant:
                        existing_setting = SystemSetting.objects.filter(key=key, tenant=tenant).first()
                    else:
                        existing_setting = SystemSetting.objects.filter(key=key, tenant__isnull=True).first()
                    
                    # Prepare setting data
                    setting_dict = {
                        'key': key,
                        'name': setting_data.get('name', key.replace('.', ' ').replace('_', ' ').title()),
                        'description': setting_data.get('description', ''),
                        'category': setting_data.get('category', 'GENERAL'),
                        'group': setting_data.get('group', ''),
                        'setting_type': setting_data.get('setting_type', 'STRING'),
                        'is_encrypted': setting_data.get('is_encrypted', False),
                        'is_public': setting_data.get('is_public', False),
                        'is_required': setting_data.get('is_required', False),
                        'is_readonly': setting_data.get('is_readonly', False),
                        'validation_regex': setting_data.get('validation_regex', ''),
                        'validation_message': setting_data.get('validation_message', ''),
                        'min_value': setting_data.get('min_value'),
                        'max_value': setting_data.get('max_value'),
                        'choices': setting_data.get('choices', []),
                        'order': setting_data.get('order', 0),
                        'version': setting_data.get('version', 1),
                    }
                    
                    # Add tenant if available
                    if tenant:
                        setting_dict['tenant'] = tenant
                    
                    # Handle value based on setting type
                    setting_type = setting_dict['setting_type']
                    value = setting_data.get('value')
                    
                    # Clear all value fields first
                    # Note: CharField and TextField should be empty string, not None
                    setting_dict['value_string'] = ""
                    setting_dict['value_text'] = ""
                    
                    nullable_fields = [
                        'value_integer', 'value_decimal', 'value_boolean', 
                        'value_json', 'value_datetime', 'value_date', 'value_time'
                    ]
                    for field in nullable_fields:
                        setting_dict[field] = None
                    
                    # Set the appropriate value field
                    if value is not None:
                        if setting_type == 'STRING':
                            setting_dict['value_string'] = str(value)
                        elif setting_type == 'TEXT':
                            setting_dict['value_text'] = str(value)
                        elif setting_type == 'INTEGER':
                            setting_dict['value_integer'] = int(value) if value is not None else None
                        elif setting_type == 'DECIMAL':
                            from decimal import Decimal
                            setting_dict['value_decimal'] = Decimal(str(value)) if value is not None else None
                        elif setting_type == 'BOOLEAN':
                            setting_dict['value_boolean'] = bool(value)
                        elif setting_type == 'JSON':
                            setting_dict['value_json'] = value
                        elif setting_type == 'DATETIME':
                            if isinstance(value, str):
                                from django.utils.dateparse import parse_datetime
                                parsed = parse_datetime(value)
                                setting_dict['value_datetime'] = parsed if parsed else None
                            else:
                                setting_dict['value_datetime'] = value
                        elif setting_type == 'DATE':
                            if isinstance(value, str):
                                from django.utils.dateparse import parse_date
                                parsed = parse_date(value)
                                setting_dict['value_date'] = parsed if parsed else None
                            else:
                                setting_dict['value_date'] = value
                        elif setting_type == 'TIME':
                            if isinstance(value, str):
                                from django.utils.dateparse import parse_time
                                parsed = parse_time(value)
                                setting_dict['value_time'] = parsed if parsed else None
                            else:
                                setting_dict['value_time'] = value
                        elif setting_type == 'CHOICE':
                            setting_dict['value_string'] = str(value)
                        elif setting_type == 'MULTI_CHOICE':
                            setting_dict['value_json'] = value
                    
                    # Handle depends_on reference
                    depends_on_key = setting_data.get('depends_on')
                    if depends_on_key:
                        try:
                            if tenant:
                                depends_on_setting = SystemSetting.objects.get(key=depends_on_key, tenant=tenant)
                            else:
                                depends_on_setting = SystemSetting.objects.get(key=depends_on_key, tenant__isnull=True)
                            setting_dict['depends_on'] = depends_on_setting
                        except SystemSetting.DoesNotExist:
                            self.stdout.write(self.style.WARNING(
                                f"Warning: depends_on setting '{depends_on_key}' not found for '{key}'"
                            ))
                    
                    if existing_setting:
                        # Update existing setting
                        if not dry_run:
                            for field, val in setting_dict.items():
                                if field != 'depends_on' or val is not None:
                                    setattr(existing_setting, field, val)
                            
                            # Bypass tenant check if needed
                            if skip_tenant_check or not tenant:
                                existing_setting.is_superuser = True

                            # Save with or without validation
                            if skip_validation:
                                # Skip full_clean
                                existing_setting.save()
                            else:
                                try:
                                    existing_setting.full_clean()
                                    existing_setting.save()
                                except Exception as e:
                                    self.stderr.write(self.style.ERROR(f"Validation error for {key}: {e}"))
                                    raise
                        
                        action = "Updated" if not dry_run else "Would update"
                        self.stdout.write(self.style.SUCCESS(f"  {action}: {key}"))
                        updated_count += 1
                    else:
                        # Create new setting
                        if not dry_run:
                            # Patch to skip tenant validation if needed
                            if skip_tenant_check and 'tenant' not in setting_dict:
                                # Create setting without tenant
                                setting = SystemSetting(**setting_dict)
                                # Manually set tenant to None to avoid validation error
                                setting.tenant = None
                                setting.is_superuser = True # Bypass tenant check in BaseModel
                            else:
                                setting = SystemSetting(**setting_dict)
                                if skip_tenant_check:
                                    setting.is_superuser = True
                            
                            # Save with or without validation
                            if skip_validation:
                                setting.save()
                            else:
                                try:
                                    setting.full_clean()
                                    setting.save()
                                except Exception as e:
                                    self.stderr.write(self.style.ERROR(f"Validation error for {key}: {e}"))
                                    raise
                        
                        action = "Created" if not dry_run else "Would create"
                        self.stdout.write(self.style.SUCCESS(f"  {action}: {key}"))
                        imported_count += 1
                    
                except Exception as e:
                    key_display = key if 'key' in locals() else f'setting at index {index}'
                    self.stderr.write(self.style.ERROR(f"Error processing {key_display}: {str(e)}"))
                    error_count += 1
                    if not dry_run:
                        import traceback
                        traceback_str = traceback.format_exc()
                        # Show only first 200 chars of traceback
                        if len(traceback_str) > 200:
                            traceback_str = traceback_str[:200] + "..."
                        self.stderr.write(self.style.ERROR(f"Traceback: {traceback_str}"))
            
            # Rollback if dry-run
            if dry_run and sid:
                transaction.savepoint_rollback(sid)
                self.stdout.write(self.style.WARNING("DRY RUN: Changes rolled back"))
        
        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("IMPORT SUMMARY"))
        self.stdout.write("="*60)
        self.stdout.write(f"Total in file: {len(data)}")
        self.stdout.write(f"Newly imported: {imported_count}")
        self.stdout.write(f"Updated: {updated_count}")
        self.stdout.write(f"Errors: {error_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nThis was a DRY RUN. No changes were made to the database."))
        else:
            self.stdout.write(self.style.SUCCESS("\nImport completed successfully!"))
    
    def create_default_tenant(self):
        """Create a default tenant if none exists"""
        try:
            from apps.tenants.models import Tenant
            tenant, created = Tenant.objects.get_or_create(
                domain='default.localhost',
                defaults={
                    'name': 'Default Tenant',
                    'schema_name': 'public',
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created default tenant: {tenant.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Using existing default tenant: {tenant.name}"))
            return tenant
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to create default tenant: {e}"))
            return None