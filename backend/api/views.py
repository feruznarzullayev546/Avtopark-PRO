import json

from django.contrib.auth.decorators import login_required
from django.db.models import (
    Sum, Count, F, Q, ExpressionWrapper, DecimalField
)
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from api.branch_scope import branch_kwargs

from core.models import (
    UserProfile,
    Vehicle,
    DriverProfile,
    Route,
    Trip,
    Notification,
    FuelEntry,
    Issue,
    OtherExpense,
    CompanyMembership,
    Subscription,
    MaintenanceSchedule,
    Part,
    Receipt,
    Branch,
)


# ============================================================
# UMUMIY YORDAMCHI FUNKSIYALAR
# ============================================================

def health(request):
    return JsonResponse({
        "ok": True,
        "service": "avtopark-api",
        "version": "v1",
    })


@ensure_csrf_cookie
@require_http_methods(["GET"])
def csrf_view(request):
    return JsonResponse({"detail": "CSRF cookie set"})


def _profile(request):
    if not request.user.is_authenticated:
        return None

    return UserProfile.objects.filter(
        user=request.user
    ).first()


def _company(request):
    """
    Faol kompaniyani session, membership yoki eski profil
    orqali aniqlaydi.
    """
    if not request.user.is_authenticated:
        return None

    company_id = request.session.get("active_company_id")

    if company_id:
        membership = CompanyMembership.objects.filter(
            user=request.user,
            company_id=company_id,
            status=CompanyMembership.STATUS_ACTIVE,
        ).select_related("company").first()

        if membership:
            return membership.company

    membership = CompanyMembership.objects.filter(
        user=request.user,
        status=CompanyMembership.STATUS_ACTIVE,
    ).select_related(
        "company"
    ).order_by(
        "-is_default", "id"
    ).first()

    if membership:
        request.session["active_company_id"] = membership.company_id

        branch = Branch.objects.filter(
            company=membership.company,
            is_active=True,
        ).order_by(
            "-is_headquarters", "id"
        ).first()

        if branch:
            request.session["active_branch_id"] = branch.id

        request.session.modified = True
        return membership.company

    profile = UserProfile.objects.select_related(
        "company"
    ).filter(
        user=request.user
    ).first()

    return profile.company if profile else None


def csrf_failure(request, reason=""):
    return JsonResponse({
        "error": "CSRF tekshiruvi muvaffaqiyatsiz",
        "detail": reason,
    }, status=403)


# ============================================================
# FOYDALANUVCHI MA'LUMOTLARI
# ============================================================

@login_required
@require_http_methods(["GET"])
def me(request):
    profile = _profile(request)

    memberships = list(
        CompanyMembership.objects.filter(
            user=request.user,
            status=CompanyMembership.STATUS_ACTIVE,
        ).select_related(
            "company"
        ).order_by(
            "-is_default", "company__name"
        )
    )

    company_id = request.session.get("active_company_id")

    active = next(
        (
            item for item in memberships
            if item.company_id == company_id
        ),
        memberships[0] if memberships else None,
    )

    if active and not company_id:
        request.session["active_company_id"] = active.company_id
        request.session.modified = True

    is_super = (
        request.user.is_superuser
        or bool(
            profile
            and profile.role == UserProfile.ROLE_SUPER_ADMIN
        )
    )

    return JsonResponse({
        "authenticated": True,
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "full_name": (
                profile.full_name
                if profile and profile.full_name
                else request.user.get_full_name()
                or request.user.username
            ),
            "role": (
                active.role
                if active
                else profile.role if profile else None
            ),
        },
        "company": {
            "id": active.company.id,
            "name": active.company.name,
            "code": active.company.code,
        } if active else None,
        "companies": [
            {
                "id": item.company_id,
                "name": item.company.name,
                "code": item.company.code,
                "role": item.role,
            }
            for item in memberships
        ],
        "is_super": is_super,
    })


# ============================================================
# DASHBOARD
# ============================================================

@login_required
@require_http_methods(["GET"])
def dashboard(request):
    company = _company(request)

    if not company:
        return JsonResponse(
            {"error": "Kompaniya topilmadi"},
            status=403,
        )

    branch = branch_kwargs(request)

    today = timezone.localdate()
    month_start = today.replace(day=1)

    vehicles_qs = Vehicle.objects.filter(
        company=company, **branch
    )

    drivers_qs = DriverProfile.objects.filter(
        company=company, **branch
    )

    routes_qs = Route.objects.filter(
        company=company, **branch
    )

    trips_qs = Trip.objects.filter(
        company=company, **branch
    ).select_related(
        "route", "driver", "vehicle"
    )

    fuel_qs = FuelEntry.objects.filter(
        company=company, **branch
    )

    issue_qs = Issue.objects.filter(
        company=company, **branch
    )

    fuel_expr = ExpressionWrapper(
        F("liters") * F("price_per_liter"),
        output_field=DecimalField(
            max_digits=18, decimal_places=2
        ),
    )

    issue_expr = ExpressionWrapper(
        F("quantity") * F("unit_price"),
        output_field=DecimalField(
            max_digits=18, decimal_places=2
        ),
    )

    month_fuel = float(
        fuel_qs.filter(
            date__gte=month_start
        ).aggregate(
            total=Sum(fuel_expr)
        )["total"] or 0
    )

    month_issues = float(
        issue_qs.filter(
            date__gte=month_start
        ).aggregate(
            total=Sum(issue_expr)
        )["total"] or 0
    )

    month_trips = trips_qs.filter(
        date__gte=month_start
    )

    done_km = float(
        month_trips.filter(
            status="DONE"
        ).aggregate(
            total=Sum("km")
        )["total"] or 0
    )

    month_expenses = month_fuel + month_issues

    subscription = Subscription.objects.filter(
        company=company
    ).select_related(
        "plan"
    ).first()

    # Trial eslatmasi: foydalanuvchiga kuniga bir marta.
    if (
        subscription
        and subscription.status == Subscription.STATUS_TRIAL
        and company.trial_ends_at
    ):
        trial_left = (
            company.trial_ends_at - today
        ).days

        if trial_left >= 0:
            profile = _profile(request)

            if profile:
                dedupe_key = (
                    f"trial-{company.id}-"
                    f"{today.isoformat()}-{profile.id}"
                )

                exists = Notification.objects.filter(
                    recipient=profile,
                    company=company,
                    dedupe_key=dedupe_key,
                ).exists()

                if not exists:
                    if trial_left == 0:
                        message = (
                            "Bepul sinov muddati bugun yakunlanadi. "
                            "Xizmatlar uzluksiz davom etishi uchun "
                            "tarif rejasini faollashtiring."
                        )
                    elif trial_left == 1:
                        message = (
                            "Bepul sinov muddati tugashiga 1 kun qoldi. "
                            "O'zingizga mos tarifni tanlang."
                        )
                    else:
                        message = (
                            f"Bepul sinov muddatingiz yakunlanishiga "
                            f"{trial_left} kun qoldi. "
                            f"Tarif rejasini tanlang."
                        )

                    Notification.objects.create(
                        recipient=profile,
                        company=company,
                        title="Trial eslatmasi",
                        message=message,
                        url="/billing",
                        dedupe_key=dedupe_key,
                    )

    trial_days_left = None

    if (
        subscription
        and subscription.status == Subscription.STATUS_TRIAL
        and subscription.current_period_end
    ):
        trial_days_left = max(
            (subscription.current_period_end - today).days,
            0,
        )

    # Ombordagi minimal qoldiq.
    parts = list(
        Part.objects.filter(
            company=company, **branch
        ).only(
            "id", "code", "name", "min_stock", "unit_price"
        )[:80]
    )

    part_ids = [part.id for part in parts]

    incoming = {
        row["part_id"]: row["total"] or 0
        for row in Receipt.objects.filter(
            company=company,
            part_id__in=part_ids,
            **branch,
        ).values(
            "part_id"
        ).annotate(
            total=Sum("quantity")
        )
    }

    outgoing = {
        row["part_id"]: row["total"] or 0
        for row in issue_qs.filter(
            part_id__in=part_ids
        ).values(
            "part_id"
        ).annotate(
            total=Sum("quantity")
        )
    }

    low_stock = []

    for part in parts:
        stock = float(
            incoming.get(part.id, 0)
            - outgoing.get(part.id, 0)
        )

        min_stock = float(part.min_stock or 0)

        if stock <= min_stock:
            low_stock.append({
                "id": part.id,
                "code": part.code,
                "name": part.name,
                "stock": stock,
                "min_stock": min_stock,
            })

    # Texnik xizmat ogohlantirishlari.
    maintenance = MaintenanceSchedule.objects.filter(
        vehicle__company=company,
        active=True,
    ).select_related(
        "vehicle", "part"
    )

    service_alerts = []

    for item in maintenance[:60]:
        status = getattr(item, "status_code", "NORMAL")

        if status in {
            "QIZIL", "SARIQ", "CRITICAL", "HIGH"
        }:
            service_alerts.append({
                "id": item.id,
                "vehicle": (
                    item.vehicle.number
                    if item.vehicle_id else "—"
                ),
                "part": (
                    item.part.name
                    if item.part_id else "Servis"
                ),
                "status": status,
                "remaining_km": float(
                    item.remaining_km or 0
                ),
                "remaining_days": int(
                    item.remaining_days or 0
                ),
            })

    # So'nggi reyslar.
    recent = []

    for trip in trips_qs.order_by("-date", "-id")[:7]:
        recent.append({
            "id": trip.id,
            "trip_no": trip.trip_no or trip.id,
            "date": (
                trip.date.isoformat()
                if trip.date else None
            ),
            "status": trip.status,
            "route": (
                trip.route.name
                if trip.route_id
                else f"{trip.from_location} → {trip.to_location}"
            ),
            "vehicle": (
                trip.vehicle.number
                if trip.vehicle_id else "—"
            ),
            "driver": (
                trip.driver.full_name
                if trip.driver_id else "—"
            ),
            "km": float(trip.km or 0),
        })

    today_qs = trips_qs.filter(date=today)

    # Bildirishnomalar: faqat joriy foydalanuvchiga tegishlilari.
    unread_notifications = Notification.objects.filter(
        company=company,
        read_at__isnull=True,
    ).filter(
        Q(recipient__user=request.user)
        | Q(driver__user=request.user)
    ).count()

    return JsonResponse({
        "company": {
            "id": company.id,
            "name": company.name,
            "code": company.code,
            "status": company.status,
            "trial_ends_at": (
                company.trial_ends_at.isoformat()
                if company.trial_ends_at else None
            ),
        },

        "subscription": {
            "plan": (
                subscription.plan.name
                if subscription and subscription.plan else ""
            ),
            "plan_code": (
                subscription.plan.code
                if subscription and subscription.plan else ""
            ),
            "status": subscription.status,
            "period_end": (
                subscription.current_period_end.isoformat()
                if subscription.current_period_end else None
            ),
            "trial_days_left": trial_days_left,
        } if subscription else None,

        "vehicles": vehicles_qs.filter(active=True).count(),
        "drivers": drivers_qs.filter(active=True).count(),
        "routes": routes_qs.filter(active=True).count(),
        "trips": trips_qs.count(),

        "today_trips": today_qs.count(),
        "today_done": today_qs.filter(status="DONE").count(),
        "today_active": today_qs.filter(
            status__in=["PLANNED", "CONFIRMED"]
        ).count(),

        "month_trips": month_trips.count(),
        "month_done": month_trips.filter(
            status="DONE"
        ).count(),
        "month_cancelled": month_trips.filter(
            status="CANCELLED"
        ).count(),

        "month_fuel": month_fuel,
        "month_issues": month_issues,
        "month_expenses": month_expenses,
        "done_km": done_km,
        "cost_per_km": (
            month_expenses / done_km if done_km else 0
        ),

        "unread_notifications": unread_notifications,
        "low_stock_count": len(low_stock),
        "service_alert_count": len(service_alerts),
        "low_stock": low_stock[:6],
        "service_alerts": service_alerts[:6],
        "recent_trips": recent,
    })


# ============================================================
# AVTOMOBILLAR
# ============================================================

@login_required
@require_http_methods(["GET"])
def vehicles(request):
    company = _company(request)

    if not company:
        return JsonResponse({
            "results": [],
            "count": 0,
        })

    qs = Vehicle.objects.filter(
        company=company,
        **branch_kwargs(request),
    ).select_related(
        "driver", "model_catalog"
    )

    return JsonResponse({
        "count": qs.count(),
        "results": [
            {
                "id": item.id,
                "number": item.number,
                "model": (
                    item.model_catalog.name
                    if item.model_catalog else ""
                ),
                "driver": (
                    item.driver.full_name
                    if item.driver else ""
                ),
                "mileage": item.current_mileage,
                "active": item.active,
            }
            for item in qs
        ],
    })


# ============================================================
# HAYDOVCHILAR
# ============================================================

@login_required
@require_http_methods(["GET"])
def drivers(request):
    company = _company(request)

    if not company:
        return JsonResponse({
            "results": [],
            "count": 0,
        })

    qs = DriverProfile.objects.filter(
        company=company,
        **branch_kwargs(request),
    ).select_related("vehicle")

    return JsonResponse({
        "count": qs.count(),
        "results": [
            {
                "id": item.id,
                "name": item.full_name,
                "phone": item.phone,
                "vehicle": (
                    item.vehicle.number
                    if item.vehicle else ""
                ),
                "rating": getattr(item, "rating", None),
                "active": item.active,
            }
            for item in qs
        ],
    })


# ============================================================
# YO'NALISHLAR
# ============================================================

@login_required
@require_http_methods(["GET"])
def routes(request):
    company = _company(request)

    if not company:
        return JsonResponse({
            "results": [],
            "count": 0,
        })

    qs = Route.objects.filter(
        company=company,
        active=True,
        **branch_kwargs(request),
    )

    return JsonResponse({
        "count": qs.count(),
        "results": [
            {
                "id": item.id,
                "name": item.name,
                "from": getattr(item, "origin", ""),
                "to": getattr(item, "destination", ""),
                "round_trip_km": getattr(
                    item, "round_trip_km", None
                ),
            }
            for item in qs
        ],
    })


# ============================================================
# REYSLAR
# ============================================================

@login_required
@require_http_methods(["GET"])
def trips(request):
    company = _company(request)

    if not company:
        return JsonResponse({
            "results": [],
            "count": 0,
        })

    qs = Trip.objects.filter(
        company=company,
        **branch_kwargs(request),
    ).select_related(
        "route", "driver", "vehicle"
    )

    return JsonResponse({
        "count": qs.count(),
        "results": [
            {
                "id": item.id,
                "date": (
                    item.date.isoformat()
                    if item.date else None
                ),
                "route": (
                    item.route.name if item.route else ""
                ),
                "driver": (
                    item.driver.full_name
                    if item.driver else ""
                ),
                "vehicle": (
                    item.vehicle.number
                    if item.vehicle else ""
                ),
                "status": item.status,
            }
            for item in qs
        ],
    })


# ============================================================
# BILDIRISHNOMALAR
# ============================================================

@login_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def notifications(request):
    profile = _profile(request)

    is_super = bool(
        request.user.is_superuser
        or (
            profile
            and profile.role == UserProfile.ROLE_SUPER_ADMIN
        )
    )
