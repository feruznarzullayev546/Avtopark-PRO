from django.db import migrations, models
import django.db.models.deletion


def backfill_branches(apps, schema_editor):
    Company = apps.get_model('core', 'Company')
    models_to_fill = ['Vehicle','DriverProfile','Part','Receipt','Issue','WarehouseReturn','WarehouseAdjustment','Route','Trip','FuelEntry','OtherExpense']
    for company in Company.objects.all().iterator():
        branch_id = company.default_branch_id
        if not branch_id:
            branch = company.branches.filter(is_headquarters=True).first() or company.branches.first()
            branch_id = branch.id if branch else None
        if not branch_id:
            continue
        for model_name in models_to_fill:
            Model = apps.get_model('core', model_name)
            Model.objects.filter(company_id=company.id, branch__isnull=True).update(branch_id=branch_id)
        BranchMembership = apps.get_model('core','BranchMembership')
        CompanyMembership = apps.get_model('core','CompanyMembership')
        for cm in CompanyMembership.objects.filter(company_id=company.id,status='ACTIVE'):
            BranchMembership.objects.get_or_create(user_id=cm.user_id,branch_id=branch_id,defaults={'role':'MANAGER' if cm.role in ('DIRECTOR','MANAGER') else 'VIEWER','status':'ACTIVE','is_default':cm.is_default})

class Migration(migrations.Migration):
    dependencies=[('core','0010_enterprise_multitenancy')]
    operations=[
        migrations.CreateModel(
            name='BranchMembership',
            fields=[
                ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
                ('role',models.CharField(choices=[('MANAGER','Filial rahbari'),('OPERATOR','Operator'),('VIEWER','Kuzatuvchi')],default='VIEWER',max_length=20)),
                ('status',models.CharField(choices=[('ACTIVE','Faol'),('SUSPENDED','Bloklangan'),('REMOVED','Chiqarilgan')],default='ACTIVE',max_length=20)),
                ('permissions',models.JSONField(blank=True,default=dict)),
                ('is_default',models.BooleanField(default=False)),
                ('created_at',models.DateTimeField(auto_now_add=True)),
                ('updated_at',models.DateTimeField(auto_now=True)),
                ('branch',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='memberships',to='core.branch')),
                ('user',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='branch_memberships',to='auth.user')),
            ],
            options={'indexes':[models.Index(fields=['user','status'],name='core_branchm_user_id_4c4b0a_idx'),models.Index(fields=['branch','status'],name='core_branchm_branch_i_7c8e2e_idx')],'constraints':[models.UniqueConstraint(fields=('user','branch'),name='uniq_branch_membership_user_branch')]},
        ),
    ]
    for model in ['vehicle','driverprofile','part','receipt','issue','warehousereturn','warehouseadjustment','route','trip','fuelentry','otherexpense']:
        model_cls=model.capitalize() if model!='driverprofile' else 'DriverProfile'
        field_name='branch'
        related={'vehicle':'branch_vehicles','driverprofile':'branch_drivers','part':'branch_parts','receipt':'branch_receipts','issue':'branch_issues','warehousereturn':'branch_returns','warehouseadjustment':'branch_adjustments','route':'branch_routes','trip':'branch_trips','fuelentry':'branch_fuel_entries','otherexpense':'branch_other_expenses'}[model]
        operations_field=migrations.AddField(model_name=model, name=field_name, field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name=related,to='core.branch'))
        # can't append dynamically outside operations declaration
        operations_field
        # placeholder handled below
        
    operations += [migrations.AddField(model_name='vehicle',name='branch',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='branch_vehicles',to='core.branch')),
        migrations.AddField(model_name='driverprofile',name='branch',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='branch_drivers',to='core.branch')),
        migrations.AddField(model_name='part',name='branch',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='branch_parts',to='core.branch')),
        migrations.AddField(model_name='receipt',name='branch',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='branch_receipts',to='core.branch')),
        migrations.AddField(model_name='issue',name='branch',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='branch_issues',to='core.branch')),
        migrations.AddField(model_name='warehousereturn',name='branch',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='branch_returns',to='core.branch')),
        migrations.AddField(model_name='warehouseadjustment',name='branch',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='branch_adjustments',to='core.branch')),
        migrations.AddField(model_name='route',name='branch',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='branch_routes',to='core.branch')),
        migrations.AddField(model_name='trip',name='branch',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='branch_trips',to='core.branch')),
        migrations.AddField(model_name='fuelentry',name='branch',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='branch_fuel_entries',to='core.branch')),
        migrations.AddField(model_name='otherexpense',name='branch',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='branch_other_expenses',to='core.branch')),
        migrations.RunPython(backfill_branches,migrations.RunPython.noop),]
