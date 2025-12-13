# apps/core/management/commands/setup_system.py
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Complete system setup with proper order'
    
    def handle(self, *args, **options):
        self.stdout.write('Starting system setup...')
        
        # Step 1: Make sure migrations are applied
        self.stdout.write('1. Applying migrations...')
        try:
            call_command('migrate')
            self.stdout.write(self.style.SUCCESS('  ✓ Migrations applied'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error applying migrations: {e}'))
            return
        
        # Step 2: Create superuser if not exists
        self.stdout.write('2. Checking for superuser...')
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write('  No superuser found. Please create one:')
            call_command('createsuperuser')
        else:
            self.stdout.write('  ✓ Superuser exists')
        
        # Step 3: Create default permissions
        self.stdout.write('3. Creating default permissions...')
        try:
            call_command('init_permissions')
            self.stdout.write(self.style.SUCCESS('  ✓ Permissions initialized'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠ Error initializing permissions: {e}'))
        
        # Step 4: Setup role permissions
        self.stdout.write('4. Setting up role permissions...')
        try:
            call_command('setup_permissions')
            self.stdout.write(self.style.SUCCESS('  ✓ Role permissions setup complete'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠ Error setting up role permissions: {e}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ System setup complete!'))