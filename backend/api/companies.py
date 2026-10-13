import hashlib, json, secrets
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from core.models import Company, CompanyMembership, CompanyInvitation, UserProfile, AuditLog, Organization, OrganizationMembership, Branch, BranchMembership, CompanyRole

ROLES = {k for k,_ in CompanyMembership.ROLE_CHOICES}
ADMIN_ROLES = {CompanyMembership.ROLE_DIRECTOR, CompanyMembership.ROLE_MANAGER}
ROLE_PERMISSIONS = {
    'DIRECTOR': ['dashboard.view','fleet.view','fleet.manage','drivers.view','drivers.manage','trips.view','trips.manage','routes.manage','fuel.view','fuel.manage','warehouse.view','warehouse.manage','finance.view','finance.manage','maintenance.view','maintenance.manage','team.view','team.manage','company.manage','audit.view'],
    'MANAGER': ['dashboard.view','fleet.view','fleet.manage','drivers.view','drivers.manage','trips.view','trips.manage','routes.manage','fuel.view','fuel.manage','warehouse.view','warehouse.manage','maintenance.view','maintenance.manage','team.view'],
    'ACCOUNTANT': ['dashboard.view','finance.view','finance.manage','fuel.view','warehouse.view'],
    'WAREHOUSE': ['dashboard.view','warehouse.view','warehouse.manage'],
    'DISPATCHER': ['dashboard.view','fleet.view','drivers.view','trips.view','trips.manage','routes.manage'],
    'DRIVER': ['dashboard.view','trips.view'],
    'VIEWER': ['dashboard.view','fleet.view','drivers.view','trips.view','warehouse.view','finance.view','maintenance.view'],
}

def _json(request):
    try: return json.loads(request.body or '{}')
    except json.JSONDecodeError: return None

def _profile(request):
    return UserProfile.objects.select_related('company').filter(user=request.user).first()

def _membership(request, company=None):
    if not request.user.is_authenticated: return None
    c=company or _active_company(request)
    if not c: return None
    return CompanyMembership.objects.filter(user=request.user, company=c, status=CompanyMembership.STATUS_ACTIVE).first()

def _active_company(request):
    if request.user.is_superuser or (getattr(_profile(request),'role',None)==UserProfile.ROLE_SUPER_ADMIN):
        cid=request.session.get('active_company_id') or request.session.get('super_active_company_id')
        return Company.objects.filter(pk=cid, is_active=True).first() if cid else None
    cid=request.session.get('active_company_id')
    if cid:
        c=Company.objects.filter(pk=cid,is_active=True,status='ACTIVE').first()
        if c and CompanyMembership.objects.filter(user=request.user,company=c,status='ACTIVE').exists(): return c
    p=_profile(request)
    if p and p.company_id and CompanyMembership.objects.filter(user=request.user,company_id=p.company_id,status='ACTIVE').exists():
        return p.company
    return None

def _is_super(request):
    return request.user.is_superuser or getattr(_profile(request),'role',None)==UserProfile.ROLE_SUPER_ADMIN

def _can_company_admin(request, company=None):
    if _is_super(request): return True
    m=_membership(request, company)
    return bool(m and m.role in ADMIN_ROLES)

def _serialize_membership(m):
    return {'id':m.id,'user_id':m.user_id,'username':m.user.username,'full_name':getattr(m.user,'profile',None).full_name if hasattr(m.user,'profile') else (m.user.get_full_name() or m.user.username),'email':m.user.email,'role':m.role,'role_label':dict(CompanyMembership.ROLE_CHOICES).get(m.role,m.role),'status':m.status,'is_default':m.is_default,'permissions':m.permissions or {},'custom_role_id':m.custom_role_id,'custom_role_name':m.custom_role.name if m.custom_role_id else None}

def _serialize_company(c, membership=None):
    return {'id':c.id,'name':c.name,'slug':c.slug,'code':c.code,'legal_name':c.legal_name,'tin':c.tin,'phone':c.phone,'email':c.email,'address':c.address,'currency':c.currency,'timezone':c.timezone_name,'status':c.status,'is_active':c.is_active,'industry':c.industry,'max_users':c.max_users,'max_vehicles':c.max_vehicles,'organization_id':c.organization_id,'organization_name':c.organization.name if c.organization_id else None,'default_branch_id':c.default_branch_id,'membership':_serialize_membership(membership) if membership else None}

@require_http_methods(['GET'])
def context(request):
    if not request.user.is_authenticated: return JsonResponse({'error':'Autentifikatsiya talab qilinadi'},status=401)
    memberships=list(CompanyMembership.objects.filter(user=request.user,status=CompanyMembership.STATUS_ACTIVE).select_related('company','user__profile').order_by('-is_default','company__name'))
    if _is_super(request):
        companies=list(Company.objects.filter(is_active=True,status='ACTIVE').order_by('name'))
        company_items=[_serialize_company(c,None) | {'membership':{'role':'SUPER_ADMIN','role_label':'Super Admin','status':'ACTIVE'}} for c in companies]
    else:
        company_items=[_serialize_company(m.company,m) for m in memberships]
    active=_active_company(request)
    return JsonResponse({'active_company':_serialize_company(active,_membership(request,active)) if active else None,'companies':company_items,'is_super':_is_super(request),'roles':dict(CompanyMembership.ROLE_CHOICES),'permission_catalog':sorted(set(x for xs in ROLE_PERMISSIONS.values() for x in xs))})

@csrf_protect
@require_http_methods(['POST'])
def switch(request):
    if not request.user.is_authenticated: return JsonResponse({'error':'Autentifikatsiya talab qilinadi'},status=401)
    data=_json(request) or {}; cid=data.get('company_id')
    c=Company.objects.filter(pk=cid,is_active=True,status='ACTIVE').first()
    if not c: return JsonResponse({'error':'Kompaniya topilmadi yoki faol emas'},status=404)
    if not _is_super(request) and not CompanyMembership.objects.filter(user=request.user,company=c,status='ACTIVE').exists(): return JsonResponse({'error':'Ushbu kompaniyaga kirish huquqi yo‘q'},status=403)
    request.session['active_company_id']=c.id; request.session['active_org_id']=c.organization_id if c.organization_id else request.session.get('active_org_id'); request.session['active_branch_id']=c.default_branch_id; request.session.modified=True
    m=_membership(request,c)
    AuditLog.objects.create(company=c,user=request.user,action='SWITCH_COMPANY',model_name='Company',object_id=str(c.id),description=f'Faol kompaniya almashtirildi: {c.name}')
    return JsonResponse({'ok':True,'active_company':_serialize_company(c,m)})

@csrf_protect
@require_http_methods(['POST'])
def create_company(request):
    if not request.user.is_authenticated: return JsonResponse({'error':'Autentifikatsiya talab qilinadi'},status=401)
    data=_json(request) or {}; name=str(data.get('name','')).strip()
    if not name: return JsonResponse({'error':'Kompaniya nomi majburiy'},status=400)
    org=None
    oid=request.session.get('active_org_id')
    if oid: org=Organization.objects.filter(pk=oid,status='ACTIVE').first()
    if not org:
        org_m=OrganizationMembership.objects.filter(user=request.user,status='ACTIVE').select_related('organization').order_by('-is_default','organization__name').first()
        org=org_m.organization if org_m else None
    if org and not (_is_super(request) or OrganizationMembership.objects.filter(user=request.user,organization=org,status='ACTIVE',role__in=['OWNER','ADMIN']).exists()):
        return JsonResponse({'error':'Organization ichida kompaniya yaratish uchun admin huquqi kerak'},status=403)
    with transaction.atomic():
        if not org:
            org=Organization.objects.create(name=name,slug=f"{slugify(name) or 'organization'}-{request.user.id}",code=f"ORG-{Organization.objects.count()+1:06d}",legal_name=str(data.get('legal_name',name)).strip(),email=str(data.get('email',request.user.email)).strip())
            OrganizationMembership.objects.create(user=request.user,organization=org,role='OWNER',status='ACTIVE',is_default=True)
        if org.companies.filter(is_active=True).count() >= org.max_companies and not _is_super(request):
            return JsonResponse({'error':'Organization kompaniya limiti to‘ldi'},status=409)
        c=Company.objects.create(organization=org,name=name,legal_name=str(data.get('legal_name',name)).strip(),tin=str(data.get('tin','')).strip(),phone=str(data.get('phone','')).strip(),email=str(data.get('email',request.user.email)).strip(),industry=str(data.get('industry','')).strip(),address=str(data.get('address','')).strip(),currency=str(data.get('currency','UZS')).upper())
        m=CompanyMembership.objects.create(user=request.user,company=c,role=CompanyMembership.ROLE_DIRECTOR,status='ACTIVE',is_default=False,permissions={})
        b=Branch.objects.create(company=c,name='Bosh filial',code='HQ',address=c.address,phone=c.phone,is_headquarters=True)
        BranchMembership.objects.create(user=request.user,branch=b,role=BranchMembership.ROLE_MANAGER,status=BranchMembership.STATUS_ACTIVE,is_default=True)
        c.default_branch=b; c.save(update_fields=['default_branch'])
        request.session['active_company_id']=c.id; request.session['active_org_id']=org.id; request.session.modified=True
        AuditLog.objects.create(company=c,user=request.user,action='CREATE',model_name='Company',object_id=str(c.id),description=f'Yangi kompaniya yaratildi: {c.name}')
    return JsonResponse({'ok':True,'company':_serialize_company(c,m)},status=201)

@csrf_protect
@require_http_methods(['PATCH'])
def update_company(request):
    if not request.user.is_authenticated: return JsonResponse({'error':'Autentifikatsiya talab qilinadi'},status=401)
    c=_active_company(request)
    if not c or not _can_company_admin(request,c): return JsonResponse({'error':'Ruxsat yo‘q'},status=403)
    data=_json(request) or {}; allowed={'name','legal_name','tin','phone','email','address','industry','currency','website','description','timezone_name','max_users','max_vehicles'}
    for k,v in data.items():
        if k in allowed and hasattr(c,k): setattr(c,k,v)
    c.save(); AuditLog.objects.create(company=c,user=request.user,action='UPDATE',model_name='Company',object_id=str(c.id),description='Kompaniya sozlamalari yangilandi')
    return JsonResponse({'ok':True,'company':_serialize_company(c,_membership(request,c))})

@require_http_methods(['GET'])
def members(request):
    if not request.user.is_authenticated: return JsonResponse({'error':'Autentifikatsiya talab qilinadi'},status=401)
    c=_active_company(request)
    if not c: return JsonResponse({'results':[],'count':0})
    qs=CompanyMembership.objects.filter(company=c,status__in=['ACTIVE','SUSPENDED','INVITED']).select_related('user','user__profile','custom_role').order_by('role','user__username')
    return JsonResponse({'company':_serialize_company(c,_membership(request,c)),'count':qs.count(),'results':[_serialize_membership(m) for m in qs],'can_manage':_can_company_admin(request,c)})

@csrf_protect
@require_http_methods(['POST'])
def invite(request):
    if not request.user.is_authenticated: return JsonResponse({'error':'Autentifikatsiya talab qilinadi'},status=401)
    c=_active_company(request)
    if not c or not _can_company_admin(request,c): return JsonResponse({'error':'Ruxsat yo‘q'},status=403)
    data=_json(request) or {}; email=str(data.get('email','')).strip().lower(); role=str(data.get('role','VIEWER')).upper()
    if not email or '@' not in email: return JsonResponse({'error':'Email noto‘g‘ri'},status=400)
    if role not in ROLES: return JsonResponse({'error':'Rol noto‘g‘ri'},status=400)
    if CompanyMembership.objects.filter(company=c,user__email__iexact=email,status__in=['ACTIVE','SUSPENDED']).exists(): return JsonResponse({'error':'Bu foydalanuvchi kompaniyada allaqachon mavjud'},status=409)
    if c.memberships.filter(status='ACTIVE').count() >= c.max_users: return JsonResponse({'error':'Tarifdagi foydalanuvchi limiti to‘ldi'},status=409)
    raw=secrets.token_urlsafe(32); inv=CompanyInvitation.objects.create(company=c,email=email,role=role,token_hash=hashlib.sha256(raw.encode()).hexdigest(),invited_by=request.user,expires_at=timezone.now()+timedelta(days=7))
    return JsonResponse({'ok':True,'id':inv.id,'expires_at':inv.expires_at.isoformat(),'invite_token':raw,'invite_url':f'/invite/{raw}','message':'Taklif yaratildi. Invite linkni foydalanuvchiga yuboring.'},status=201)

@csrf_protect
@require_http_methods(['POST'])
def accept_invitation(request):
    if not request.user.is_authenticated: return JsonResponse({'error':'Avval tizimga kiring'},status=401)
    data=_json(request) or {}; raw=str(data.get('token','')).strip()
    if not raw: return JsonResponse({'error':'Token majburiy'},status=400)
    inv=CompanyInvitation.objects.select_related('company').filter(token_hash=hashlib.sha256(raw.encode()).hexdigest()).first()
    if not inv or not inv.is_usable: return JsonResponse({'error':'Taklif yaroqsiz yoki muddati tugagan'},status=400)
    if request.user.email.lower()!=inv.email.lower(): return JsonResponse({'error':'Taklif boshqa email uchun berilgan'},status=403)
    with transaction.atomic():
        m,_=CompanyMembership.objects.update_or_create(user=request.user,company=inv.company,defaults={'role':inv.role,'status':'ACTIVE','is_default':False,'permissions':{}})
        inv.accepted_at=timezone.now(); inv.save(update_fields=['accepted_at'])
        request.session['active_company_id']=inv.company_id; request.session['active_org_id']=inv.company.organization_id; request.session.modified=True
        AuditLog.objects.create(company=inv.company,user=request.user,action='ACCEPT_INVITE',model_name='CompanyMembership',object_id=str(m.id),description='Kompaniya taklifi qabul qilindi')
    return JsonResponse({'ok':True,'company':_serialize_company(inv.company,m)})

@csrf_protect
@require_http_methods(['PATCH'])
def member_update(request, pk):
    if not request.user.is_authenticated: return JsonResponse({'error':'Autentifikatsiya talab qilinadi'},status=401)
    c=_active_company(request)
    if not c or not _can_company_admin(request,c): return JsonResponse({'error':'Ruxsat yo‘q'},status=403)
    m=CompanyMembership.objects.filter(company=c,pk=pk).select_related('user').first()
    if not m:return JsonResponse({'error':'A’zo topilmadi'},status=404)
    data=_json(request) or {}; role=str(data.get('role',m.role)).upper(); status=str(data.get('status',m.status)).upper()
    if role not in ROLES or status not in {'ACTIVE','SUSPENDED','REMOVED'}: return JsonResponse({'error':'Rol yoki status noto‘g‘ri'},status=400)
    actor=_membership(request,c)
    if m.role=='DIRECTOR' and role!='DIRECTOR' and CompanyMembership.objects.filter(company=c,role='DIRECTOR',status='ACTIVE').count()<=1:return JsonResponse({'error':'Oxirgi direktor rolini olib tashlab bo‘lmaydi'},status=409)
    custom_role_id=data.get('custom_role_id',m.custom_role_id)
    if custom_role_id:
        if not CompanyRole.objects.filter(pk=custom_role_id,company=c).exists(): return JsonResponse({'error':'Custom role topilmadi'},status=400)
    m.role=role;m.status=status;m.permissions=data.get('permissions',m.permissions or {});m.custom_role_id=custom_role_id;m.save()
    AuditLog.objects.create(company=c,user=request.user,action='UPDATE_MEMBER',model_name='CompanyMembership',object_id=str(m.id),description=f'A’zo yangilandi: {m.user.username} → {role}/{status}')
    return JsonResponse({'ok':True,'member':_serialize_membership(m)})
