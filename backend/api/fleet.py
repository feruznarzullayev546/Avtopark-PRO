import json
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from core.models import UserProfile, Vehicle, VehicleModelCatalog, DriverProfile, CompanyMembership
from .forms import DriverCreateForm, VehicleForm
from .branch_scope import branch_kwargs, relation_branch_kwargs

def _profile(request):
    return UserProfile.objects.select_related("company").filter(user=request.user).first()

def _company(request):
    p=_profile(request); cid=request.session.get('active_company_id')
    if request.user.is_superuser or (p and p.role==UserProfile.ROLE_SUPER_ADMIN):
        from core.models import Company
        return Company.objects.filter(pk=cid, is_active=True).first() if cid else Company.objects.filter(is_active=True).order_by("name").first()
    if cid:
        m=CompanyMembership.objects.filter(user=request.user,company_id=cid,status='ACTIVE').select_related('company').first()
        if m:return m.company
    return p.company if p else None

def _role(request):
    c=_company(request)
    m=CompanyMembership.objects.filter(user=request.user,company=c,status='ACTIVE').first() if c else None
    return m.role if m else (_profile(request).role if _profile(request) else None)

def _is_super(request):
    return bool(request.user.is_superuser or UserProfile.objects.filter(user=request.user, role=UserProfile.ROLE_SUPER_ADMIN).exists())

def _can_update(request):
    return _is_super(request) or _role(request) in [UserProfile.ROLE_DIRECTOR, UserProfile.ROLE_MANAGER]

def _can_create(request):
    return _is_super(request) or _role(request) == UserProfile.ROLE_DIRECTOR

def _can_delete(request):
    return _is_super(request) or _role(request) == UserProfile.ROLE_DIRECTOR

def _json(request):
    try: return json.loads(request.body or "{}")
    except json.JSONDecodeError: return None

def _errors(form):
    return {k: [str(e) for e in v] for k,v in form.errors.items()}

@require_http_methods(["GET"])
def driver_list(request):
    if not request.user.is_authenticated: return JsonResponse({"error":"Autentifikatsiya talab qilinadi"},status=401)
    c=_company(request)
    if not c: return JsonResponse({"results":[],"count":0})
    qs=DriverProfile.objects.filter(company=c, **branch_kwargs(request)).select_related("vehicle").order_by("-active","full_name")
    results=[]
    for d in qs:
        results.append({
            "id":d.id,"name":d.full_name,"phone":d.phone,
            "vehicle_id":d.vehicle_id,"vehicle":d.vehicle.number if d.vehicle else "",
            "active":d.active,"suspended":d.is_suspended,
            "suspended_until":d.suspended_until.isoformat() if d.suspended_until else None,
            "monthly_target":d.monthly_km_target,
            "workload_km":d.workload_km(),"completed_km":d.completed_km(),
            "rating":d.rating(),
        })
    return JsonResponse({"count":len(results),"results":results})

@csrf_protect
@require_http_methods(["POST"])
def driver_create(request):
    if not request.user.is_authenticated or not _can_create(request):
        return JsonResponse({"error":"Ruxsat yo‘q"},status=403)
    data=_json(request)
    if data is None: return JsonResponse({"error":"Noto‘g‘ri JSON"},status=400)
    form=DriverCreateForm(data)
    if not form.is_valid(): return JsonResponse({"errors":_errors(form)},status=400)
    c=_company(request); d=form.cleaned_data; User=get_user_model()
    with transaction.atomic():
        u=User.objects.create_user(username=d["username"],password=d["password1"])
        UserProfile.objects.create(user=u,company=c,role=UserProfile.ROLE_DRIVER,full_name=d["full_name"],phone=d["phone"])
        CompanyMembership.objects.create(user=u,company=c,role=CompanyMembership.ROLE_DRIVER,status=CompanyMembership.STATUS_ACTIVE,is_default=True)
        driver=DriverProfile.objects.create(company=c,user=u,full_name=d["full_name"],phone=d["phone"],branch=getattr(request,"active_branch",None))
    return JsonResponse({"id":driver.id,"message":"Haydovchi yaratildi"},status=201)

@csrf_protect
@require_http_methods(["PATCH"])
def driver_update(request,pk):
    if not request.user.is_authenticated or not _can_update(request): return JsonResponse({"error":"Ruxsat yo‘q"},status=403)
    c=_company(request); driver=DriverProfile.objects.filter(company=c, **branch_kwargs(request),pk=pk).first()
    if not driver:return JsonResponse({"error":"Haydovchi topilmadi"},status=404)
    data=_json(request) or {}
    allowed={"full_name","phone","monthly_km_target","active","note"}
    for k,v in data.items():
        if k in allowed and hasattr(driver,k): setattr(driver,k,v)
    driver.save()
    if driver.user_id:
        UserProfile.objects.filter(user_id=driver.user_id).update(full_name=driver.full_name, phone=driver.phone, is_active=driver.active)
    return JsonResponse({"ok":True,"id":driver.id})

@require_http_methods(["GET"])
def vehicle_list(request):
    if not request.user.is_authenticated:return JsonResponse({"error":"Autentifikatsiya talab qilinadi"},status=401)
    c=_company(request)
    if not c:return JsonResponse({"results":[],"count":0})
    qs=Vehicle.objects.filter(company=c, **branch_kwargs(request)).select_related("model_catalog","driver").order_by("model","number")
    results=[{"id":v.id,"number":v.number,"model":v.model_catalog.name if v.model_catalog else v.model,
              "model_id":v.model_catalog_id,"tonnage":v.tonnage,"mileage":v.current_mileage,
              "avg_daily_km":v.avg_daily_km,"driver_id":v.driver_id,
              "driver":v.driver.full_name if v.driver else "Biriktirilmagan","active":v.active,
              "start_date":v.start_date.isoformat(),"note":v.note,"image_url":v.image.url if v.image else None} for v in qs]
    return JsonResponse({"count":len(results),"results":results})

@require_http_methods(["GET"])
def vehicle_meta(request):
    if not request.user.is_authenticated:return JsonResponse({"error":"Autentifikatsiya talab qilinadi"},status=401)
    c=_company(request)
    return JsonResponse({
        "models":[{"id":x.id,"name":x.name,"tonnage":x.tonnage} for x in VehicleModelCatalog.objects.filter(company=c, active=True)],
        "drivers":[{"id":x.id,"name":x.full_name} for x in DriverProfile.objects.filter(company=c, **branch_kwargs(request),active=True).filter(vehicle__isnull=True)]
    })

@csrf_protect
@require_http_methods(["POST"])
def vehicle_model_create(request):
    if not request.user.is_authenticated or not _can_create(request): return JsonResponse({"error":"Faqat Direktor yoki Super Admin model qo‘sha oladi"},status=403)
    c=_company(request); data=request.POST if request.content_type.startswith("multipart/") else (_json(request) or {})
    name=str(data.get("name","")).strip(); tonnage=float(data.get("tonnage") or 0)
    if not name: return JsonResponse({"error":"Model nomi majburiy"},status=400)
    if VehicleModelCatalog.objects.filter(company=c,name__iexact=name).exists(): return JsonResponse({"error":"Bu model allaqachon mavjud"},status=409)
    m=VehicleModelCatalog.objects.create(company=c,name=name,tonnage=tonnage,active=True)
    return JsonResponse({"id":m.id,"name":m.name,"tonnage":m.tonnage},status=201)

@csrf_protect
@require_http_methods(["POST"])
def vehicle_create(request):
    if not request.user.is_authenticated or not _can_create(request):return JsonResponse({"error":"Ruxsat yo‘q"},status=403)
    c=_company(request); data=request.POST if request.content_type.startswith("multipart/") else _json(request)
    if data is None:return JsonResponse({"error":"Noto‘g‘ri JSON"},status=400)
    sub=getattr(c,"subscription",None); vehicle_limit=sub.plan.vehicle_limit if sub else c.max_vehicles
    if Vehicle.objects.filter(company=c).count() >= vehicle_limit and not request.user.is_superuser:
        return JsonResponse({"error":f"Tarif limiti to‘ldi: {vehicle_limit} ta transport"},status=409)
    form=VehicleForm(c,data,files=request.FILES)
    if not form.is_valid():return JsonResponse({"errors":_errors(form)},status=400)
    v=form.save()
    branch=getattr(request,"active_branch",None)
    if branch:
        v.branch=branch
        v.save(update_fields=["branch"])
        DriverProfile.objects.filter(pk=v.driver_id).update(branch=branch)
    return JsonResponse({"id":v.id,"message":"Avtomobil yaratildi"},status=201)

@csrf_protect
@require_http_methods(["PATCH"])
def vehicle_update(request,pk):
    if not request.user.is_authenticated or not _can_update(request):return JsonResponse({"error":"Ruxsat yo‘q"},status=403)
    c=_company(request); v=Vehicle.objects.filter(company=c, **branch_kwargs(request),pk=pk).first()
    if not v:return JsonResponse({"error":"Avtomobil topilmadi"},status=404)
    data=request.POST if request.content_type.startswith("multipart/") else (_json(request) or {})
    if "model_catalog" in data: data["model_catalog"]=str(data["model_catalog"])
    # Preserve existing image on JSON-only edit.
    form=VehicleForm(c,data,files=request.FILES,instance=v)
    if not form.is_valid():return JsonResponse({"errors":_errors(form)},status=400)
    form.save()
    return JsonResponse({"ok":True,"id":v.id})


@csrf_protect
@require_http_methods(["DELETE"])
def vehicle_delete(request, pk):
    if not request.user.is_authenticated or not _can_delete(request):
        return JsonResponse({"error":"Faqat Direktor yoki Super Admin o‘chira oladi"}, status=403)
    c=_company(request)
    v=Vehicle.objects.filter(company=c, **branch_kwargs(request), pk=pk).first()
    if not v:
        return JsonResponse({"error":"Avtomobil topilmadi"}, status=404)
    if getattr(v, 'driver_id', None):
        DriverProfile.objects.filter(pk=v.driver_id).update(vehicle=None)
    number=v.number
    v.delete()
    return JsonResponse({"ok":True,"message":f"{number} o‘chirildi"})


@csrf_protect
@require_http_methods(["DELETE"])
def driver_delete(request, pk):
    if not request.user.is_authenticated or not _can_delete(request):
        return JsonResponse({"error":"Faqat Direktor yoki Super Admin o‘chira oladi"}, status=403)
    c=_company(request)
    driver=DriverProfile.objects.filter(company=c, **branch_kwargs(request), pk=pk).select_related('user').first()
    if not driver:
        return JsonResponse({"error":"Haydovchi topilmadi"}, status=404)
    user=driver.user
    name=driver.full_name
    driver.delete()
    user.delete()
    return JsonResponse({"ok":True,"message":f"{name} o‘chirildi"})
