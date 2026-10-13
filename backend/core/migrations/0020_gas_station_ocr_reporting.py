from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0016_fuel_receipt_submission'),
        ('core', '0019_manual_billing'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='GasStation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=180)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('branch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='gas_stations', to='core.branch')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gas_stations', to='core.company')),
            ],
            options={'ordering': ['name']},
        ),
        migrations.AddConstraint(model_name='gasstation', constraint=models.UniqueConstraint(fields=('company', 'name'), name='uniq_gas_station_company_name')),
        migrations.AddIndex(model_name='gasstation', index=models.Index(fields=['company', 'active'], name='core_gassta_company_6ad3e2_idx')),
        migrations.AddField(model_name='fuelentry', name='gas_station', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fuel_entries', to='core.gasstation')),
        migrations.AddField(model_name='fuelentry', name='submitted_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='fuelentry', name='ocr_text', field=models.TextField(blank=True)),
        migrations.AddField(model_name='fuelentry', name='ocr_quantity_m3', field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name='fuelentry', name='ocr_status', field=models.CharField(choices=[('PENDING', 'Tekshirilmagan'), ('MATCH', 'Mos'), ('MISMATCH', 'Farq bor'), ('UNREADABLE', 'O‘qilmadi')], default='PENDING', max_length=20)),
    ]
