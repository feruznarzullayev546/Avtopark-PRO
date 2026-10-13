import hashlib, json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
from core.models import Organization, Company, UserProfile, Subscription, SubscriptionPlan, Invoice, Payment, FeatureFlag, UsageMetric, PlatformSecurityEvent, PlatformSession

def _super(request):
    p=UserProfile.objects.filter(user=request.user).first()
    return request.user.is_superuser or bool(p and p.role==UserProfile.ROLE_SUPER_ADMIN)
def _ip(request):
    return request.META.get('HTTP_X_FORWARDED_FOR','').split(',')[0].strip() or request.META.get('REMOTE_ADDR')
def _event(request,event_type,severity='INFO',org=None,company=None,metadata=None):
    return PlatformSecurityEvent.objects.create(event_type=event_type,severity=severity,organization=org,company=company,user=request.user,ip_address=_ip(request),user_agent=request.META.get('HTTP_USER_AGENT','')[:4000],metadata=metadata or {})

def _deny(request): return JsonResponse({'error':'Super Admin huquqi talab qilinadi','error_ru':'Требуются права Super Admin'},status=403)

@login_required
@require_http_methods(['GET'])
def overview(request):
    if not _super(request): return _deny(request)
    companies=Company.objects.select_related('organization').all()
    subs=Subscription.objects.select_related('plan','company').all()
    invoices=Invoice.objects.select_related('company').all()
    active_sessions=PlatformSession.objects.filter(is_active=True).count()
    rows=[]
    for c in companies:
        s=next((x for x in subs if x.company_id==c.id),None)
        rows.append({'id':c.id,'organization_id':c.organization_id,'organization':c.organization.name if c.organization_id else None,'name':c.name,'code':c.code,'status':c.status,'users':c.memberships.filter(status='ACTIVE').count(),'vehicles':c.vehicles.filter(active=True).count(),'branches':c.branches.filter(is_active=True).count(),'plan':s.plan.name if s else None,'plan_code':s.plan.code if s else None,'subscription_status':s.status if s else None,'period_end':s.current_period_end.isoformat() if s and s.current_period_end else None})
    plan_rows=[{'id':p.id,'name':p.name,'code':p.code,'monthly':str(p.price_monthly),'yearly':str(p.price_yearly),'user_limit':p.user_limit,'vehicle_limit':p.vehicle_limit,'features':p.features,'active':p.is_active} for p in SubscriptionPlan.objects.order_by('sort_order','price_monthly')]
    return JsonResponse({'summary':{'organizations':Organization.objects.count(),'companies':companies.count(),'active_companies':companies.filter(is_active=True).count(),'users':sum(x['users'] for x in rows),'vehicles':sum(x['vehicles'] for x in rows),'active_sessions':active_sessions,'pending_invoices':invoices.filter(status='PENDING').count(),'past_due':subs.filter(status='PAST_DUE').count()},'companies':rows,'plans':plan_rows})

@login_required
@csrf_protect
@require_http_methods(['POST'])
def company_status(request,pk):
    if not _super(request): return _deny(request)
    data=json.loads(request.body or '{}'); status=str(data.get('status','ACTIVE')).upper()
    if status not in {'ACTIVE','SUSPENDED','ARCHIVED'}: return JsonResponse({'error':'Noto‘g‘ri status'},status=400)
    c=Company.objects.filter(pk=pk).first()
    if not c:return JsonResponse({'error':'Kompaniya topilmadi'},status=404)
    c.status=status;c.is_active=status=='ACTIVE';c.save(update_fields=['status','is_active'])
    _event(request,'COMPANY_STATUS_CHANGED','WARNING' if status!='ACTIVE' else 'INFO',c.organization,c,{'status':status})
    return JsonResponse({'ok':True,'status':status})

@login_required
@csrf_protect
@require_http_methods(['POST'])
def org_status(request,pk):
    if not _super(request): return _deny(request)
    data=json.loads(request.body or '{}'); status=str(data.get('status','ACTIVE')).upper()
    if status not in {'ACTIVE','SUSPENDED','ARCHIVED'}: return JsonResponse({'error':'Noto‘g‘ri status'},status=400)
    o=Organization.objects.filter(pk=pk).first()
    if not o:return JsonResponse({'error':'Organization topilmadi'},status=404)
    o.status=status;o.save(update_fields=['status'])
    if status!='ACTIVE': Company.objects.filter(organization=o).update(status='SUSPENDED',is_active=False)
    _event(request,'ORG_STATUS_CHANGED','CRITICAL' if status!='ACTIVE' else 'INFO',o,None,{'status':status})
    return JsonResponse({'ok':True,'status':status})

@login_required
@require_http_methods(['GET'])
def security_events(request):
    if not _super(request): return _deny(request)
    qs=PlatformSecurityEvent.objects.select_related('organization','company','user')[:250]
    return JsonResponse({'results':[{'id':e.id,'type':e.event_type,'severity':e.severity,'organization':e.organization.name if e.organization_id else None,'company':e.company.name if e.company_id else None,'user':e.user.username if e.user_id else None,'ip':e.ip_address,'created_at':e.created_at.isoformat(),'metadata':e.metadata} for e in qs]})

@login_required
@require_http_methods(['GET'])
def sessions(request):
    if not _super(request): return _deny(request)
    qs=PlatformSession.objects.select_related('user').all()[:250]
    return JsonResponse({'results':[{'id':s.id,'user':s.user.username,'device':s.device_label,'ip':s.ip_address,'active':s.is_active,'last_seen':s.last_seen_at.isoformat(),'created_at':s.created_at.isoformat()} for s in qs]})

@login_required
@csrf_protect
@require_http_methods(['POST'])
def revoke_session(request,pk):
    if not _super(request): return _deny(request)
    s=PlatformSession.objects.filter(pk=pk).first()
    if not s:return JsonResponse({'error':'Session topilmadi'},status=404)
    s.is_active=False;s.revoked_at=timezone.now();s.save(update_fields=['is_active','revoked_at','last_seen_at'])
    _event(request,'SESSION_REVOKED','WARNING',metadata={'session_id':pk,'user_id':s.user_id})
    return JsonResponse({'ok':True})

@login_required
@csrf_protect
@require_http_methods(['POST'])
def feature_flag(request):
    if not _super(request): return _deny(request)
    data=json.loads(request.body or '{}'); cid=data.get('company_id'); key=str(data.get('key','')).strip(); enabled=bool(data.get('enabled',False)); rollout=int(data.get('rollout_percent',100))
    c=Company.objects.filter(pk=cid).first()
    if not c or not key:return JsonResponse({'error':'Kompaniya va flag majburiy'},status=400)
    if rollout<0 or rollout>100:return JsonResponse({'error':'Rollout 0..100 oralig‘ida'},status=400)
    f,_=FeatureFlag.objects.update_or_create(company=c,key=key,defaults={'enabled':enabled,'rollout_percent':rollout,'config':data.get('config') or {}})
    _event(request,'FEATURE_FLAG_CHANGED','INFO',c.organization,c,{'key':key,'enabled':enabled,'rollout':rollout})
    return JsonResponse({'ok':True,'id':f.id})
