# Generated manually for AVTOPARK PRO professional warehouse hardening.
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [('core', '0002_maintenanceschedule_vehiclemodelcatalog_issue_driver_and_more')]

    operations = [
        migrations.AlterModelOptions(name='userprofile', options={'verbose_name': 'Foydalanuvchi profili', 'verbose_name_plural': 'Foydalanuvchi profillari'}),
        migrations.AlterModelOptions(name='driverprofile', options={'verbose_name': 'Haydovchi', 'verbose_name_plural': 'Haydovchilar'}),
        migrations.AlterModelOptions(name='company', options={'verbose_name': 'Kompaniya', 'verbose_name_plural': 'Kompaniyalar', 'ordering': ['name']}),
        migrations.AlterModelOptions(name='vehiclemodelcatalog', options={'verbose_name': 'Avtomobil modeli', 'verbose_name_plural': 'Avtomobil modellari', 'ordering': ['name']}),
        migrations.AlterModelOptions(name='vehicle', options={'verbose_name': 'Avtomobil', 'verbose_name_plural': 'Avtomobillar', 'ordering': ['model', 'number']}),
        migrations.AlterModelOptions(name='part', options={'verbose_name': 'Ehtiyot qism', 'verbose_name_plural': 'Ehtiyot qismlar', 'ordering': ['name', 'code']}),
        migrations.AlterModelOptions(name='receipt', options={'verbose_name': 'Sklad kirimi', 'verbose_name_plural': 'Sklad kirimlari', 'ordering': ['-date', '-id']}),
        migrations.AlterModelOptions(name='issue', options={'verbose_name': 'Sklad chiqimi', 'verbose_name_plural': 'Sklad chiqimlari', 'ordering': ['-date', '-id']}),
        migrations.AlterModelOptions(name='maintenanceschedule', options={'verbose_name': 'Texnik xizmat rejasi', 'verbose_name_plural': 'Texnik xizmat rejalari', 'ordering': ['vehicle_id', 'name']}),
        migrations.AlterModelOptions(name='servicerecord', options={'verbose_name': 'Servis yozuvi', 'verbose_name_plural': 'Servis yozuvlari', 'unique_together': {('vehicle', 'service_type')}}),
        migrations.AlterModelOptions(name='route', options={'verbose_name': 'Yo‘nalish', 'verbose_name_plural': 'Yo‘nalishlar'}),
        migrations.AlterModelOptions(name='trip', options={'verbose_name': 'Reys', 'verbose_name_plural': 'Reyslar', 'ordering': ['-date', '-id']}),
        migrations.AlterModelOptions(name='notification', options={'verbose_name': 'Bildirishnoma', 'verbose_name_plural': 'Bildirishnomalar', 'ordering': ['-created_at']}),
        migrations.AlterModelOptions(name='auditlog', options={'verbose_name': 'Audit yozuvi', 'verbose_name_plural': 'Audit yozuvlari', 'ordering': ['-created_at']}),
        migrations.AlterModelOptions(name='fuelentry', options={'verbose_name': 'Yoqilg‘i yozuvi', 'verbose_name_plural': 'Yoqilg‘i yozuvlari'}),
        migrations.AlterModelOptions(name='subscriptionplan', options={'verbose_name': 'Tarif', 'verbose_name_plural': 'Tariflar', 'ordering': ['sort_order', 'price_monthly', 'name']}),
        migrations.AlterModelOptions(name='subscription', options={'verbose_name': 'Obuna', 'verbose_name_plural': 'Obunalar'}),
        migrations.AlterModelOptions(name='invoice', options={'verbose_name': 'Hisob-faktura', 'verbose_name_plural': 'Hisob-fakturalar', 'ordering': ['-issue_date', '-id']}),
        migrations.AlterModelOptions(name='payment', options={'verbose_name': 'To‘lov', 'verbose_name_plural': 'To‘lovlar', 'ordering': ['-received_at', '-id']}),

        migrations.AddIndex(model_name='part', index=models.Index(fields=['company', 'category'], name='core_part_company_cat_idx')),
        migrations.AddIndex(model_name='part', index=models.Index(fields=['company', 'name'], name='core_part_company_name_idx')),
        migrations.AddIndex(model_name='receipt', index=models.Index(fields=['company', 'part', 'date'], name='core_receipt_company_part_idx')),
        migrations.AddIndex(model_name='receipt', index=models.Index(fields=['company', 'date'], name='core_receipt_company_date_idx')),
        migrations.AddIndex(model_name='issue', index=models.Index(fields=['company', 'part', 'date'], name='core_issue_company_part_idx')),
        migrations.AddIndex(model_name='issue', index=models.Index(fields=['company', 'vehicle', 'date'], name='core_issue_company_vehicle_idx')),
        migrations.AddIndex(model_name='issue', index=models.Index(fields=['company', 'date'], name='core_issue_company_date_idx')),

        migrations.AddConstraint(model_name='vehicle', constraint=models.CheckConstraint(condition=Q(current_mileage__gte=0), name='vehicle_mileage_nonnegative')),
        migrations.AddConstraint(model_name='vehicle', constraint=models.CheckConstraint(condition=Q(avg_daily_km__gte=0), name='vehicle_avg_km_nonnegative')),
        migrations.AddConstraint(model_name='vehicle', constraint=models.CheckConstraint(condition=Q(tonnage__gte=0), name='vehicle_tonnage_nonnegative')),
        migrations.AddConstraint(model_name='part', constraint=models.CheckConstraint(condition=Q(min_stock__gte=0), name='part_min_stock_nonnegative')),
        migrations.AddConstraint(model_name='part', constraint=models.CheckConstraint(condition=Q(unit_price__gte=0), name='part_unit_price_nonnegative')),
        migrations.AddConstraint(model_name='receipt', constraint=models.CheckConstraint(condition=Q(quantity__gt=0), name='receipt_quantity_positive')),
        migrations.AddConstraint(model_name='receipt', constraint=models.CheckConstraint(condition=Q(unit_price__gte=0), name='receipt_unit_price_nonnegative')),
        migrations.AddConstraint(model_name='issue', constraint=models.CheckConstraint(condition=Q(quantity__gt=0), name='issue_quantity_positive')),
        migrations.AddConstraint(model_name='issue', constraint=models.CheckConstraint(condition=Q(unit_price__gte=0), name='issue_unit_price_nonnegative')),
        migrations.AddConstraint(model_name='fuelentry', constraint=models.CheckConstraint(condition=Q(liters__gt=0), name='fuel_liters_positive')),
        migrations.AddConstraint(model_name='fuelentry', constraint=models.CheckConstraint(condition=Q(price_per_liter__gte=0), name='fuel_price_nonnegative')),
    ]
