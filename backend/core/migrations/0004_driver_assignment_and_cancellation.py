from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('core','0003_professional_warehouse_and_uzbek_options')]
    operations = [
        migrations.AddField(model_name='driverprofile',name='suspended_until',field=models.DateField(blank=True,null=True)),
        migrations.AddField(model_name='driverprofile',name='last_assigned_at',field=models.DateTimeField(blank=True,null=True)),
        migrations.AddField(model_name='trip',name='cancellation_reason',field=models.TextField(blank=True)),
        migrations.AddField(model_name='trip',name='cancelled_at',field=models.DateTimeField(blank=True,null=True)),
        migrations.AddField(model_name='trip',name='cancellation_review',field=models.CharField(choices=[('PENDING','Ko‘rib chiqilmoqda'),('JUSTIFIED','Asosli'),('UNJUSTIFIED','Asossiz')],default='PENDING',max_length=20)),
        migrations.AddField(model_name='trip',name='cancellation_review_note',field=models.TextField(blank=True)),
        migrations.AddField(model_name='trip',name='reviewed_at',field=models.DateTimeField(blank=True,null=True)),
        migrations.AddField(model_name='trip',name='reviewed_by',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='reviewed_trip_cancellations',to='auth.user')),
    ]
