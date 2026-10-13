from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone

class Migration(migrations.Migration):
    dependencies=[('core','0012_enterprise_governance')]
    operations=[
        migrations.CreateModel(name='FeatureFlag',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('key',models.SlugField(max_length=80)),('enabled',models.BooleanField(default=True)),('rollout_percent',models.PositiveSmallIntegerField(default=100)),('config',models.JSONField(blank=True,default=dict)),('updated_at',models.DateTimeField(auto_now=True)),('company',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='feature_flags',to='core.company'))],options={'indexes':[models.Index(fields=['company','enabled'],name='core_featur_company_1d8f55_idx')]}),
        migrations.CreateModel(name='UsageMetric',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('metric',models.SlugField(max_length=80)),('value',models.PositiveBigIntegerField(default=0)),('limit',models.PositiveBigIntegerField(default=0)),('period_start',models.DateField(default=timezone.localdate)),('period_end',models.DateField(blank=True,null=True)),('updated_at',models.DateTimeField(auto_now=True)),('company',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='usage_metrics',to='core.company'))],options={'indexes':[models.Index(fields=['company','metric','period_end'],name='core_usage_company_9f0e5b_idx')]}),
        migrations.AddConstraint(model_name='featureflag',constraint=models.UniqueConstraint(fields=('company','key'),name='uniq_company_feature_flag')),
        migrations.AddConstraint(model_name='usagemetric',constraint=models.UniqueConstraint(fields=('company','metric','period_start'),name='uniq_company_metric_period')),
    ]
