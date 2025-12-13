# apps/core/management/commands/setup_database.py
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Setup database only (migrations and superuser)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-superuser',
            action='store_true',
            help='Skip superuser creation',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Setting up database...')
        
        # Apply migrations
        self.stdout.write('1. Applying migrations...')
        call_command('migrate')
        self.stdout.write(self.style.SUCCESS('  ✓ Migrations applied'))
        
        # Create superuser
        if not options['skip_superuser']:
            self.stdout.write('2. Creating superuser...')
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            if not User.objects.filter(is_superuser=True).exists():
                call_command('createsuperuser')
                self.stdout.write(self.style.SUCCESS('  ✓ Superuser created'))
            else:
                self.stdout.write('  ⚡ Superuser already exists')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Database setup complete!'))