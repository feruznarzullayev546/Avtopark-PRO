from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_saas_governance'),
    ]

    operations = [

        migrations.CreateModel(
            name='PlatformSecurityEvent',
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
                    'event_type',
                    models.CharField(max_length=60)
                ),
                (
                    'severity',
                    models.CharField(
                        max_length=20,
                        default='INFO',
                        choices=[
                            ('INFO', 'Info'),
                            ('WARNING', 'Warning'),
                            ('CRITICAL', 'Critical'),
                        ]
                    )
                ),
                (
                    'ip_address',
                    models.GenericIPAddressField(
                        null=True,
                        blank=True
                    )
                ),
                (
                    'user_agent',
                    models.TextField(blank=True)
                ),
                (
                    'metadata',
                    models.JSONField(
                        default=dict,
                        blank=True
                    )
                ),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True)
                ),
                (
                    'organization',
                    models.ForeignKey(
                        null=True,
                        blank=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='platform_security_events',
                        to='core.organization'
                    )
                ),
                (
                    'company',
                    models.ForeignKey(
                        null=True,
                        blank=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='platform_security_events',
                        to='core.company'
                    )
                ),
                (
                    'user',
                    models.ForeignKey(
                        null=True,
                        blank=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='platform_security_events',
                        to='auth.user'
                    )
                ),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(
                        fields=['severity', 'created_at'],
                        name='platform_event_severity_created'
                    ),
                    models.Index(
                        fields=['organization', 'created_at'],
                        name='platform_event_org_created'
                    ),
                    models.Index(
                        fields=['event_type', 'created_at'],
                        name='platform_event_type_created'
                    ),
                ],
            },
        ),

        migrations.CreateModel(
            name='PlatformSession',
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
                    'session_key_hash',
                    models.CharField(
                        max_length=128,
                        unique=True
                    )
                ),
                (
                    'ip_address',
                    models.GenericIPAddressField(
                        null=True,
                        blank=True
                    )
                ),
                (
                    'user_agent',
                    models.TextField(blank=True)
                ),
                (
                    'device_label',
                    models.CharField(
                        max_length=120,
                        blank=True
                    )
                ),
                (
                    'is_active',
                    models.BooleanField(default=True)
                ),
                (
                    'last_seen_at',
                    models.DateTimeField(auto_now=True)
                ),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True)
                ),
                (
                    'revoked_at',
                    models.DateTimeField(
                        null=True,
                        blank=True
                    )
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='platform_sessions',
                        to='auth.user'
                    )
                ),
            ],
            options={
                'ordering': ['-last_seen_at'],
                'indexes': [
                    models.Index(
                        fields=['user', 'is_active'],
                        name='platform_session_user_active'
                    ),
                    models.Index(
                        fields=['last_seen_at'],
                        name='platform_session_last_seen'
                    ),
                ],
            },
        ),

    ]