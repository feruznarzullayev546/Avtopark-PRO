from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Company, Subscription, UserProfile, Notification

class Command(BaseCommand):
    help='Free Trial uchun kundalik billing bildirishnomalarini yaratadi.'
    def handle(self,*args,**kwargs):
        today=timezone.localdate(); created=0
        for c in Company.objects.filter(is_active=True,trial_ends_at__isnull=False):
            sub=Subscription.objects.filter(company=c).first()
            if not sub or sub.status!='TRIAL': continue
            left=(c.trial_ends_at-today).days
            if left<0: continue
            if left==0: msg='Bepul sinov muddati bugun yakunlanadi. Xizmatlar uzluksiz davom etishi uchun tarif rejasini faollashtiring.'
            elif left==1: msg='Bepul sinov muddati yakunlanishiga 1 kun qoldi. O‘zingizga mos tarifni tanlab, xizmatlarni davom ettiring.'
            else: msg=f'Bepul sinov muddatingiz yakunlanishiga {left} kun qoldi. Platformadan uzluksiz foydalanish uchun tarif rejasini tanlang.'
            for profile in UserProfile.objects.filter(company=c,is_active=True):
                key=f'trial-{c.id}-{today.isoformat()}-{profile.id}'
                _,was_created=Notification.objects.get_or_create(recipient=profile,company=c,dedupe_key=key,defaults={'title':'Trial eslatmasi','message':msg,'url':'/billing'})
                created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f'Trial notificationlar yaratildi: {created}'))
