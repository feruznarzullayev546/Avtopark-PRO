from django.db import migrations, models
import django.db.models.deletion
import django.conf
import django.utils.timezone


def seed_company_codes(apps, schema_editor):
    from django.utils.text import slugify
    Company = apps.get_model('core', 'Company')
    for c in Company.objects.order_by('id'):
        base=slugify(c.name) or 'company'; slug=f'{base}-{c.id}'
        code=f'AP-{c.id:06d}'
        Company.objects.filter(pk=c.pk).update(slug=slug, code=code)

def seed_memberships(apps, schema_editor):
    Company = apps.get_model('core', 'Company')
    UserProfile = apps.get_model('core', 'UserProfile')
    Membership = apps.get_model('core', 'CompanyMembership')
    for p in UserProfile.objects.select_related('company').all():
        if p.company_id:
            Membership.objects.get_or_create(user_id=p.user_id, company_id=p.company_id, defaults={
                'role': p.role if p.role in {'DIRECTOR','MANAGER','DRIVER'} else 'VIEWER',
                'status': 'ACTIVE', 'is_default': True,
            })

class Migration(migrations.Migration):
    dependencies=[('core','0008_warehouse_pro')]
    operations=[
        migrations.AddField(model_name='company',name='slug',field=models.SlugField(blank=True,max_length=190)),
        migrations.AddField(model_name='company',name='code',field=models.CharField(blank=True,max_length=30)),
        migrations.AddField(model_name='company',name='industry',field=models.CharField(blank=True,max_length=120)),
        migrations.AddField(model_name='company',name='status',field=models.CharField(choices=[('ACTIVE','Faol'),('SUSPENDED','To‘xtatilgan'),('ARCHIVED','Arxiv')],default='ACTIVE',max_length=20)),
        migrations.AddField(model_name='company',name='max_users',field=models.PositiveIntegerField(default=10)),
        migrations.AddField(model_name='company',name='max_vehicles',field=models.PositiveIntegerField(default=50)),
        migrations.RunPython(seed_company_codes, migrations.RunPython.noop),
        migrations.AlterField(model_name='company',name='slug',field=models.SlugField(blank=True,max_length=190,unique=True)),
        migrations.AlterField(model_name='company',name='code',field=models.CharField(blank=True,max_length=30,unique=True)),
        migrations.CreateModel(name='CompanyMembership',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('role',models.CharField(choices=[('DIRECTOR','Direktor'),('MANAGER','Manager'),('DRIVER','Haydovchi'),('ACCOUNTANT','Buxgalter'),('WAREHOUSE','Omborchi'),('DISPATCHER','Dispetcher'),('VIEWER','Kuzatuvchi')],default='VIEWER',max_length=20)),
            ('status',models.CharField(choices=[('ACTIVE','Faol'),('INVITED','Taklif qilingan'),('SUSPENDED','Bloklangan'),('REMOVED','Chiqarilgan')],default='ACTIVE',max_length=20)),
            ('is_default',models.BooleanField(default=False)),('permissions',models.JSONField(blank=True,default=dict)),('joined_at',models.DateTimeField(auto_now_add=True)),('updated_at',models.DateTimeField(auto_now=True)),
            ('company',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='memberships',to='core.company')),
            ('invited_by',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='sent_company_memberships',to=django.conf.settings.AUTH_USER_MODEL)),
            ('user',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='company_memberships',to=django.conf.settings.AUTH_USER_MODEL)),
        ], options={'verbose_name':'Kompaniya a’zoligi','verbose_name_plural':'Kompaniya a’zoliklari'},),
        migrations.AddIndex(model_name='companymembership',index=models.Index(fields=['user','status'],name='core_compan_user_id_6c2f6f_idx')),
        migrations.AddIndex(model_name='companymembership',index=models.Index(fields=['company','status'],name='core_compan_company_9a89e2_idx')),
        migrations.AddIndex(model_name='companymembership',index=models.Index(fields=['company','role'],name='core_compan_company_4f6b1c_idx')),
        migrations.AddConstraint(model_name='companymembership',constraint=models.UniqueConstraint(fields=('user','company'),name='uniq_company_membership_user_company')),
        migrations.CreateModel(name='CompanyInvitation',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('email',models.EmailField(max_length=254)),('role',models.CharField(choices=[('DIRECTOR','Direktor'),('MANAGER','Manager'),('DRIVER','Haydovchi'),('ACCOUNTANT','Buxgalter'),('WAREHOUSE','Omborchi'),('DISPATCHER','Dispetcher'),('VIEWER','Kuzatuvchi')],default='VIEWER',max_length=20)),('token_hash',models.CharField(max_length=128,unique=True)),('expires_at',models.DateTimeField()),('accepted_at',models.DateTimeField(blank=True,null=True)),('revoked_at',models.DateTimeField(blank=True,null=True)),('created_at',models.DateTimeField(auto_now_add=True)),
            ('company',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='invitations',to='core.company')),
            ('invited_by',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='company_invitations',to=django.conf.settings.AUTH_USER_MODEL)),
        ], options={'ordering':['-created_at']}),
        migrations.AddIndex(model_name='companyinvitation',index=models.Index(fields=['company','email'],name='core_compan_company_2f8c1e_idx')),
        migrations.AddIndex(model_name='companyinvitation',index=models.Index(fields=['company','expires_at'],name='core_compan_company_8b1d3a_idx')),
        migrations.RunPython(seed_memberships, migrations.RunPython.noop),
    ]
