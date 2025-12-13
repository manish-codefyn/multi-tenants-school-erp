import shutil
from pathlib import Path
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Copy Backend Theme assets from templates/Backend Theme/assets to static/backend_theme/assets'

    def handle(self, *args, **options):
        base = Path(__file__).resolve().parent.parent.parent.parent
        src = base / 'templates' / 'Backend Theme' / 'assets'
        dst = base / 'static' / 'backend_theme' / 'assets'
        if not src.exists():
            self.stdout.write(self.style.ERROR(f'Source assets not found: {src}'))
            return
        if dst.exists():
            self.stdout.write(self.style.WARNING(f'Destination already exists, removing: {dst}'))
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        self.stdout.write(self.style.SUCCESS(f'Copied backend theme assets to {dst}'))
