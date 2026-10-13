from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0007_otherexpense'),
    ]
    operations = [
        migrations.AddField(
            model_name='issue',
            name='expense',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='warehouse_issue', to='core.otherexpense'),
        ),
        migrations.CreateModel(
            name='WarehouseAdjustment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=timezone.localdate)),
                ('quantity', models.FloatField()),
                ('unit_price', models.FloatField(default=0)),
                ('reason', models.CharField(max_length=180)),
                ('document_no', models.CharField(blank=True, max_length=80)),
                ('note', models.TextField(blank=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='warehouse_adjustments', to='core.company')),
                ('part', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='adjustments', to='core.part')),
            ],
            options={'ordering':['-date','-id']},
        ),
        migrations.CreateModel(
            name='WarehouseReturn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=timezone.localdate)),
                ('quantity', models.FloatField()),
                ('unit_price', models.FloatField(default=0)),
                ('document_no', models.CharField(blank=True, max_length=80)),
                ('reason', models.CharField(blank=True, max_length=180)),
                ('note', models.TextField(blank=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='warehouse_returns', to='core.company')),
                ('issue', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='returns', to='core.issue')),
                ('part', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='returns', to='core.part')),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='warehouse_returns', to='core.vehicle')),
            ],
            options={'ordering':['-date','-id']},
        ),
        migrations.AddIndex(model_name='warehouseadjustment', index=models.Index(fields=['company','date'], name='core_warehou_company_1d4f7b_idx')),
        migrations.AddIndex(model_name='warehouseadjustment', index=models.Index(fields=['company','part','date'], name='core_warehou_company_5c6f6a_idx')),
        migrations.AddIndex(model_name='warehousereturn', index=models.Index(fields=['company','date'], name='core_warehou_company_84a9d0_idx')),
        migrations.AddIndex(model_name='warehousereturn', index=models.Index(fields=['company','part','date'], name='core_warehou_company_5a1d44_idx')),
        migrations.AddIndex(model_name='warehousereturn', index=models.Index(fields=['company','vehicle','date'], name='core_warehou_company_9b4a1c_idx')),
        migrations.AddConstraint(model_name='warehouseadjustment', constraint=models.CheckConstraint(condition=models.Q(('unit_price__gte',0)), name='warehouse_adjustment_price_nonnegative')),
        migrations.AddConstraint(model_name='warehousereturn', constraint=models.CheckConstraint(condition=models.Q(('quantity__gt',0)), name='warehouse_return_quantity_positive')),
        migrations.AddConstraint(model_name='warehousereturn', constraint=models.CheckConstraint(condition=models.Q(('unit_price__gte',0)), name='warehouse_return_price_nonnegative')),
    ]
