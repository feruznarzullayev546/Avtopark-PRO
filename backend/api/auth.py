import json
import hashlib
from datetime import timedelta
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.views.decorators.http import require_http_methods
from core.models import UserProfile, CompanyMembership, Company, OrganizationMembership, PlatformSession, PlatformSecurityEvent, Organization, Branch, BranchMembership, SubscriptionPlan, Subscription
from .forms import RegistrationForm
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})
    
@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})


def _default_plans():
    defaults = [
        {"name":"START","code":"start","price_monthly":299000,"price_yearly":2990000,"vehicle_limit":10,"user_limit":5,"features":["Avtopark","Reyslar","Yoqilg‘i","Sklad"],"sort_order":1},
        {"name":"BUSINESS","code":"business","price_monthly":499000,"price_yearly":4990000,"vehicle_limit":50,"user_limit":20,"features":["START imkoniyatlari","Servis","Audit log","Hisobotlar"],"sort_order":2},
        {"name":"PRO","code":"pro","price_monthly":999000,"price_yearly":9990000,"vehicle_limit":200,"user_limit":100,"features":["BUSINESS imkoniyatlari","GPS integratsiya","Analitika"],"sort_order":3},
        {"name":"ENTERPRISE","code":"enterprise","price_monthly":0,"price_yearly":0,"vehicle_limit":10000,"user_limit":1000,"features":["Individual shartlar","API","SLA"],"sort_order":4},
    ]
    for item in defaults:
        SubscriptionPlan.objects.get_or_create(code=item["code"], defaults=item)

def _unique_slug(model, name):
    """Return a unique URL-safe slug for models with a unique slug column."""
    base = slugify(name)[:150] or "company"
    candidate = base
    i = 1
    while model.objects.filter(slug=candidate).exists():
        i += 1
        suffix = f"-{i}"
        candidate = f"{base[:150-len(suffix)]}{suffix}"
    return candidate

def _unique_code(model, prefix, name):
    base = slugify(name)[:18] or prefix
    candidate = base.upper().replace('-', '_')
    i = 1
    while model.objects.filter(code=candidate).exists():
        i += 1
        candidate = f"{base[:14].upper()}_{i}"
    return candidate

@csrf_protect
def register_api(request):
    if request.method != "POST":
        return JsonResponse({"error":"POST talab qilinadi"}, status=405)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error":"Noto‘g‘ri JSON"}, status=400)
    form = RegistrationForm(payload)
    if not form.is_valid():
        return JsonResponse({"error":"Ma’lumotlarni tekshiring", "errors": {k:[str(e) for e in v] for k,v in form.errors.items()}}, status=400)
    d=form.cleaned_data
    User=get_user_model()
    try:
        with transaction.atomic():
            _default_plans()
            plan=SubscriptionPlan.objects.get(code="start", is_active=True)
            company_name=d["company_name"].strip()
            org=Organization.objects.create(name=company_name, legal_name=company_name, tin=d.get("tin","").strip(), email=d["email"].lower(), phone=d["phone"], code=_unique_code(Organization,"ORG",company_name),slug=_unique_slug(Organization,company_name))
            company=Company.objects.create(organization=org,name=company_name,legal_name=company_name,tin=d.get("tin","").strip(),phone=d["phone"],email=d["email"].lower(),code=_unique_code(Company,"CMP",company_name),slug=_unique_slug(Company,company_name),trial_ends_at=timezone.localdate()+timedelta(days=14))
            branch=Branch.objects.create(company=company,name="Bosh filial",code="HQ",is_headquarters=True,phone=d["phone"])
            company.default_branch=branch; company.save(update_fields=["default_branch"])
            user=User.objects.create_user(username=d["username"],email=d["email"].lower(),password=d["password1"],first_name=d["full_name"].strip())
            UserProfile.objects.create(user=user,company=company,role=UserProfile.ROLE_DIRECTOR,full_name=d["full_name"].strip(),phone=d["phone"])
            CompanyMembership.objects.create(user=user,company=company,role=CompanyMembership.ROLE_DIRECTOR,status=CompanyMembership.STATUS_ACTIVE,is_default=True)
            OrganizationMembership.objects.create(user=user,organization=org,role=OrganizationMembership.ROLE_OWNER,status=OrganizationMembership.STATUS_ACTIVE,is_default=True)
            BranchMembership.objects.create(user=user,branch=branch,role=BranchMembership.ROLE_MANAGER,status=BranchMembership.STATUS_ACTIVE,is_default=True)
            Subscription.objects.create(company=company,plan=plan,status=Subscription.STATUS_TRIAL,started_at=timezone.localdate(),current_period_start=timezone.localdate(),current_period_end=company.trial_ends_at)
            request.session["active_company_id"]=company.id
            request.session["active_branch_id"]=branch.id
            request.session.modified=True
            login(request,user)
        return JsonResponse({"ok":True,"message":"Kompaniya yaratildi. 14 kunlik START trial boshlandi."}, status=201)
    except IntegrityError as exc:
        # Registration used to report every DB uniqueness error as a duplicate login.
        # That was misleading: Organization/Company slugs are also unique.
        detail = str(exc)
        if "auth_user.username" in detail or "username" in detail.lower():
            message = "Bu login allaqachon mavjud."
        elif "slug" in detail.lower():
            message = "Bu kompaniya nomi uchun takroriy identifikator yuz berdi. Qayta urinib ko‘ring."
        elif "email" in detail.lower():
            message = "Bu email allaqachon tizimda ishlatilgan."
        else:
            message = "Registratsiya ma’lumotlari bazadagi mavjud yozuv bilan to‘qnashdi."
        return JsonResponse({"error": message, "code":"DUPLICATE", "detail": detail if __import__("django.conf", fromlist=["settings"]).settings.DEBUG else None}, status=409)
    except Exception as exc:
        # Do not silently turn a database/migration problem into a generic registration failure.
        # The frontend can show the exact actionable message while the server keeps the real detail in logs.
        import logging
        logging.getLogger(__name__).exception("Registration failed")
        return JsonResponse({
            "error":"Registratsiya vaqtida server/baza xatosi yuz berdi. Backendda migrationlarni ishga tushiring: python manage.py migrate va python manage.py repair_avtopark.",
            "code":"REGISTRATION_SERVER_ERROR",
            "detail": str(exc) if __import__("django.conf", fromlist=["settings"]).settings.DEBUG else "server-error",
        }, status=500)


@csrf_protect
def login_view(request):
    import json
    import hashlib
    import logging

    from django.contrib.auth import authenticate, login
    from django.http import JsonResponse
    from django.views.decorators.http import require_http_methods

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST talab qilinadi"},
            status=405,
        )

    try:
        payload = json.loads(request.body or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"error": "Noto‘g‘ri JSON"},
            status=400,
        )

    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))

    if not username or not password:
        return JsonResponse(
            {"error": "Login va parol majburiy"},
            status=400,
        )

    user = authenticate(
        request,
        username=username,
        password=password,
    )

    if user is None or not user.is_active:
        return JsonResponse(
            {"error": "Login yoki parol noto‘g‘ri"},
            status=401,
        )

    # 1. Asosiy autentifikatsiya.
    login(request, user)

    # 2. Kompaniya va filial kontekstini tiklash.
    try:
        from django.db import transaction
        from django.utils import timezone
        from core.models import (
            UserProfile,
            CompanyMembership,
            Branch,
            BranchMembership,
            OrganizationMembership,
            Subscription,
            SubscriptionPlan,
            PlatformSession,
            PlatformSecurityEvent,
        )

        with transaction.atomic():
            membership = (
                CompanyMembership.objects
                .filter(
                    user=user,
                    status=CompanyMembership.STATUS_ACTIVE,
                )
                .select_related("company")
                .order_by("-is_default", "id")
                .first()
            )

            profile = UserProfile.objects.filter(user=user).first()

            if membership:
                company = membership.company

                if profile is None:
                    role = membership.role
                    allowed_roles = {
                        UserProfile.ROLE_DIRECTOR,
                        UserProfile.ROLE_MANAGER,
                        UserProfile.ROLE_DRIVER,
                    }
                    if role not in allowed_roles:
                        role = UserProfile.ROLE_DIRECTOR

                    UserProfile.objects.create(
                        user=user,
                        company=company,
                        role=role,
                        full_name=user.get_full_name() or user.username,
                        phone=company.phone or "",
                    )
                elif not profile.company_id:
                    profile.company = company
                    profile.save(update_fields=["company"])

                branch = (
                    Branch.objects
                    .filter(company=company, is_active=True)
                    .order_by("-is_headquarters", "id")
                    .first()
                )

                if branch:
                    BranchMembership.objects.get_or_create(
                        user=user,
                        branch=branch,
                        defaults={
                            "role": BranchMembership.ROLE_MANAGER,
                            "status": BranchMembership.STATUS_ACTIVE,
                            "is_default": True,
                        },
                    )
                    request.session["active_branch_id"] = branch.id

                if company.organization_id:
                    OrganizationMembership.objects.get_or_create(
                        user=user,
                        organization_id=company.organization_id,
                        defaults={
                            "role": OrganizationMembership.ROLE_OWNER,
                            "status": OrganizationMembership.STATUS_ACTIVE,
                            "is_default": True,
                        },
                    )

                request.session["active_company_id"] = company.id

                if not Subscription.objects.filter(company=company).exists():
                    plan, _ = SubscriptionPlan.objects.get_or_create(
                        code="start",
                        defaults={
                            "name": "START",
                            "price_monthly": 299000,
                            "price_yearly": 2990000,
                            "vehicle_limit": 10,
                            "user_limit": 5,
                            "features": [],
                            "is_active": True,
                            "sort_order": 1,
                        },
                    )

                    end = company.trial_ends_at
                    if not end:
                        end = timezone.localdate() + timezone.timedelta(days=14)
                        company.trial_ends_at = end
                        company.save(update_fields=["trial_ends_at"])

                    Subscription.objects.create(
                        company=company,
                        plan=plan,
                        status=Subscription.STATUS_TRIAL,
                        started_at=timezone.localdate(),
                        current_period_start=timezone.localdate(),
                        current_period_end=end,
                    )

            request.session.modified = True

    except Exception:
        # Tenant kontekstini tiklashdagi xato loginni o'zi bilan
        # aralashtirilmasin. Tafsilot terminal logida saqlanadi.
        logging.getLogger(__name__).exception(
            "Login succeeded, but tenant context repair failed"
        )

    # 3. Sessiyani va audit logini yozish loginni bekor qilmasin.
    try:
        request.session.save()
        session_key = request.session.session_key

        if session_key:
            PlatformSession.objects.update_or_create(
                session_key_hash=hashlib.sha256(
                    session_key.encode()
                ).hexdigest(),
                defaults={
                    "user": user,
                    "ip_address": request.META.get("REMOTE_ADDR"),
                    "user_agent": request.META.get(
                        "HTTP_USER_AGENT", ""
                    )[:4000],
                    "device_label": request.META.get(
                        "HTTP_USER_AGENT", ""
                    )[:120],
                    "is_active": True,
                    "revoked_at": None,
                },
            )

        PlatformSecurityEvent.objects.create(
            event_type="LOGIN",
            severity="INFO",
            user=user,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:4000],
            metadata={},
        )

    except Exception:
        logging.getLogger(__name__).exception(
            "Login succeeded, but session audit logging failed"
        )

    return JsonResponse({"ok": True})

@csrf_protect
def logout_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST talab qilinadi"}, status=405)
    if request.user.is_authenticated:
        key=request.session.session_key
        if key:
            PlatformSession.objects.filter(session_key_hash=hashlib.sha256(key.encode()).hexdigest()).update(is_active=False,revoked_at=__import__("django.utils.timezone",fromlist=["now"]).now())
        PlatformSecurityEvent.objects.create(event_type="LOGOUT",severity="INFO",user=request.user,ip_address=request.META.get("REMOTE_ADDR"),user_agent=request.META.get("HTTP_USER_AGENT","")[:4000],metadata={})
    logout(request)
    return JsonResponse({"ok": True})

def session_user(request):
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False}, status=401)
    profile = UserProfile.objects.select_related("company").filter(user=request.user).first()
    memberships = list(CompanyMembership.objects.filter(user=request.user, status=CompanyMembership.STATUS_ACTIVE).select_related("company").order_by("-is_default", "company__name"))
    is_super=bool(request.user.is_superuser or (profile and profile.role == UserProfile.ROLE_SUPER_ADMIN))
    if is_super and not memberships:
        companies=list(Company.objects.filter(is_active=True,status='ACTIVE').order_by('name'))
        active_id=request.session.get('active_company_id')
        active=next((c for c in companies if c.id==active_id), companies[0] if companies else None)
        if active and not active_id: request.session['active_company_id']=active.id; request.session.modified=True
        company_items=[{'id':c.id,'name':c.name,'code':c.code,'role':'SUPER_ADMIN'} for c in companies]
        active_json={'id':active.id,'name':active.name,'code':active.code} if active else None
    else:
        active_id = request.session.get("active_company_id")
        active = next((m for m in memberships if m.company_id == active_id), None) or (memberships[0] if memberships else None)
        if active and not active_id:
            request.session["active_company_id"] = active.company_id; request.session.modified=True
        company_items=[{"id":m.company_id,"name":m.company.name,"code":m.company.code,"role":m.role,"is_default":m.is_default} for m in memberships]
        active_json={"id":active.company.id,"name":active.company.name,"code":active.company.code} if active else None
    return JsonResponse({
        "authenticated": True,
        "user": {"id": request.user.id, "username": request.user.username,
                 "full_name": profile.full_name if profile else (request.user.get_full_name() or request.user.username),
                 "role": (
    profile.role
    if profile
    else ("SUPER_ADMIN" if request.user.is_superuser else None)
),                 "avatar_url": request.build_absolute_uri(profile.avatar.url) if profile and profile.avatar else None},
        "company": active_json,
        "companies": company_items,
        "organizations": [{"id":m.organization_id,"name":m.organization.name,"code":m.organization.code,"role":m.role,"is_default":m.is_default} for m in OrganizationMembership.objects.filter(user=request.user,status="ACTIVE").select_related("organization")],
        "active_organization_id": getattr(active.company, "organization_id", None) if active and hasattr(active, "company") else (active.organization_id if active else None),
        "is_super": is_super,
    })



@csrf_protect
def profile_avatar(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error":"Avval tizimga kiring."}, status=401)
    if request.method not in {"POST", "DELETE"}:
        return JsonResponse({"error":"POST yoki DELETE talab qilinadi."}, status=405)
    profile = UserProfile.objects.filter(user=request.user).first()
    if not profile:
        return JsonResponse({"error":"Profil topilmadi."}, status=404)
    if request.method == "DELETE":
        if profile.avatar:
            profile.avatar.delete(save=False)
        profile.avatar = None
        profile.save(update_fields=["avatar"])
        return JsonResponse({"ok": True, "avatar_url": None})
    avatar = request.FILES.get("avatar")
    if not avatar:
        return JsonResponse({"error":"Avatar faylini tanlang."}, status=400)
    if avatar.size > 5 * 1024 * 1024:
        return JsonResponse({"error":"Avatar hajmi 5 MB dan oshmasligi kerak."}, status=400)
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if avatar.content_type not in allowed:
        return JsonResponse({"error":"Faqat JPG, PNG yoki WEBP rasmlar qabul qilinadi."}, status=400)
    try:
        from PIL import Image
        img = Image.open(avatar)
        img.verify()
    except Exception:
        return JsonResponse({"error":"Yuklangan fayl haqiqiy rasm emas."}, status=400)
    avatar.seek(0)
    if profile.avatar:
        profile.avatar.delete(save=False)
    profile.avatar = avatar
    profile.save(update_fields=["avatar"])
    return JsonResponse({"ok": True, "avatar_url": request.build_absolute_uri(profile.avatar.url)})
