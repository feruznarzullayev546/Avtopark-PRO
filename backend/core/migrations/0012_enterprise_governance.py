from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_branch_scope'),
    ]

    operations = [

        migrations.CreateModel(
            name='CompanyRole',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'key',
                    models.SlugField(max_length=60)
                ),
                (
                    'name',
                    models.CharField(max_length=100)
                ),
                (
                    'description',
                    models.CharField(
                        max_length=255,
                        blank=True
                    )
                ),
                (
                    'permissions',
                    models.JSONField(
                        default=list,
                        blank=True
                    )
                ),
                (
                    'is_system',
                    models.BooleanField(default=False)
                ),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True)
                ),
                (
                    'company',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='custom_roles',
                        to='core.company'
                    )
                ),
            ],
            options={
                'ordering': ['name'],
                'constraints': [
                    models.UniqueConstraint(
                        fields=['company', 'key'],
                        name='uniq_company_role_key'
                    )
                ],
            },
        ),

        migrations.AddField(
            model_name='companymembership',
            name='custom_role',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='memberships',
                to='core.companyrole'
            ),
        ),

        migrations.CreateModel(
            name='ApprovalPolicy',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'action',
                    models.CharField(max_length=80)
                ),
                (
                    'threshold',
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=18
                    )
                ),
                (
                    'required_role',
                    models.CharField(
                        default='DIRECTOR',
                        max_length=30
                    )
                ),
                (
                    'is_active',
                    models.BooleanField(default=True)
                ),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True)
                ),
                (
                    'company',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='approval_policies',
                        to='core.company'
                    )
                ),
                (
                    'branch',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='approval_policies',
                        to='core.branch'
                    )
                ),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(
                        fields=['company', 'branch', 'action'],
                        name='uniq_approval_policy_scope_action'
                    )
                ],
            },
        ),

        migrations.CreateModel(
            name='ApprovalRequest',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'action',
                    models.CharField(max_length=80)
                ),
                (
                    'object_type',
                    models.CharField(max_length=100)
                ),
                (
                    'object_id',
                    models.CharField(max_length=60)
                ),
                (
                    'amount',
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=18
                    )
                ),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('PENDING', 'Kutilmoqda'),
                            ('APPROVED', 'Tasdiqlangan'),
                            ('REJECTED', 'Rad etilgan'),
                            ('CANCELLED', 'Bekor qilingan')
                        ],
                        default='PENDING',
                        max_length=20
                    )
                ),
                (
                    'reason',
                    models.TextField(blank=True)
                ),
                (
                    'decision_note',
                    models.TextField(blank=True)
                ),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True)
                ),
                (
                    'decided_at',
                    models.DateTimeField(
                        blank=True,
                        null=True
                    )
                ),
                (
                    'company',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='approval_requests',
                        to='core.company'
                    )
                ),
                (
                    'branch',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='approval_requests',
                        to='core.branch'
                    )
                ),
                (
                    'requester',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='approval_requests',
                        to=settings.AUTH_USER_MODEL
                    )
                ),
                (
                    'decided_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='decided_approval_requests',
                        to=settings.AUTH_USER_MODEL
                    )
                ),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(
                        fields=['company', 'status', 'created_at'],
                        name='approval_req_company_status_created'
                    ),
                    models.Index(
                        fields=['branch', 'status', 'created_at'],
                        name='approval_req_branch_status_created'
                    ),
                ],
            },
        ),

        migrations.AddField(
            model_name='auditlog',
            name='branch',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='audit_logs',
                to='core.branch'
            ),
        ),

        migrations.AddField(
            model_name='auditlog',
            name='metadata',
            field=models.JSONField(
                default=dict,
                blank=True
            ),
        ),

        migrations.AddField(
            model_name='auditlog',
            name='ip_address',
            field=models.GenericIPAddressField(
                blank=True,
                null=True
            ),
        ),

        migrations.AddField(
            model_name='auditlog',
            name='user_agent',
            field=models.CharField(
                blank=True,
                max_length=500
            ),
        ),

        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(
                fields=['branch', 'created_at'],
                name='core_audit_branch_created'
            )
        ),
    ]