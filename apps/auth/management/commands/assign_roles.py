import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Assign roles to users from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', 
            type=str, 
            help='Path to the JSON file containing user roles (relative to apps/auth/data/ by default)'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        # Default path if none provided
        if not file_path:
            base_dir = settings.BASE_DIR
            file_path = os.path.join(base_dir, 'apps', 'auth', 'data', 'user_roles.json')
        
        # Ensure file exists
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                self.stdout.write(self.style.ERROR('JSON data must be a list of objects'))
                return

            self.stdout.write(f"Found {len(data)} users to process...")
            
            success_count = 0
            error_count = 0
            
            for item in data:
                email = item.get('email')
                role = item.get('role')
                
                if not email or not role:
                    self.stdout.write(self.style.WARNING(f'Skipping invalid item: {item}'))
                    continue
                    
                # validate role
                if role not in dict(User.ROLE_CHOICES):
                    self.stdout.write(self.style.WARNING(f'Invalid role "{role}" for user {email}. Skipping.'))
                    continue

                try:
                    user = User.objects.get(email=email)
                    if user.role != role:
                        user.role = role
                        user.save(update_fields=['role'])
                        self.stdout.write(self.style.SUCCESS(f'Updated {email} to {role}'))
                    else:
                        self.stdout.write(f'Skipping {email} (already {role})')
                    success_count += 1
                except User.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'User not found: {email}'))
                    error_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error updating {email}: {str(e)}'))
                    error_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'\nComplete! Updated: {success_count}, Errors/Skipped: {error_count}'))

        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Invalid JSON format in {file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))
