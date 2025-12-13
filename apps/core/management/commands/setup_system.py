# apps/core/management/commands/setup_system.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
import sys

class Command(BaseCommand):
    help = 'Complete system setup with proper order'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-migrations',
            action='store_true',
            help='Skip applying migrations',
        )
        parser.add_argument(
            '--skip-superuser',
            action='store_true',
            help='Skip superuser creation',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force setup even if errors occur',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('SYSTEM SETUP INITIATED'.center(60))
        self.stdout.write('=' * 60 + '\n')
        
        steps_completed = 0
        total_steps = 4
        
        # Step 1: Apply Migrations
        if not options['skip_migrations']:
            steps_completed += self._run_step(
                step_number=1,
                total_steps=total_steps,
                title="Applying Database Migrations",
                function=self._apply_migrations,
                options=options
            )
        else:
            self.stdout.write(f'[SKIP] Step 1/{total_steps}: Migrations skipped by user')
            steps_completed += 1
        
        # Step 2: Create Superuser
        if not options['skip_superuser']:
            steps_completed += self._run_step(
                step_number=2,
                total_steps=total_steps,
                title="Creating Superuser",
                function=self._create_superuser,
                options=options
            )
        else:
            self.stdout.write(f'[SKIP] Step 2/{total_steps}: Superuser creation skipped by user')
            steps_completed += 1
        
        # Step 3: Initialize Permissions
        steps_completed += self._run_step(
            step_number=3,
            total_steps=total_steps,
            title="Initializing Permissions",
            function=self._init_permissions,
            options=options
        )
        
        # Step 4: Setup Role Permissions
        steps_completed += self._run_step(
            step_number=4,
            total_steps=total_steps,
            title="Setting Up Role Permissions",
            function=self._setup_role_permissions,
            options=options
        )
        
        # Summary
        self._print_summary(steps_completed, total_steps, options)
    
    def _run_step(self, step_number, total_steps, title, function, options):
        """Execute a setup step with proper formatting and error handling"""
        self.stdout.write(f'\n{"─" * 60}')
        self.stdout.write(f'STEP {step_number}/{total_steps}: {title}')
        self.stdout.write(f'{"─" * 60}')
        
        try:
            success = function(options)
            if success:
                self.stdout.write(self.style.SUCCESS(f'  ✅ {title} completed successfully'))
                return 1
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠ {title} completed with warnings'))
                return 0 if not options['force'] else 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error in {title}: {str(e)}'))
            if not options['force']:
                self.stdout.write(self.style.ERROR('  Setup aborted!'))
                sys.exit(1)
            return 0
    
    def _apply_migrations(self, options):
        """Apply database migrations"""
        try:
            self.stdout.write('  Applying migrations...')
            call_command('migrate', verbosity=1)
            self.stdout.write('  ✓ All migrations applied')
            return True
        except Exception as e:
            self.stdout.write(f'  ✗ Migration error: {e}')
            if options.get('force'):
                self.stdout.write('  ⚠ Continuing due to --force flag')
                return False
            raise
    
    def _create_superuser(self, options):
        """Create superuser if not exists"""
        User = get_user_model()
        
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write('  ✓ Superuser already exists')
            return True
        
        self.stdout.write('  No superuser found.')
        
        # Try to create with default values first
        try:
            # You can customize these defaults
            default_email = 'admin@erpsystem.com'
            default_password = 'admin123'
            
            if not User.objects.filter(email=default_email).exists():
                User.objects.create_superuser(
                    email=default_email,
                    password=default_password,
                    first_name='System',
                    last_name='Administrator'
                )
                self.stdout.write(f'  ✓ Created default superuser: {default_email}')
                self.stdout.write(f'  ⚠ Default password: {default_password}')
                self.stdout.write('  ⚠ Please change the password immediately!')
                return True
        except Exception as e:
            self.stdout.write(f'  ✗ Could not create default superuser: {e}')
        
        # Interactive creation
        self.stdout.write('  Starting interactive superuser creation...')
        try:
            call_command('createsuperuser', interactive=True)
            self.stdout.write('  ✓ Superuser created interactively')
            return True
        except Exception as e:
            self.stdout.write(f'  ✗ Interactive creation failed: {e}')
            if options.get('force'):
                self.stdout.write('  ⚠ Continuing without superuser (--force flag)')
                return False
            raise
    
    def _init_permissions(self, options):
        """Initialize system permissions"""
        try:
            # Try different possible command names
            permission_commands = ['init_permissions', 'setup_permissions', 'simple_setup']
            
            for cmd in permission_commands:
                try:
                    self.stdout.write(f'  Trying command: {cmd}...')
                    call_command(cmd)
                    self.stdout.write(f'  ✓ Permissions initialized with {cmd}')
                    return True
                except Exception as e:
                    self.stdout.write(f'  ✗ Command {cmd} failed: {e}')
                    continue
            
            # If no permission command works, create basic permissions
            self.stdout.write('  Creating basic permissions manually...')
            self._create_basic_permissions()
            self.stdout.write('  ✓ Basic permissions created')
            return True
            
        except Exception as e:
            self.stdout.write(f'  ✗ Permission initialization failed: {e}')
            if options.get('force'):
                self.stdout.write('  ⚠ Continuing without permissions (--force flag)')
                return False
            raise
    
    def _setup_role_permissions(self, options):
        """Setup role-based permissions"""
        try:
            # Check if RolePermission model exists
            from django.apps import apps
            
            if apps.is_installed('apps_auth'):
                try:
                    from apps.auth.models import RolePermission
                    
                    # Create default permissions
                    self.stdout.write('  Creating default role permissions...')
                    created = RolePermission.create_default_permissions()
                    self.stdout.write(f'  ✓ Created {created} role permissions')
                    
                    # Create role groups
                    self.stdout.write('  Creating role groups...')
                    from django.contrib.auth.models import Group
                    from apps.users.models import ROLE_CHOICES
                    
                    for role_value, role_name in ROLE_CHOICES:
                        group, created = Group.objects.get_or_create(name=role_name)
                        if created:
                            self.stdout.write(f'    ✓ Created group: {role_name}')
                    
                    self.stdout.write('  ✓ Role groups created')
                    return True
                    
                except ImportError as e:
                    self.stdout.write(f'  ⚠ Could not import RolePermission: {e}')
                except Exception as e:
                    self.stdout.write(f'  ⚠ Error setting up role permissions: {e}')
            
            self.stdout.write('  ⚠ Skipping role permissions (auth app not ready)')
            return True
            
        except Exception as e:
            self.stdout.write(f'  ✗ Role permission setup failed: {e}')
            if options.get('force'):
                self.stdout.write('  ⚠ Continuing without role permissions (--force flag)')
                return False
            raise
    
    def _create_basic_permissions(self):
        """Create basic permissions if no permission command exists"""
        from django.contrib.auth.models import Permission, Group, ContentType
        from django.contrib.auth.management import create_permissions
        from django.apps import apps
        
        # Ensure Django permissions are created
        for app_config in apps.get_app_configs():
            app_config.models_module = True
            create_permissions(app_config, verbosity=0)
            app_config.models_module = None
        
        # Create basic admin group with all permissions
        admin_group, created = Group.objects.get_or_create(name='Administrator')
        all_perms = Permission.objects.all()
        admin_group.permissions.set(all_perms)
        
        # Create other basic groups
        basic_groups = ['Teacher', 'Student', 'Staff']
        for group_name in basic_groups:
            Group.objects.get_or_create(name=group_name)
    
    def _print_summary(self, steps_completed, total_steps, options):
        """Print setup summary"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('SETUP SUMMARY'.center(60))
        self.stdout.write('=' * 60)
        
        success_rate = (steps_completed / total_steps) * 100
        
        if success_rate == 100:
            self.stdout.write(self.style.SUCCESS(f'\n✅ SUCCESS: All {total_steps} steps completed!'))
        elif success_rate >= 80:
            self.stdout.write(self.style.WARNING(f'\n⚠ WARNING: {steps_completed}/{total_steps} steps completed ({success_rate:.0f}%)'))
        else:
            self.stdout.write(self.style.ERROR(f'\n❌ FAILURE: Only {steps_completed}/{total_steps} steps completed ({success_rate:.0f}%)'))
        
        # Next steps
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write('NEXT STEPS:'.center(60))
        self.stdout.write('─' * 60)
        
        next_steps = [
            "1. Log in to the admin panel at /admin/",
            "2. Create tenants for your organization",
            "3. Set up user roles and permissions",
            "4. Configure system settings",
            "5. Create departments and courses",
            "6. Add students and staff members",
        ]
        
        for step in next_steps:
            self.stdout.write(f'  {step}')
        
        # Important notes
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write('IMPORTANT NOTES:'.center(60))
        self.stdout.write('─' * 60)
        
        notes = [
            "• Default superuser: admin@erpsystem.com / admin123",
            "• Change default passwords immediately!",
            "• Review role permissions in the admin panel",
            "• Create tenant-specific configurations",
            "• Test user access with different roles",
        ]
        
        for note in notes:
            self.stdout.write(f'  {note}')
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('SETUP COMPLETE'.center(60))
        self.stdout.write('=' * 60 + '\n')