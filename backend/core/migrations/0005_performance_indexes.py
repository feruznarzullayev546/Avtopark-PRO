from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('core','0004_driver_assignment_and_cancellation')]
    operations = [
        migrations.AddIndex(model_name='trip', index=models.Index(fields=['company','date','status'], name='core_trip_comp_date_sta_idx')),
        migrations.AddIndex(model_name='trip', index=models.Index(fields=['company','driver','date'], name='core_trip_comp_driv_date_idx')),
        migrations.AddIndex(model_name='trip', index=models.Index(fields=['company','route','date'], name='core_trip_comp_rout_date_idx')),
        migrations.AddIndex(model_name='notification', index=models.Index(fields=['recipient','read_at','created_at'], name='core_notif_rec_read_idx')),
        migrations.AddIndex(model_name='notification', index=models.Index(fields=['driver','read_at','created_at'], name='core_notif_drv_read_idx')),
        migrations.AddIndex(model_name='notification', index=models.Index(fields=['company','created_at'], name='core_notif_comp_created_idx')),
        migrations.AddIndex(model_name='auditlog', index=models.Index(fields=['company','created_at'], name='core_audit_comp_created_idx')),
        migrations.AddIndex(model_name='auditlog', index=models.Index(fields=['company','action','created_at'], name='core_audit_comp_action_idx')),
        migrations.AddIndex(model_name='fuelentry', index=models.Index(fields=['company','date'], name='core_fuel_comp_date_idx')),
        migrations.AddIndex(model_name='fuelentry', index=models.Index(fields=['company','vehicle','date'], name='core_fuel_comp_veh_date_idx')),
    ]
