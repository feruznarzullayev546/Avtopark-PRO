from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('core','0017_route_branch_unique')]
    operations=[
        migrations.CreateModel(
            name='ChatConversation',
            fields=[
                ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
                ('created_at',models.DateTimeField(auto_now_add=True)),
                ('updated_at',models.DateTimeField(auto_now=True)),
                ('company',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.CASCADE,related_name='chat_conversations',to='core.company')),
                ('user_a',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='chat_conversations_a',to=settings.AUTH_USER_MODEL)),
                ('user_b',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='chat_conversations_b',to=settings.AUTH_USER_MODEL)),
            ],
            options={'indexes':[models.Index(fields=['user_a','updated_at'],name='core_chatcon_user_a_8e7c1d_idx'),models.Index(fields=['user_b','updated_at'],name='core_chatcon_user_b_9bcf65_idx')]},
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
                ('body',models.TextField(max_length=5000)),
                ('created_at',models.DateTimeField(auto_now_add=True)),
                ('read_at',models.DateTimeField(blank=True,null=True)),
                ('conversation',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='messages',to='core.chatconversation')),
                ('sender',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='chat_messages',to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering':['created_at'],'indexes':[models.Index(fields=['conversation','created_at'],name='core_chatme_conversa_6b91a6_idx'),models.Index(fields=['conversation','read_at'],name='core_chatme_conversa_6b66c5_idx')]},
        ),
        migrations.AddConstraint(model_name='chatconversation',constraint=models.UniqueConstraint(fields=('user_a','user_b'),name='uniq_chat_conversation_pair')),
    ]
