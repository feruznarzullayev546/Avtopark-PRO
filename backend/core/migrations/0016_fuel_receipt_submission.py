from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('core', '0015_alter_warehouseadjustment_options_and_more'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name='fuelentry', name='receipt_image', field=models.FileField(blank=True, null=True, upload_to='fuel_receipts/%Y/%m/')),
        migrations.AddField(model_name='fuelentry', name='quantity_unit', field=models.CharField(choices=[('L', 'Litr'), ('M3', 'Kub metr')], default='L', max_length=10)),
        migrations.AddField(model_name='fuelentry', name='submitted_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fuel_submissions', to=settings.AUTH_USER_MODEL)),
    ]
