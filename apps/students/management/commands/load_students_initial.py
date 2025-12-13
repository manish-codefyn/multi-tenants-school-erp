from django.core.management.base import BaseCommand
from django.core.management import call_command
from pathlib import Path


class Command(BaseCommand):
    help = 'Load students app initial fixtures'

    def handle(self, *args, **options):
        fixture = Path(__file__).resolve().parent.parent / 'fixtures' / 'initial_data.json'
        if not fixture.exists():
            self.stdout.write(self.style.WARNING(f'Fixture not found: {fixture}'))
            return
        call_command('loaddata', str(fixture))
        self.stdout.write(self.style.SUCCESS('Loaded students fixtures'))
