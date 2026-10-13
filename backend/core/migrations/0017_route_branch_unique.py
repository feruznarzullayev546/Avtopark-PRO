from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0016_trip_in_progress')]
    operations = [
        migrations.RemoveConstraint(
            model_name='route',
            name='uniq_route_company_name',
        ),
        migrations.AddConstraint(
            model_name='route',
            constraint=models.UniqueConstraint(
                fields=('company', 'branch', 'name'),
                name='uniq_route_company_branch_name',
            ),
        ),
    ]
