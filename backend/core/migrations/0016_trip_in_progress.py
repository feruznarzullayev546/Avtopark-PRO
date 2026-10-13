from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0015_alter_warehouseadjustment_options_and_more")]

    operations = [
        migrations.AlterField(
            model_name="trip",
            name="status",
            field=models.CharField(
                choices=[
                    ("PLANNED", "Rejalashtirilgan"),
                    ("CONFIRMED", "Qabul qilingan"),
                    ("IN_PROGRESS", "Yo‘lda"),
                    ("DONE", "Bajarilgan"),
                    ("CANCELLED", "Bekor qilingan"),
                ],
                default="PLANNED",
                max_length=20,
            ),
        ),
    ]
