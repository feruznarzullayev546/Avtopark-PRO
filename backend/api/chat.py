import json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from core.models import ChatConversation, ChatMessage, CompanyMembership, UserProfile


def _profile(request):
    return UserProfile.objects.filter(user=request.user).select_related('company').first()

def _is_super(request):
    p=_profile(request)
    return bool(request.user.is_superuser or (p and p.role==UserProfile.ROLE_SUPER_ADMIN))

def _role_in_company(user, company_id):
    m=CompanyMembership.objects.filter(user=user,company_id=company_id,status=CompanyMembership.STATUS_ACTIVE).first()
    return m.role if m else None

def _can_chat_pair(request, other):
    if request.user.id == other.id: return False
    if _is_super(request):
        return _role_any_company(other) in {'DIRECTOR','MANAGER'}
    my_company_ids=set(CompanyMembership.objects.filter(user=request.user,status='ACTIVE').values_list('company_id',flat=True))
    if not my_company_ids: return False
    my_roles=set(CompanyMembership.objects.filter(user=request.user,status='ACTIVE').values_list('role',flat=True))
    if _role_any_company(other)=='SUPER_ADMIN' and my_roles & {'DIRECTOR','MANAGER'}: return True
    other_memberships=CompanyMembership.objects.filter(user=other,status='ACTIVE')
    for om in other_memberships:
        if om.company_id not in my_company_ids: continue
        if 'MANAGER' in my_roles and om.role=='DRIVER': return True
    return False

def _role_any_company(user):
    p=UserProfile.objects.filter(user=user).first()
    if user.is_superuser or (p and p.role=='SUPER_ADMIN'): return 'SUPER_ADMIN'
    return CompanyMembership.objects.filter(user=user,status='ACTIVE').values_list('role',flat=True).first()

def _serialize_user(user):
    p=UserProfile.objects.filter(user=user).first()
    role=_role_any_company(user) or ''
    return {'id':user.id,'name':(p.full_name if p and p.full_name else user.get_full_name() or user.username),'username':user.username,'role':role,'avatar_url':('/media/'+p.avatar.name) if p and p.avatar else None}

def _ordered_pair(a,b): return (a,b) if a < b else (b,a)

def _conversation_for(a,b):
    x,y=_ordered_pair(a,b)
    return ChatConversation.objects.filter(user_a_id=x,user_b_id=y).first()

@login_required
@csrf_protect
def contacts(request):
    if request.method!='GET': return JsonResponse({'error':'GET talab qilinadi'},status=405)
    qs=CompanyMembership.objects.filter(status='ACTIVE')
    if _is_super(request):
        users={m.user for m in qs.filter(role__in=['DIRECTOR','MANAGER']).select_related('user')}
    else:
        my_company_ids=set(qs.filter(user=request.user).values_list('company_id',flat=True))
        my_roles=set(qs.filter(user=request.user).values_list('role',flat=True))
        users=set()
        if 'DIRECTOR' in my_roles:
            users.update(u for u in __import__('django.contrib.auth',fromlist=['get_user_model']).get_user_model().objects.filter(is_superuser=True))
            users.update(u for u in UserProfile.objects.filter(role='SUPER_ADMIN',is_active=True).values_list('user',flat=True))
            # IDs are normalized below.
            users={__import__('django.contrib.auth',fromlist=['get_user_model']).get_user_model().objects.get(id=u if isinstance(u,int) else u.id) for u in users}
        if 'MANAGER' in my_roles:
            users.update(m.user for m in qs.filter(company_id__in=my_company_ids,role='DRIVER').select_related('user'))
    items=[]
    for u in users:
        c=_conversation_for(request.user.id,u.id)
        last=c.messages.order_by('-created_at').first() if c else None
        unread=c.messages.filter(read_at__isnull=True).exclude(sender=request.user).count() if c else 0
        items.append({'user':_serialize_user(u),'conversation_id':c.id if c else None,'last_message':last.body if last else None,'last_at':last.created_at.isoformat() if last else None,'unread':unread})
    items.sort(key=lambda x:x['last_at'] or '',reverse=True)
    return JsonResponse({'contacts':items})

@login_required
@csrf_protect
def conversation(request, user_id):
    try: other=__import__('django.contrib.auth',fromlist=['get_user_model']).get_user_model().objects.get(id=user_id,is_active=True)
    except Exception: return JsonResponse({'error':'Foydalanuvchi topilmadi'},status=404)
    if not _can_chat_pair(request,other): return JsonResponse({'error':'Bu foydalanuvchi bilan chat qilish huquqi yo‘q.'},status=403)
    a,b=_ordered_pair(request.user.id,other.id)
    if request.method=='GET':
        c=ChatConversation.objects.filter(user_a_id=a,user_b_id=b).first()
        if not c: return JsonResponse({'conversation':None,'messages':[],'other':_serialize_user(other)})
        msgs=list(c.messages.select_related('sender').order_by('created_at'))
        c.messages.filter(read_at__isnull=True).exclude(sender=request.user).update(read_at=timezone.now())
        return JsonResponse({'conversation':{'id':c.id,'updated_at':c.updated_at.isoformat()},'other':_serialize_user(other),'messages':[{'id':m.id,'sender_id':m.sender_id,'body':m.body,'created_at':m.created_at.isoformat(),'read_at':m.read_at.isoformat() if m.read_at else None} for m in msgs]})
    if request.method!='POST': return JsonResponse({'error':'GET yoki POST talab qilinadi'},status=405)
    try: payload=json.loads(request.body or '{}')
    except json.JSONDecodeError: return JsonResponse({'error':'Noto‘g‘ri JSON'},status=400)
    body=str(payload.get('body','')).strip()
    if not body: return JsonResponse({'error':'Xabar bo‘sh bo‘lishi mumkin emas.'},status=400)
    if len(body)>5000: return JsonResponse({'error':'Xabar 5000 belgidan oshmasin.'},status=400)
    with transaction.atomic():
        c,created=ChatConversation.objects.get_or_create(user_a_id=a,user_b_id=b,defaults={'company_id':None})
        if not _is_super(request):
            company_id=CompanyMembership.objects.filter(user=request.user,status='ACTIVE',company__memberships__user=other,company__memberships__status='ACTIVE').values_list('company_id',flat=True).first()
            if company_id: c.company_id=company_id; c.save(update_fields=['company','updated_at'])
        m=ChatMessage.objects.create(conversation=c,sender=request.user,body=body)
    message_payload={'id':m.id,'sender_id':m.sender_id,'body':body,'created_at':m.created_at.isoformat(),'read_at':None}
    try:
        async_to_sync(get_channel_layer().group_send)(f'chat.conversation.{a}.{b}', {'type':'chat.message','message':message_payload,'conversation_id':c.id})
    except Exception:
        pass
    return JsonResponse({'message':message_payload,'conversation_id':c.id},status=201)
