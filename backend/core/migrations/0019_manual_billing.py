from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('core','0018_chat')]
    operations=[
        migrations.CreateModel(
            name='PaymentCard',
            fields=[
                ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
                ('company_name',models.CharField(blank=True,default='AVTOPARK PRO',max_length=180)),
                ('card_number',models.CharField(max_length=32)),
                ('holder_name',models.CharField(blank=True,max_length=180)),
                ('bank_name',models.CharField(blank=True,max_length=120)),
                ('is_active',models.BooleanField(default=True)),
                ('sort_order',models.PositiveIntegerField(default=0)),
                ('created_at',models.DateTimeField(auto_now_add=True)),
                ('updated_at',models.DateTimeField(auto_now=True)),
            ],
            options={'ordering':['sort_order','id']},
        ),
        migrations.AddField(model_name='invoice',name='assigned_card',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='invoices',to='core.paymentcard')),
        migrations.AddField(model_name='payment',name='payment_card',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='payments',to='core.paymentcard')),
        migrations.AddField(model_name='payment',name='receipt',field=models.FileField(blank=True,null=True,upload_to='billing/receipts/')),
        migrations.AddField(model_name='payment',name='reviewed_at',field=models.DateTimeField(blank=True,null=True)),
        migrations.AddField(model_name='payment',name='reviewed_by',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='reviewed_payments',to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='payment',name='review_note',field=models.CharField(blank=True,max_length=500)),
    ]
