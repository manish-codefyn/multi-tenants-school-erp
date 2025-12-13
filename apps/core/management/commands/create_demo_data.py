from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Create demo groups, a superuser and a sample student user'

    def handle(self, *args, **options):
        User = get_user_model()

        # Create groups
        groups = ['student', 'admin', 'public']
        for g in groups:
            Group.objects.get_or_create(name=g)
        self.stdout.write(self.style.SUCCESS('Ensured groups: %s' % ','.join(groups)))

        # Create superuser
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(username='admin', email='admin@example.com', password='adminpass')
            self.stdout.write(self.style.SUCCESS('Created superuser: admin / adminpass'))
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists'))

        # Create sample student
        if not User.objects.filter(username='student1').exists():
            u = User.objects.create_user(username='student1', email='student1@example.com', password='studentpass')
            student_group = Group.objects.get(name='student')
            u.groups.add(student_group)
            u.save()
            self.stdout.write(self.style.SUCCESS('Created sample student: student1 / studentpass'))
        else:
            self.stdout.write(self.style.WARNING('Sample student already exists'))
