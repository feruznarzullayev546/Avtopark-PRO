from django.core.management.base import BaseCommand
from core.models import Company
from core.services import notify_maintenance_staff

class Command(BaseCommand):
    requires_system_checks = []
    help='Servis/almashtirish statuslarini tekshiradi va Manager/Director ga ogohlantirish yuboradi.'
    def handle(self,*args,**options):
        for company in Company.objects.filter(is_active=True):
            notify_maintenance_staff(company)
        self.stdout.write(self.style.SUCCESS('Maintenance notifications checked.'))
