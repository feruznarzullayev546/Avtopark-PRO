import json
from decimal import Decimal
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from core.models import (Company, CompanyMembership, CompanyRole, ApprovalPolicy, ApprovalRequest,
                         AuditLog, BranchMembership, UserProfile)
from .companies import _active_company, _is_super, ROLE_PERMISSIONS

PERMISSIONS = sorted(set(x for values in ROLE_PERMISSIONS.values() for x in values) | {
    'team.manage','roles.view','roles.manage','branches.view','branches.manage','audit.view','audit.export',
    'approvals.view','approvals.request','approvals.decide','billing.view','billing.manage','settings.manage',
    'platform.view','platform.manage'
})

def _membership(request, company=None):
    c=company or _active_company(request)
    if not c:return None
    return CompanyMembership.objects.select_related('custom_role').filter(user=request.user,company=c,status='ACTIVE').first()

def permissions_for(request):
    if _is_super(request): return set(PERMISSIONS)|{'platform.view','platform.manage'}
    m=_membership(request)
    if not m:return set()
    if m.custom_role_id:
        base=set(m.custom_role.permissions or [])
    else:
        base=set(ROLE_PERMISSIONS.get(m.role,[]))
    base.update(m.permissions.keys() if isinstance(m.permissions,dict) else (m.permissions or []))
    # explicit deny syntax: {"-finance.manage": true}
    if isinstance(m.permissions,dict):
        for key,val in m.permissions.items():
            if key.startswith('-') and val: base.discard(key[1:])
    return base

def has_permission(request, permission):
    perms=permissions_for(request)
    return permission in perms or permission.split('.')[0]+'.*' in perms

def require_permission(request, permission):
    if not request.user.is_authenticated:return JsonResponse({'error':'Autentifikatsiya talab qilinadi'},status=401)
    if not has_permission(request,permission):return JsonResponse({'error':f'Ruxsat yetarli emas: {permission}'},status=403)
    return None

def audit(request, action, model_name, description, obj_id='', company=None, metadata=None):
    c=company or _active_company(request)
    if not c:return
    branch=getattr(request,'active_branch',None)
    AuditLog.objects.create(company=c,branch=branch,user=request.user,action=action,model_name=model_name,object_id=str(obj_id or ''),description=description,metadata=metadata or {},ip_address=request.META.get('REMOTE_ADDR'),user_agent=request.META.get('HTTP_USER_AGENT','')[:500])

def _serialize_role(r):
    return {'id':r.id,'key':r.key,'name':r.name,'description':r.description,'permissions':r.permissions or [],'is_system':r.is_system}

@require_http_methods(['GET'])
def roles(request):
    denied=require_permission(request,'roles.view')
    if denied:return denied
    c=_active_company(request)
    rows=list(CompanyRole.objects.filter(company=c)) if c else []
    if c:
        for key,label in CompanyMembership.ROLE_CHOICES:
            defaults={'name':label,'permissions':ROLE_PERMISSIONS.get(key,[]),'is_system':True}
            CompanyRole.objects.get_or_create(company=c,key=key.lower(),defaults=defaults)
        rows=list(CompanyRole.objects.filter(company=c))
    return JsonResponse({'results':[_serialize_role(x) for x in rows],'catalog':PERMISSIONS})

@csrf_protect
@require_http_methods(['POST'])
def role_create(request):
    denied=require_permission(request,'roles.manage')
    if denied:return denied
    c=_active_company(request); data=json.loads(request.body or '{}')
    key=(data.get('key') or '').strip().lower(); name=(data.get('name') or '').strip()
    perms=[p for p in data.get('permissions',[]) if p in PERMISSIONS]
    if not key or not name:return JsonResponse({'error':'Key va nom majburiy'},status=400)
    if CompanyRole.objects.filter(company=c,key=key).exists():return JsonResponse({'error':'Bu role key mavjud'},status=400)
    r=CompanyRole.objects.create(company=c,key=key,name=name,description=data.get('description',''),permissions=perms,is_system=False)
    audit(request,'ROLE_CREATE','CompanyRole',f'Role yaratildi: {name}',r.id)
    return JsonResponse({'role':_serialize_role(r)},status=201)

@csrf_protect
@require_http_methods(['PATCH'])
def role_update(request, pk):
    denied=require_permission(request,'roles.manage')
    if denied:return denied
    c=_active_company(request); r=CompanyRole.objects.filter(pk=pk,company=c).first()
    if not r:return JsonResponse({'error':'Role topilmadi'},status=404)
    data=json.loads(request.body or '{}')
    if r.is_system and 'permissions' in data:return JsonResponse({'error':'System role permissionini bu yerdan o‘zgartirib bo‘lmaydi'},status=400)
    if 'name' in data:r.name=str(data['name']).strip() or r.name
    if 'description' in data:r.description=data['description']
    if 'permissions' in data:r.permissions=[p for p in data['permissions'] if p in PERMISSIONS]
    r.save(); audit(request,'ROLE_UPDATE','CompanyRole',f'Role yangilandi: {r.name}',r.id); return JsonResponse({'role':_serialize_role(r)})

@require_http_methods(['GET'])
def audit_center(request):
    denied=require_permission(request,'audit.view')
    if denied:return denied
    c=_active_company(request); qs=AuditLog.objects.filter(company=c).select_related('user','branch')
    action=request.GET.get('action'); branch=request.GET.get('branch_id'); limit=min(int(request.GET.get('limit',100)),500)
    if action:qs=qs.filter(action=action)
    if branch:qs=qs.filter(branch_id=branch)
    rows=[]
    for x in qs[:limit]: rows.append({'id':x.id,'action':x.action,'model':x.model_name,'object_id':x.object_id,'description':x.description,'user':x.user.username if x.user_id else 'SYSTEM','branch':x.branch.name if x.branch_id else '—','created_at':x.created_at.isoformat(),'metadata':x.metadata or {}})
    return JsonResponse({'results':rows,'count':qs.count()})

@require_http_methods(['GET'])
def approvals(request):
    denied=require_permission(request,'approvals.view')
    if denied:return denied
    c=_active_company(request); qs=ApprovalRequest.objects.filter(company=c).select_related('requester','decided_by','branch')
    status=request.GET.get('status')
    if status:qs=qs.filter(status=status)
    return JsonResponse({'results':[{'id':x.id,'action':x.action,'object_type':x.object_type,'object_id':x.object_id,'amount':str(x.amount),'status':x.status,'reason':x.reason,'decision_note':x.decision_note,'requester':x.requester.username,'decided_by':x.decided_by.username if x.decided_by_id else None,'branch':x.branch.name if x.branch_id else '—','created_at':x.created_at.isoformat(),'decided_at':x.decided_at.isoformat() if x.decided_at else None} for x in qs[:300]]})

@csrf_protect
@require_http_methods(['POST'])
def approval_request(request):
    denied=require_permission(request,'approvals.request')
    if denied:return denied
    c=_active_company(request); data=json.loads(request.body or '{}'); action=data.get('action'); amount=Decimal(str(data.get('amount') or 0))
    if not action or not data.get('object_type') or not data.get('object_id'):return JsonResponse({'error':'Approval request maydonlari to‘liq emas'},status=400)
    branch=getattr(request,'active_branch',None)
    policy=ApprovalPolicy.objects.filter(company=c,is_active=True,action=action).filter(branch=branch).first() or ApprovalPolicy.objects.filter(company=c,is_active=True,action=action,branch__isnull=True).first()
    if policy and amount < policy.threshold:
        return JsonResponse({'error':'Ushbu operatsiya approval thresholdidan past'},status=400)
    x=ApprovalRequest.objects.create(company=c,branch=branch,requester=request.user,action=action,object_type=data['object_type'],object_id=str(data['object_id']),amount=amount,reason=data.get('reason',''))
    audit(request,'APPROVAL_REQUEST','ApprovalRequest',f'Approval so‘rovi: {action}',x.id,metadata={'amount':str(amount)})
    return JsonResponse({'request_id':x.id,'status':x.status},status=201)

@csrf_protect
@require_http_methods(['POST'])
def approval_decide(request, pk):
    denied=require_permission(request,'approvals.decide')
    if denied:return denied
    c=_active_company(request); x=ApprovalRequest.objects.filter(pk=pk,company=c,status='PENDING').first()
    if not x:return JsonResponse({'error':'Pending approval topilmadi'},status=404)
    data=json.loads(request.body or '{}'); decision=data.get('decision')
    if decision not in {'APPROVED','REJECTED','CANCELLED'}:return JsonResponse({'error':'Noto‘g‘ri qaror'},status=400)
    x.status=decision;x.decision_note=data.get('note','');x.decided_by=request.user;x.decided_at=timezone.now();x.save(update_fields=['status','decision_note','decided_by','decided_at'])
    audit(request,'APPROVAL_DECISION','ApprovalRequest',f'Approval {decision}: {x.action}',x.id,metadata={'decision':decision})
    return JsonResponse({'ok':True,'status':x.status})

@require_http_methods(['GET'])
def security_center(request):
    denied=require_permission(request,'roles.view')
    if denied:return denied
    c=_active_company(request); m=_membership(request,c)
    sub=getattr(c,'subscription',None) if c else None
    used_users=CompanyMembership.objects.filter(company=c,status__in=['ACTIVE','INVITED']).count() if c else 0
    return JsonResponse({'company':{'id':c.id,'name':c.name,'code':c.code} if c else None,'membership':{'role':m.role if m else None,'permissions':sorted(permissions_for(request))},'security':{'tenant_isolation':True,'branch_isolation':True,'server_side_rbac':True,'audit_trail':True,'approval_workflow':True,'custom_roles':True},'subscription':{'plan':sub.plan.name if sub else None,'status':sub.status if sub else None,'user_limit':sub.plan.user_limit if sub else c.max_users if c else 0,'users_used':used_users,'vehicle_limit':sub.plan.vehicle_limit if sub else c.max_vehicles if c else 0}})
