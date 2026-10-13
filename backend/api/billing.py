import json, random
from datetime import timedelta
from decimal import Decimal
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from core.models import Company, Subscription, SubscriptionPlan, Invoice, Payment, PaymentCard, FeatureFlag, UsageMetric, Notification, UserProfile
from .companies import _active_company
from .access import require_permission, audit

def _company(request): return _active_company(request)
def _super(request):
    p=UserProfile.objects.filter(user=request.user).first()
    return bool(request.user.is_superuser or (p and p.role==UserProfile.ROLE_SUPER_ADMIN))

def _serialize_sub(s):
    return {'id':s.id,'plan':s.plan.name,'plan_code':s.plan.code,'status':s.status,'billing_cycle':s.billing_cycle,'started_at':s.started_at.isoformat(),'period_start':s.current_period_start.isoformat(),'period_end':s.current_period_end.isoformat() if s.current_period_end else None,'auto_renew':s.auto_renew,'price':str(s.price())}

def _trial_notice(request,c,sub):
    if not c or not sub or sub.status!='TRIAL' or not c.trial_ends_at:return
    left=(c.trial_ends_at-timezone.localdate()).days
    if left<0:return
    # Avoid duplicates for the same company, profile and day. Notification
    # belongs to UserProfile (recipient), not directly to AUTH_USER_MODEL.
    today = timezone.localdate()
    profile = UserProfile.objects.filter(user=request.user).first()
    if not profile:
        return
    dedupe_key = f'trial-{c.id}-{today.isoformat()}-{profile.id}'
    if Notification.objects.filter(
        recipient=profile, company=c, dedupe_key=dedupe_key
    ).exists():
        return
    if left==0: text='Bepul sinov muddati bugun yakunlanadi. Xizmatlar uzluksiz davom etishi uchun tarif rejasini faollashtiring.'
    elif left==1: text='Bepul sinov muddati yakunlanishiga 1 kun qoldi. O‘zingizga mos tarifni tanlab, xizmatlarni davom ettiring.'
    else: text=f'Bepul sinov muddatingiz yakunlanishiga {left} kun qoldi. Platformadan uzluksiz foydalanish uchun tarif rejasini tanlang.'
    Notification.objects.create(recipient=profile, company=c, title='Trial eslatmasi', message=text, url='/billing', dedupe_key=dedupe_key)

def _invoice_payload(inv):
    p=inv.payments.order_by('-id').first()
    return {'id':inv.id,'number':inv.number,'issue_date':inv.issue_date,'due_date':inv.due_date,'amount':str(inv.amount),'status':inv.status,'paid_at':inv.paid_at.isoformat() if inv.paid_at else None,'payment_status':p.status if p else None,'receipt_url':p.receipt.url if p and p.receipt else None,'review_note':p.review_note if p else '', 'card':inv.assigned_card.masked_number if inv.assigned_card_id else None}

@require_http_methods(['GET'])
def overview(request):
    denied=require_permission(request,'billing.view')
    if denied:return denied
    c=_company(request); sub=Subscription.objects.filter(company=c).select_related('plan').first()
    if sub and sub.status=='TRIAL' and c.trial_ends_at and c.trial_ends_at < timezone.localdate():
        sub.status=Subscription.STATUS_EXPIRED; sub.save(update_fields=['status','updated_at'])
    _trial_notice(request,c,sub)
    plans=[dict(x,price_monthly=str(x['price_monthly']),price_yearly=str(x['price_yearly'])) for x in SubscriptionPlan.objects.filter(is_active=True).values('id','name','code','price_monthly','price_yearly','vehicle_limit','user_limit','features')]
    invoices=[_invoice_payload(x) for x in Invoice.objects.filter(company=c).prefetch_related('payments')[:50]]
    flags=list(FeatureFlag.objects.filter(company=c).values('key','enabled','rollout_percent'))
    usage={x.metric:{'value':x.value,'limit':x.limit,'period_end':x.period_end.isoformat() if x.period_end else None} for x in UsageMetric.objects.filter(company=c)}
    cards=list(PaymentCard.objects.filter(is_active=True).values('id','card_number','holder_name','bank_name','company_name'))
    pending_inv=Invoice.objects.filter(company=c,status='PENDING').select_related('assigned_card').first()
    selected=None
    if pending_inv and pending_inv.assigned_card_id:
        x=pending_inv.assigned_card; selected={'id':x.id,'card_number':x.card_number,'holder_name':x.holder_name,'bank_name':x.bank_name,'company_name':x.company_name}
    elif cards:
        selected=random.choice(cards)
    if selected:
        digits=''.join(ch for ch in selected['card_number'] if ch.isdigit()); selected['card_number']=f'{digits[:4]} **** **** {digits[-4:]}' if len(digits)>=8 else selected['card_number']
    return JsonResponse({'subscription':_serialize_sub(sub) if sub else None,'trial_ends_at':c.trial_ends_at.isoformat() if c and c.trial_ends_at else None,'plans':plans,'invoices':invoices,'features':flags,'usage':usage,'payment_card':selected})

@csrf_protect
@require_http_methods(['POST'])
def change_plan(request):
    denied=require_permission(request,'billing.manage')
    if denied:return denied
    c=_company(request); data=json.loads(request.body or '{}'); plan=SubscriptionPlan.objects.filter(code=data.get('plan_code'),is_active=True).first()
    if not plan:return JsonResponse({'error':'Tarif topilmadi'},status=404)
    cycle=data.get('billing_cycle','MONTHLY'); price=plan.price_yearly if cycle=='YEARLY' else plan.price_monthly
    with transaction.atomic():
        sub,created=Subscription.objects.select_for_update().get_or_create(company=c,defaults={'plan':plan,'status':Subscription.STATUS_TRIAL,'current_period_end':c.trial_ends_at})
        card=PaymentCard.objects.filter(is_active=True).order_by('?').first()
        # A plan request should still be recorded if the platform admin has not configured
        # a payment card yet; the invoice can be issued and the missing payment setup
        # is surfaced to the company instead of making plan selection look broken.
        inv=Invoice.objects.create(company=c,subscription=sub,assigned_card=card,number=f'INV-{timezone.now():%Y%m%d%H%M%S}-{sub.id}',due_date=timezone.localdate()+timedelta(days=3),amount=price,note=f'Plan request: {plan.code}; cycle: {cycle}')
    audit(request,'PLAN_PAYMENT_REQUEST','Invoice',f'Tarif uchun to‘lov so‘rovi: {plan.code}',inv.id,metadata={'plan':plan.code,'amount':str(price)})
    message='Tarif tanlandi. To‘lovni amalga oshirib, chekni yuklang.' if card else 'Tarif uchun hisob-faktura yaratildi, ammo platforma to‘lov kartasini hali sozlamagan. Super Admin bilan bog‘laning.'
    return JsonResponse({'ok':True,'invoice':_invoice_payload(inv),'message':message,'payment_card_configured':bool(card)},status=201)

@csrf_protect
@require_http_methods(['POST'])
def submit_receipt(request,pk):
    denied=require_permission(request,'billing.manage')
    if denied:return denied
    c=_company(request); inv=Invoice.objects.filter(pk=pk,company=c,status='PENDING').select_related('subscription').first()
    if not inv:return JsonResponse({'error':'Kutilayotgan hisob topilmadi'},status=404)
    receipt=request.FILES.get('receipt')
    if not receipt:return JsonResponse({'error':'To‘lov chekini yuklang'},status=400)
    if receipt.size>10*1024*1024:return JsonResponse({'error':'Chek hajmi 10 MB dan oshmasligi kerak'},status=400)
    allowed={'image/jpeg','image/png','image/webp','application/pdf'}
    if receipt.content_type not in allowed:return JsonResponse({'error':'JPG, PNG, WEBP yoki PDF yuklang'},status=400)
    card=inv.assigned_card
    if not card:return JsonResponse({'error':'Hozircha to‘lov kartasi sozlanmagan'},status=400)
    p=Payment.objects.create(company=c,invoice=inv,amount=inv.amount,method=Payment.METHOD_BANK,status=Payment.STATUS_PENDING,payment_card=card,receipt=receipt,payer_name=request.POST.get('payer_name',''),transaction_id=request.POST.get('transaction_id',''),note=request.POST.get('note',''))
    audit(request,'PAYMENT_RECEIPT_SUBMITTED','Payment','To‘lov cheki yuklandi',p.id,metadata={'invoice':inv.number,'card_id':card.id})
    return JsonResponse({'ok':True,'status':'PENDING','payment_id':p.id})

@require_http_methods(['GET'])
def admin_payments(request):
    if not _super(request):return JsonResponse({'error':'Super Admin huquqi talab qilinadi'},status=403)
    qs=Payment.objects.select_related('company','invoice','payment_card','reviewed_by').order_by('-id')[:250]
    rows=[]
    for p in qs:
        rows.append({'id':p.id,'company_id':p.company_id,'company':p.company.name,'invoice':p.invoice.number if p.invoice_id else None,'amount':str(p.amount),'status':p.status,'card':p.payment_card.masked_number if p.payment_card else None,'receipt_url':request.build_absolute_uri(p.receipt.url) if p.receipt else None,'created_at':p.created_at.isoformat(),'review_note':p.review_note})
    return JsonResponse({'results':rows})

@csrf_protect
@require_http_methods(['POST'])
def admin_payment_decide(request,pk):
    if not _super(request):return JsonResponse({'error':'Super Admin huquqi talab qilinadi'},status=403)
    data=json.loads(request.body or '{}'); decision=data.get('decision')
    if decision not in {'APPROVED','REJECTED'}:return JsonResponse({'error':'Noto‘g‘ri qaror'},status=400)
    with transaction.atomic():
        p=Payment.objects.select_for_update().select_related('invoice','invoice__subscription','company').filter(pk=pk,status=Payment.STATUS_PENDING).first()
        if not p:return JsonResponse({'error':'Tekshiriladigan to‘lov topilmadi'},status=404)
        p.reviewed_at=timezone.now();p.reviewed_by=request.user;p.review_note=data.get('note','')
        if decision=='APPROVED':
            p.status=Payment.STATUS_COMPLETED
            inv=p.invoice; inv.status=Invoice.STATUS_PAID;inv.paid_at=timezone.now();inv.save(update_fields=['status','paid_at'])
            sub=inv.subscription
            if sub:
                # Activate the plan requested on this invoice, not the subscription's old plan.
                # The previous implementation reloaded sub.plan_id (the old plan), so a paid
                # upgrade could be marked active while keeping the previous tariff.
                import re
                match=re.search(r'Plan request:\s*([a-zA-Z0-9_-]+)', inv.note or '')
                requested_plan=SubscriptionPlan.objects.filter(code=match.group(1),is_active=True).first() if match else None
                if requested_plan:
                    sub.plan=requested_plan
                cycle_match=re.search(r'cycle:\s*(MONTHLY|YEARLY)', inv.note or '')
                if cycle_match:
                    sub.billing_cycle=cycle_match.group(1)
                sub.status=Subscription.STATUS_ACTIVE;sub.current_period_start=timezone.localdate();sub.current_period_end=timezone.localdate()+timedelta(days=365 if sub.billing_cycle=='YEARLY' else 30);sub.save()
            msg='To‘lovingiz tasdiqlandi. Tanlangan tarif faollashtirildi.'
        else:
            p.status=Payment.STATUS_REFUNDED
            msg='To‘lov cheki tasdiqlanmadi. Iltimos, to‘g‘ri chek bilan qayta yuboring.'
        p.save(update_fields=['status','reviewed_at','reviewed_by','review_note'])
        (lambda prof: Notification.objects.create(recipient=prof,company=p.company,title='To‘lov holati',message=msg,url='/billing'))(p.company.users.filter(is_active=True).order_by('id').first()) if p.company.users.filter(is_active=True).exists() else None
    audit(request,'PAYMENT_'+decision,'Payment',f'To‘lov {decision.lower()}',p.id,company=p.company,metadata={'invoice':p.invoice.number if p.invoice_id else None})
    return JsonResponse({'ok':True,'status':p.status})

@csrf_protect
@require_http_methods(['POST'])
def pay_invoice(request,pk):
    return JsonResponse({'error':'Manual to‘lov tizimida avval chek yuklash talab qilinadi.'},status=400)

@require_http_methods(['GET'])
def admin_cards(request):
    if not _super(request):return JsonResponse({'error':'Super Admin huquqi talab qilinadi'},status=403)
    return JsonResponse({'results':[{'id':x.id,'card_number':x.card_number,'masked':x.masked_number,'holder_name':x.holder_name,'bank_name':x.bank_name,'company_name':x.company_name,'is_active':x.is_active} for x in PaymentCard.objects.order_by('sort_order','id')]})

@csrf_protect
@require_http_methods(['POST'])
def admin_card_save(request):
    if not _super(request):return JsonResponse({'error':'Super Admin huquqi talab qilinadi'},status=403)
    data=json.loads(request.body or '{}'); cid=data.get('id'); number=str(data.get('card_number','')).strip()
    if not number:return JsonResponse({'error':'Karta raqami majburiy'},status=400)
    obj=PaymentCard.objects.filter(pk=cid).first() if cid else PaymentCard()
    obj.card_number=number;obj.holder_name=data.get('holder_name','');obj.bank_name=data.get('bank_name','');obj.company_name=data.get('company_name','AVTOPARK PRO');obj.is_active=bool(data.get('is_active',True));obj.sort_order=int(data.get('sort_order',0));obj.save()
    return JsonResponse({'ok':True,'id':obj.id})

@csrf_protect
@require_http_methods(['POST'])
def admin_card_delete(request,pk):
    if not _super(request):return JsonResponse({'error':'Super Admin huquqi talab qilinadi'},status=403)
    x=PaymentCard.objects.filter(pk=pk).first()
    if not x:return JsonResponse({'error':'Karta topilmadi'},status=404)
    x.delete();return JsonResponse({'ok':True})
