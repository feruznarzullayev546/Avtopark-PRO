import csv, json
from datetime import date
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from core.models import UserProfile, Vehicle, FuelEntry, Issue, OtherExpense
from .trips import _company, _can_manage
from .branch_scope import branch_kwargs, relation_branch_kwargs

def _date(v):
    if not v: return date.today()
    try: return date.fromisoformat(str(v))
    except (TypeError, ValueError): raise ValueError('Sana noto\'g\'ri')

def _num(v):
    try: n=float(v)
    except (TypeError,ValueError): raise ValueError('Summa noto\'g\'ri')
    if n<0: raise ValueError('Summa manfiy bo\'lishi mumkin emas')
    return n

def _profile(request): return UserProfile.objects.select_related('company').filter(user=request.user).first()

def _rows(c, vehicle_id=None, start=None, end=None):
    fuels=FuelEntry.objects.filter(company=c, **branch_kwargs(request)).select_related('vehicle')
    issues=Issue.objects.filter(company=c, **branch_kwargs(request)).select_related('vehicle','part')
    others=OtherExpense.objects.filter(company=c, **branch_kwargs(request)).select_related('vehicle')
    if vehicle_id:
        fuels=fuels.filter(vehicle_id=vehicle_id); issues=issues.filter(vehicle_id=vehicle_id); others=others.filter(vehicle_id=vehicle_id)
    if start: fuels=fuels.filter(date__gte=start); issues=issues.filter(date__gte=start); others=others.filter(date__gte=start)
    if end: fuels=fuels.filter(date__lte=end); issues=issues.filter(date__lte=end); others=others.filter(date__lte=end)
    rows=[]
    for x in fuels: rows.append({'id':f'F{x.id}','source':'fuel','source_label':'Yoqilg\'i','date':x.date.isoformat(),'vehicle_id':x.vehicle_id,'vehicle':x.vehicle.number,'category':'Yoqilg\'i','description':x.fuel_type or 'Yoqilg\'i','amount':round(x.total,2),'document_no':x.document_no,'note':x.station})
    for x in issues: rows.append({'id':f'I{x.id}','source':'warehouse','source_label':'Sklad','date':x.date.isoformat(),'vehicle_id':x.vehicle_id,'vehicle':x.vehicle.number,'category':'Servis / ehtiyot qism','description':x.historical_part_name,'amount':round(x.total,2),'document_no':'','note':x.note})
    for x in others: rows.append({'id':f'O{x.id}','source':'other','source_label':'Boshqa','date':x.date.isoformat(),'vehicle_id':x.vehicle_id,'vehicle':x.vehicle.number if x.vehicle_id else 'Umumiy','category':x.category,'description':x.description,'amount':round(x.amount,2),'document_no':x.document_no,'note':x.note})
    rows.sort(key=lambda r:(r['date'],r['id']), reverse=True)
    return rows


@require_http_methods(['GET'])
def finance_list(request):
    if not request.user.is_authenticated or not _can_manage(request): return JsonResponse({'error':'Ruxsat yo\'q'},status=403)
    c=_company(request)
    try: vehicle_id=int(request.GET.get('vehicle_id')) if request.GET.get('vehicle_id') else None; start=_date(request.GET.get('from')) if request.GET.get('from') else None; end=_date(request.GET.get('to')) if request.GET.get('to') else None
    except ValueError as e: return JsonResponse({'error':str(e)},status=400)
    rows=_rows(c,vehicle_id,start,end); totals={}
    for r in rows: totals[r['source']]=round(totals.get(r['source'],0)+r['amount'],2)
    return JsonResponse({'results':rows,'summary':{'count':len(rows),'fuel':totals.get('fuel',0),'warehouse':totals.get('warehouse',0),'other':totals.get('other',0),'total':round(sum(totals.values()),2)},'vehicles':[{'id':v.id,'number':v.number,'model':v.model} for v in Vehicle.objects.filter(company=c, **branch_kwargs(request),active=True).order_by('number')]})

@csrf_protect
@require_http_methods(['POST'])
def other_create(request):
    if not request.user.is_authenticated or not _can_manage(request): return JsonResponse({'error':'Ruxsat yo\'q'},status=403)
    c=_company(request)
    try: data=json.loads(request.body or '{}'); dt=_date(data.get('date')); amount=_num(data.get('amount')); category=str(data.get('category','Boshqa')).strip() or 'Boshqa'; description=str(data.get('description','')).strip(); document_no=str(data.get('document_no','')).strip(); note=str(data.get('note','')).strip(); vehicle_id=data.get('vehicle_id') or None
    except (ValueError,json.JSONDecodeError) as e: return JsonResponse({'error':str(e)},status=400)
    if not description: return JsonResponse({'error':'Xarajat nomi majburiy'},status=400)
    vehicle=Vehicle.objects.filter(company=c, **branch_kwargs(request),pk=vehicle_id,active=True).first() if vehicle_id else None
    if vehicle_id and not vehicle: return JsonResponse({'error':'Avtomobil topilmadi'},status=400)
    x=OtherExpense.objects.create(company=c,date=dt,amount=amount,category=category,description=description,document_no=document_no,note=note,vehicle=vehicle)
    return JsonResponse({'expense':{'id':x.id,'date':x.date.isoformat(),'amount':x.amount}})

@require_http_methods(['GET'])
def finance_export(request):
    if not request.user.is_authenticated or not _can_manage(request): return JsonResponse({'error':'Ruxsat yo\'q'},status=403)
    c=_company(request); rows=_rows(c)
    response=HttpResponse(content_type='text/csv; charset=utf-8-sig'); response['Content-Disposition']='attachment; filename="avtopark_xarajatlar.csv"'
    w=csv.writer(response); w.writerow(['Sana','Manba','Avtomobil','Kategoriya','Tavsif','Summa','Hujjat','Izoh'])
    for r in rows: w.writerow([r['date'],r['source_label'],r['vehicle'],r['category'],r['description'],r['amount'],r['document_no'],r['note']])
    return response
