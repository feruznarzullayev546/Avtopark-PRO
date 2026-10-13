from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import FuelEntry

class Command(BaseCommand):
    help = 'Deletes dispenser/fuel photos older than 365 days while retaining report rows.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=365)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=max(1, options['days']))
        qs = FuelEntry.objects.filter(receipt_image__gt='').filter(submitted_at__lt=cutoff)
        count = qs.count()
        if options['dry_run']:
            self.stdout.write(f'DRY RUN: {count} photo files eligible for removal.')
            return
        removed = 0
        for entry in qs.iterator():
            if entry.receipt_image:
                entry.receipt_image.delete(save=False)
                entry.save(update_fields=['receipt_image'])
                removed += 1
        self.stdout.write(self.style.SUCCESS(f'Removed {removed} photo files; report rows retained.'))
