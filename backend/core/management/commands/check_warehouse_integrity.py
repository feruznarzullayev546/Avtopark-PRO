from django.core.management.base import BaseCommand
from django.db.models import Sum
from core.models import Part, Receipt, Issue

class Command(BaseCommand):
    help = 'Sklad kirim-chiqim ma’lumotlaridagi nomuvofiqliklarni tekshiradi.'
    def handle(self, *args, **options):
        bad=0
        for p in Part.objects.select_related('company').all():
            inc=Receipt.objects.filter(part=p).aggregate(v=Sum('quantity'))['v'] or 0
            out=Issue.objects.filter(part=p).aggregate(v=Sum('quantity'))['v'] or 0
            stock=float(inc)-float(out)
            if stock < -1e-9:
                bad+=1
                self.stdout.write(self.style.ERROR(f'{p.company.name}: {p.code} / {p.name} — manfiy qoldiq: {stock:g} {p.unit}'))
        if bad:
            self.stdout.write(self.style.ERROR(f'Tekshiruv yakunlandi: {bad} ta muammo topildi.'))
        else:
            self.stdout.write(self.style.SUCCESS('Sklad tekshiruvi muvaffaqiyatli: manfiy qoldiq topilmadi.'))
