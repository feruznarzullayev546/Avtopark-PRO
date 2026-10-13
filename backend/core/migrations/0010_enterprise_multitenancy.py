from django.db import migrations, models
import django.db.models.deletion
from django.utils.text import slugify


def seed_enterprise(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Organization = apps.get_model('core', 'Organization')
    OrganizationMembership = apps.get_model('core', 'OrganizationMembership')
    Company = apps.get_model('core', 'Company')
    Branch = apps.get_model('core', 'Branch')
    Membership = apps.get_model('core', 'CompanyMembership')

    for company in Company.objects.all().order_by('id'):
        if not company.organization_id:
            org = Organization.objects.create(
                name=company.name,
                slug=f"{slugify(company.name) or 'organization'}-{company.id}",
                code=f"ORG-{company.id:06d}",
                legal_name=company.legal_name,
                tin=company.tin,
                email=company.email,
                phone=company.phone,
            )
            company.organization_id = org.id
            company.save(update_fields=['organization'])
        else:
            org = company.organization
        memberships = list(Membership.objects.filter(company_id=company.id, status='ACTIVE').values_list('user_id', flat=True))
        for uid in memberships:
            role = 'OWNER' if Membership.objects.filter(company_id=company.id, user_id=uid, role='DIRECTOR', status='ACTIVE').exists() else 'ADMIN'
            OrganizationMembership.objects.get_or_create(
                organization_id=org.id, user_id=uid,
                defaults={'role': role, 'status': 'ACTIVE', 'is_default': True},
            )
        branch = Branch.objects.filter(company_id=company.id, is_headquarters=True).first()
        if not branch:
            branch = Branch.objects.filter(company_id=company.id).first()
        if not branch:
            branch = Branch.objects.create(company_id=company.id, name='Bosh filial', code='HQ', address=company.address, phone=company.phone, is_headquarters=True)
        if not company.default_branch_id:
            Company.objects.filter(pk=company.pk).update(default_branch_id=branch.id)


def reverse_noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [('core', '0009_multicompany')]
    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=180)),
                ('slug', models.SlugField(blank=True, max_length=190, unique=True)),
                ('code', models.CharField(blank=True, max_length=30, unique=True)),
                ('legal_name', models.CharField(blank=True, max_length=220)),
                ('tin', models.CharField(blank=True, max_length=30)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('phone', models.CharField(blank=True, max_length=40)),
                ('status', models.CharField(choices=[('ACTIVE','Faol'),('SUSPENDED','To‘xtatilgan'),('ARCHIVED','Arxiv')], default='ACTIVE', max_length=20)),
                ('max_companies', models.PositiveIntegerField(default=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering':['name']},
        ),
        migrations.AddIndex(model_name='organization', index=models.Index(fields=['status','name'], name='core_org_status_name_idx')),
        migrations.CreateModel(
            name='OrganizationMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('OWNER','Owner'),('ADMIN','Organization Admin'),('FINANCE','Finance'),('AUDITOR','Auditor'),('VIEWER','Viewer')], default='VIEWER', max_length=20)),
                ('status', models.CharField(choices=[('ACTIVE','Faol'),('SUSPENDED','Bloklangan'),('REMOVED','Chiqarilgan')], default='ACTIVE', max_length=20)),
                ('permissions', models.JSONField(blank=True, default=dict)),
                ('is_default', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='core.organization')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organization_memberships', to='auth.user')),
            ],
        ),
        migrations.AddConstraint(model_name='organizationmembership', constraint=models.UniqueConstraint(fields=('user','organization'), name='uniq_org_membership_user_org')),
        migrations.AddIndex(model_name='organizationmembership', index=models.Index(fields=['user','status'], name='core_orgmem_user_status_idx')),
        migrations.AddIndex(model_name='organizationmembership', index=models.Index(fields=['organization','status'], name='core_orgmem_org_status_idx')),
        migrations.AddField(model_name='company', name='organization', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='companies', to='core.organization')),
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)), ('code', models.CharField(max_length=30)),
                ('address', models.CharField(blank=True, max_length=255)), ('phone', models.CharField(blank=True, max_length=40)),
                ('manager_name', models.CharField(blank=True, max_length=150)), ('is_active', models.BooleanField(default=True)),
                ('is_headquarters', models.BooleanField(default=False)), ('created_at', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='branches', to='core.company')),
            ], options={'ordering':['-is_headquarters','name']},
        ),
        migrations.AddConstraint(model_name='branch', constraint=models.UniqueConstraint(fields=('company','code'), name='uniq_branch_company_code')),
        migrations.AddIndex(model_name='branch', index=models.Index(fields=['company','is_active'], name='core_branch_company_active_idx')),
        migrations.AddIndex(model_name='branch', index=models.Index(fields=['company','code'], name='core_branch_company_code_idx')),
        migrations.AddField(model_name='company', name='default_branch', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='default_for_companies', to='core.branch')),
        migrations.RunPython(seed_enterprise, reverse_noop),
    ]
