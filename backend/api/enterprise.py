import json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from core.models import Organization, OrganizationMembership, Company, Branch, CompanyMembership, BranchMembership, AuditLog, UserProfile

ORG_ADMIN = {OrganizationMembership.ROLE_OWNER, OrganizationMembership.ROLE_ADMIN}

def _json(request):
    try: return json.loads(request.body or '{}')
    except json.JSONDecodeError: return None

def _is_super(request):
    p=UserProfile.objects.filter(user=request.user).first()
    return request.user.is_superuser or bool(p and p.role==UserProfile.ROLE_SUPER_ADMIN)

def _org_membership(request, org=None):
    if not request.user.is_authenticated: return None
    if org is None:
        oid=request.session.get('active_org_id')
        org=Organization.objects.filter(pk=oid,status='ACTIVE').first() if oid else None
    if not org: return None
    return OrganizationMembership.objects.filter(user=request.user,organization=org,status='ACTIVE').first()

def _active_org(request):
    if _is_super(request):
        oid=request.session.get('active_org_id')
        if oid: return Organization.objects.filter(pk=oid,status='ACTIVE').first()
        cid=request.session.get('active_company_id')
        c=Company.objects.filter(pk=cid).select_related('organization').first() if cid else None
        return c.organization if c and c.organization_id else None
    m=_org_membership(request)
    if m: return m.organization
    cid=request.session.get('active_company_id')
    c=Company.objects.filter(pk=cid).select_related('organization').first() if cid else None
    return c.organization if c and c.organization_id and (OrganizationMembership.objects.filter(user=request.user,organization_id=c.organization_id,status='ACTIVE').exists() or CompanyMembership.objects.filter(user=request.user,company=c,status='ACTIVE',role=CompanyMembership.ROLE_DIRECTOR).exists()) else None

def _org_json(o):
    return {'id':o.id,'name':o.name,'slug':o.slug,'code':o.code,'legal_name':o.legal_name,'tin':o.tin,'email':o.email,'phone':o.phone,'status':o.status,'max_companies':o.max_companies,'companies_count':o.companies.filter(is_active=True).count()}

def _branch_json(b):
    return {'id':b.id,'name':b.name,'code':b.code,'address':b.address,'phone':b.phone,'manager_name':b.manager_name,'is_active':b.is_active,'is_headquarters':b.is_headquarters}

@login_required
@require_http_methods(['GET'])
def context(request):
    ms=OrganizationMembership.objects.filter(user=request.user,status='ACTIVE').select_related('organization').order_by('-is_default','organization__name')
    orgs=[_org_json(m.organization)|{'role':m.role,'is_default':m.is_default} for m in ms]
    if _is_super(request):
        orgs=[_org_json(o)|{'role':'SUPER_ADMIN','is_default':False} for o in Organization.objects.filter(status='ACTIVE').order_by('name')]
    active=_active_org(request)
    branches=list(Branch.objects.filter(company__organization=active,is_active=True).select_related('company').order_by('company__name','-is_headquarters','name')) if active else []
    if active and not _is_super(request):
        org_member=_org_membership(request,active)
        if not (org_member and org_member.role in ORG_ADMIN):
            allowed_ids=BranchMembership.objects.filter(user=request.user,status='ACTIVE',branch__company__organization=active).values_list('branch_id',flat=True)
            branches=[b for b in branches if b.id in set(allowed_ids)]
    active_branch_id=request.session.get('active_branch_id')
    active_branch=next((b for b in branches if b.id==active_branch_id), None)
    if not active_branch and active:
        active_branch=Branch.objects.filter(company_id=request.session.get('active_company_id'),is_active=True).order_by('-is_headquarters','name').first()
        if active_branch: request.session['active_branch_id']=active_branch.id; request.session.modified=True
    return JsonResponse({'active_organization':_org_json(active) if active else None,'organizations':orgs,'branches':[_branch_json(b)|{'company_id':b.company_id,'company_name':b.company.name} for b in branches],'active_branch':(_branch_json(active_branch)|{'company_id':active_branch.company_id,'company_name':active_branch.company.name} if active_branch else None),'is_super':_is_super(request)})

@login_required
@csrf_protect
@require_http_methods(['POST'])
def switch_organization(request):
    data=_json(request) or {}; oid=data.get('organization_id')
    org=Organization.objects.filter(pk=oid,status='ACTIVE').first()
    if not org:return JsonResponse({'error':'Organization topilmadi'},status=404)
    if not _is_super(request) and not OrganizationMembership.objects.filter(user=request.user,organization=org,status='ACTIVE').exists(): return JsonResponse({'error':'Organizationga kirish huquqi yo‘q'},status=403)
    request.session['active_org_id']=org.id
    companies=Company.objects.filter(organization=org,is_active=True,status='ACTIVE').order_by('name')
    if companies.exists():
        current=request.session.get('active_company_id')
        if not Company.objects.filter(pk=current,organization=org,is_active=True,status='ACTIVE').exists(): request.session['active_company_id']=companies.first().id
    request.session.modified=True
    AuditLog.objects.create(company=companies.first() if companies.exists() else None,user=request.user,action='SWITCH_ORG',model_name='Organization',object_id=str(org.id),description=f'Organization almashtirildi: {org.name}') if companies.exists() else None
    return JsonResponse({'ok':True,'organization':_org_json(org)})

@login_required
@csrf_protect
@require_http_methods(['POST'])
def create_organization(request):
    data=_json(request) or {}; name=str(data.get('name','')).strip()
    if not name:return JsonResponse({'error':'Organization nomi majburiy'},status=400)
    with transaction.atomic():
        base=slugify(name) or 'organization'
        slug=base; n=1
        while Organization.objects.filter(slug=slug).exists(): n+=1; slug=f'{base}-{n}'
        o=Organization.objects.create(name=name,slug=slug,code=f'ORG-{Organization.objects.count()+1:06d}',legal_name=str(data.get('legal_name',name)).strip(),tin=str(data.get('tin','')).strip(),email=str(data.get('email',request.user.email)).strip(),phone=str(data.get('phone','')).strip())
        OrganizationMembership.objects.create(user=request.user,organization=o,role=OrganizationMembership.ROLE_OWNER,status='ACTIVE',is_default=True)
        c=Company.objects.create(organization=o,name=name,legal_name=o.legal_name,tin=o.tin,email=o.email,phone=o.phone,slug=f'{slug}-hq',code=f'AP-{Company.objects.count()+1:06d}')
        CompanyMembership.objects.create(user=request.user,company=c,role=CompanyMembership.ROLE_DIRECTOR,status='ACTIVE',is_default=True)
        b=Branch.objects.create(company=c,name='Bosh filial',code='HQ',is_headquarters=True,address=c.address,phone=c.phone)
        BranchMembership.objects.create(user=request.user,branch=b,role=BranchMembership.ROLE_MANAGER,status=BranchMembership.STATUS_ACTIVE,is_default=True)
        c.default_branch=b; c.save(update_fields=['default_branch'])
        request.session['active_org_id']=o.id; request.session['active_company_id']=c.id; request.session.modified=True
        AuditLog.objects.create(company=c,user=request.user,action='CREATE_ORG',model_name='Organization',object_id=str(o.id),description=f'Yangi organization yaratildi: {o.name}')
    return JsonResponse({'ok':True,'organization':_org_json(o),'company_id':c.id},status=201)

@login_required
@require_http_methods(['GET'])
def branches(request):
    org=_active_org(request)
    if not org:return JsonResponse({'results':[],'count':0})
    qs=Branch.objects.filter(company__organization=org).select_related('company').order_by('company__name','-is_headquarters','name')
    return JsonResponse({'count':qs.count(),'results':[_branch_json(b)|{'company_id':b.company_id,'company_name':b.company.name} for b in qs]})

@login_required
@csrf_protect
@require_http_methods(['POST'])
def branch_create(request):
    org=_active_org(request); m=_org_membership(request,org)
    data=_json(request) or {}; cid=data.get('company_id') or request.session.get('active_company_id'); name=str(data.get('name','')).strip(); code=str(data.get('code','')).strip().upper()
    c=Company.objects.filter(pk=cid,is_active=True).first()
    # Company directors must be able to create branches for their own company even
    # when the account was registered before organization membership was introduced.
    is_company_admin=bool(c and CompanyMembership.objects.filter(user=request.user,company=c,status='ACTIVE',role=CompanyMembership.ROLE_DIRECTOR).exists())
    if not org or not (_is_super(request) or (m and m.role in ORG_ADMIN) or is_company_admin):return JsonResponse({'error':'Ruxsat yo‘q'},status=403)
    if c and c.organization_id and c.organization_id != org.id and not _is_super(request):return JsonResponse({'error':'Boshqa tashkilot kompaniyasiga filial qo‘shib bo‘lmaydi'},status=403)
    if not c and org: c=Company.objects.filter(organization=org,is_active=True).first()
    if not c:return JsonResponse({'error':'Kompaniya topilmadi'},status=404)
    if not name or not code:return JsonResponse({'error':'Filial nomi va kodi majburiy'},status=400)
    if Branch.objects.filter(company=c,code=code).exists():return JsonResponse({'error':'Filial kodi band'},status=409)
    b=Branch.objects.create(company=c,name=name,code=code,address=str(data.get('address','')),phone=str(data.get('phone','')),manager_name=str(data.get('manager_name','')),is_headquarters=bool(data.get('is_headquarters',False)))
    BranchMembership.objects.get_or_create(user=request.user,branch=b,defaults={'role':BranchMembership.ROLE_MANAGER,'status':BranchMembership.STATUS_ACTIVE,'is_default':b.is_headquarters})
    if b.is_headquarters or not c.default_branch_id:c.default_branch=b;c.save(update_fields=['default_branch'])
    AuditLog.objects.create(company=c,user=request.user,action='CREATE',model_name='Branch',object_id=str(b.id),description=f'Filial yaratildi: {b.name}')
    return JsonResponse({'ok':True,'branch':_branch_json(b)},status=201)

@login_required
@csrf_protect
@require_http_methods(['POST'])
def switch_branch(request):
    data=_json(request) or {}; bid=data.get('branch_id')
    b=Branch.objects.filter(pk=bid,is_active=True,company__status='ACTIVE',company__is_active=True).select_related('company','company__organization').first()
    if not b:return JsonResponse({'error':'Filial topilmadi'},status=404)
    if not _is_super(request):
        cm=CompanyMembership.objects.filter(user=request.user,company=b.company,status='ACTIVE').first()
        org_allowed=OrganizationMembership.objects.filter(user=request.user,organization=b.company.organization,status='ACTIVE').exists()
        allowed=bool(cm and (org_allowed or cm.role==CompanyMembership.ROLE_DIRECTOR))
        branch_allowed=BranchMembership.objects.filter(user=request.user,branch=b,status='ACTIVE').exists() or bool(cm and cm.role==CompanyMembership.ROLE_DIRECTOR)
        if not (allowed and branch_allowed):
            return JsonResponse({'error':'Filialga kirish huquqi yo‘q'},status=403)
    request.session['active_org_id']=b.company.organization_id
    request.session['active_company_id']=b.company_id
    request.session['active_branch_id']=b.id
    request.session.modified=True
    AuditLog.objects.create(company=b.company,user=request.user,action='SWITCH_BRANCH',model_name='Branch',object_id=str(b.id),description=f'Filial almashtirildi: {b.name}')
    return JsonResponse({'ok':True,'branch':_branch_json(b)|{'company_id':b.company_id,'company_name':b.company.name}})

@login_required
@require_http_methods(['GET'])
def branch_members(request, branch_id):
    b=Branch.objects.filter(pk=branch_id,company__organization=_active_org(request)).first()
    if not b:return JsonResponse({'error':'Filial topilmadi'},status=404)
    if not _is_super(request) and not CompanyMembership.objects.filter(user=request.user,company=b.company,status='ACTIVE').exists():return JsonResponse({'error':'Ruxsat yo‘q'},status=403)
    qs=BranchMembership.objects.filter(branch=b,status__in=['ACTIVE','SUSPENDED']).select_related('user').order_by('role','user__username')
    return JsonResponse({'count':qs.count(),'results':[{'id':m.id,'user_id':m.user_id,'username':m.user.username,'email':m.user.email,'role':m.role,'status':m.status,'is_default':m.is_default,'permissions':m.permissions} for m in qs]})

@login_required
@csrf_protect
@require_http_methods(['POST'])
def branch_member_upsert(request, branch_id):
    b=Branch.objects.filter(pk=branch_id,company__organization=_active_org(request),is_active=True).select_related('company').first()
    if not b:return JsonResponse({'error':'Filial topilmadi'},status=404)
    if not _is_super(request) and not _can_manage_branch(request,b):return JsonResponse({'error':'Ruxsat yo‘q'},status=403)
    data=_json(request) or {}; uid=data.get('user_id'); role=str(data.get('role','VIEWER')).upper()
    if role not in {x[0] for x in BranchMembership.ROLE_CHOICES}:return JsonResponse({'error':'Filial roli noto‘g‘ri'},status=400)
    cm=CompanyMembership.objects.filter(user_id=uid,company=b.company,status='ACTIVE').first()
    if not cm:return JsonResponse({'error':'Foydalanuvchi avval kompaniya a’zosi bo‘lishi kerak'},status=400)
    m,_=BranchMembership.objects.update_or_create(user_id=uid,branch=b,defaults={'role':role,'status':'ACTIVE','permissions':data.get('permissions',{}),'is_default':bool(data.get('is_default',False))})
    AuditLog.objects.create(company=b.company,user=request.user,action='BRANCH_MEMBER',model_name='BranchMembership',object_id=str(m.id),description=f'Filial a’zoligi yangilandi: {m.user.username} → {role}')
    return JsonResponse({'ok':True,'id':m.id,'user_id':m.user_id,'role':m.role,'status':m.status})


def _can_manage_branch(request, branch):
    if _is_super(request): return True
    cm=CompanyMembership.objects.filter(user=request.user,company=branch.company,status='ACTIVE').first()
    if cm and cm.role in {CompanyMembership.ROLE_DIRECTOR,CompanyMembership.ROLE_MANAGER}: return True
    bm=BranchMembership.objects.filter(user=request.user,branch=branch,status='ACTIVE',role=BranchMembership.ROLE_MANAGER).exists()
    return bm

@login_required
@require_http_methods(['GET'])
def control_plane(request):
    """Enterprise Control Plane: organization/company/branch/subscription health in one tenant-aware response."""
    org=_active_org(request)
    if not org:
        return JsonResponse({'error':'Faol tashkilot topilmadi','error_ru':'Активная организация не найдена'},status=404)
    if not _is_super(request) and not _org_membership(request,org):
        return JsonResponse({'error':'Tashkilotga kirish huquqi yo‘q','error_ru':'Нет доступа к организации'},status=403)
    from core.models import Subscription, SubscriptionPlan, Vehicle, UserProfile
    companies=Company.objects.filter(organization=org).prefetch_related('branches','memberships').order_by('name')
    company_rows=[]
    for c in companies:
        sub=Subscription.objects.filter(company=c).select_related('plan').first()
        users=CompanyMembership.objects.filter(company=c,status='ACTIVE').count()
        vehicles=Vehicle.objects.filter(company=c,active=True).count()
        branches=Branch.objects.filter(company=c,is_active=True).count()
        company_rows.append({'id':c.id,'name':c.name,'code':c.code,'status':c.status,'is_active':c.is_active,'users':users,'user_limit':sub.plan.user_limit if sub else c.max_users,'vehicles':vehicles,'vehicle_limit':sub.plan.vehicle_limit if sub else c.max_vehicles,'branches':branches,'plan':sub.plan.name if sub else None,'plan_code':sub.plan.code if sub else None,'subscription_status':sub.status if sub else None,'trial_ends_at':c.trial_ends_at.isoformat() if c.trial_ends_at else None})
    plans=list(SubscriptionPlan.objects.filter(is_active=True).values('id','name','code','price_monthly','price_yearly','user_limit','vehicle_limit','features').order_by('sort_order','price_monthly'))
    return JsonResponse({'organization':{'id':org.id,'name':org.name,'code':org.code,'status':org.status,'max_companies':org.max_companies,'companies_used':len(company_rows)},'companies':company_rows,'plans':plans,'summary':{'active_companies':sum(1 for x in company_rows if x['is_active']),'branches':sum(x['branches'] for x in company_rows),'users':sum(x['users'] for x in company_rows),'vehicles':sum(x['vehicles'] for x in company_rows)}})
