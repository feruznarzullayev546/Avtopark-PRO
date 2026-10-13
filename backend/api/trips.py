import json
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Sum, Value, FloatField
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from core.models import UserProfile, Route, Trip, DriverProfile, AuditLog, Notification, CompanyMembership
from .branch_scope import branch_kwargs, relation_branch_kwargs


def _profile(request):
    return UserProfile.objects.select_related('company').filter(user=request.user).first()


def _company(request):
    p=_profile(request); cid=request.session.get('active_company_id')
    if cid:
        m=CompanyMembership.objects.filter(user=request.user,company_id=cid,status='ACTIVE').select_related('company').first()
        if m:return m.company
    return p.company if p else None

def _role(request):
    c=_company(request); m=CompanyMembership.objects.filter(user=request.user,company=c,status='ACTIVE').first() if c else None
    return m.role if m else (_profile(request).role if _profile(request) else None)

def _can_manage(request): return _role(request) in {UserProfile.ROLE_DIRECTOR, UserProfile.ROLE_MANAGER, 'DISPATCHER'}
def _can_create(request): return _role(request) in {UserProfile.ROLE_DIRECTOR, 'DISPATCHER'}
def _can_direct(request): return _role(request)==UserProfile.ROLE_DIRECTOR


def _json(request):
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return None


def _errors(form):
    return {k: [str(e) for e in v] for k, v in form.errors.items()}


def _driver_json(d):
    return {
        'id': d.id,
        'name': d.full_name,
        'phone': d.phone,
        'vehicle_id': d.vehicle_id,
        'vehicle': d.vehicle.number if d.vehicle else '',
        'active': d.active,
        'suspended': d.is_suspended,
        'suspended_until': d.suspended_until.isoformat() if d.suspended_until else None,
        'workload_km': d.workload_km(),
        'completed_km': d.completed_km(),
        'rating': d.rating(),
    }


def _route_json(r):
    return {
        'id': r.id,
        'name': r.name,
        'from_location': r.from_location,
        'to_location': r.to_location,
        'one_way_km': r.one_way_km or r.distance_km,
        'round_trip_km': r.round_trip_km or (r.distance_km * 2),
        'standard_tonnage': r.standard_tonnage,
        'active': r.active,
    }


def _trip_json(t):
    return {
        'id': t.id,
        'trip_no': t.trip_no,
        'date': t.date.isoformat(),
        'trip_time': t.trip_time.strftime('%H:%M'),
        'status': t.status,
        'status_label': t.get_status_display(),
        'route': _route_json(t.route) if t.route_id else None,
        'driver': _driver_json(t.driver),
        'vehicle': {'id': t.vehicle_id, 'number': t.vehicle.number, 'model': t.vehicle.model},
        'from_location': t.from_location,
        'to_location': t.to_location,
        'km': t.km,
        'cargo_t': t.cargo_t,
        'cancellation_reason': t.cancellation_reason,
        'cancellation_review': t.cancellation_review,
        'cancellation_review_label': t.get_cancellation_review_display(),
        'cancellation_review_note': t.cancellation_review_note,
        'accepted_at': t.accepted_at.isoformat() if t.accepted_at else None,
        'cancelled_at': t.cancelled_at.isoformat() if t.cancelled_at else None,
        'note': t.note,
    }


def _notify(profile, title, message):
    if not profile:
        return
    Notification.objects.create(company=profile.company, recipient=profile, title=title, message=message, url='/trips/')


def _audit(request, trip, action, description, metadata=None):
    AuditLog.objects.create(
        company=trip.company, branch=trip.branch, user=request.user, action=action,
        model_name='Trip', object_id=str(trip.id), description=description,
        metadata=metadata or {}, ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )


def _choose_driver(company):
    today = timezone.localdate()
    qs = DriverProfile.objects.filter(
        company=company, active=True, vehicle__isnull=False, vehicle__active=True
    ).filter(Q(suspended_until__isnull=True) | Q(suspended_until__lt=today))
    qs = qs.select_related('vehicle').annotate(
        workload=Coalesce(
            Sum('trips__km', filter=Q(trips__status__in=['PLANNED', 'CONFIRMED', 'DONE'])),
            Value(0.0), output_field=FloatField()
        )
    )
    return qs.order_by('workload', 'last_assigned_at', 'pk').first()


@require_http_methods(['GET'])
def route_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Autentifikatsiya talab qilinadi'}, status=401)
    c = _company(request)
    if not c:
        return JsonResponse({'count': 0, 'results': []})
    qs = Route.objects.filter(company=c, **branch_kwargs(request)).order_by('-active', 'name')
    return JsonResponse({'count': qs.count(), 'results': [_route_json(r) for r in qs]})


@csrf_protect
@require_http_methods(['POST'])
def route_create(request):
    if not request.user.is_authenticated or not _can_create(request):
        return JsonResponse({'error': 'Ruxsat yo‘q'}, status=403)
    data = _json(request)
    if data is None:
        return JsonResponse({'error': 'Noto‘g‘ri JSON'}, status=400)
    name = str(data.get('name', '')).strip()
    origin = str(data.get('from_location', '')).strip()
    destination = str(data.get('to_location', '')).strip()
    try:
        one_way = float(data.get('one_way_km', data.get('distance_km', 0)) or 0)
        round_trip = float(data.get('round_trip_km', 0) or 0)
        tonnage = data.get('standard_tonnage')
        tonnage = float(tonnage) if tonnage not in (None, '') else None
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Masofa yoki tonna noto‘g‘ri'}, status=400)
    if not name or not origin or not destination or one_way <= 0:
        return JsonResponse({'error': 'Yo‘nalish nomi, qayerdan, qayerga va masofa majburiy'}, status=400)
    if round_trip <= 0:
        round_trip = one_way * 2
    if round_trip < one_way:
        return JsonResponse({'error': 'Borib-kelish km bir tomonga km dan kichik bo‘lishi mumkin emas'}, status=400)
    c = _company(request)
    if Route.objects.filter(company=c, **branch_kwargs(request), name=name).exists():
        return JsonResponse({'error': 'Bu yo‘nalish nomi allaqachon mavjud'}, status=400)
    r = Route.objects.create(company=c, branch=getattr(request, 'active_branch', None), name=name, from_location=origin, to_location=destination,
                             distance_km=one_way, one_way_km=one_way, round_trip_km=round_trip,
                             standard_tonnage=tonnage, active=bool(data.get('active', True)))
    AuditLog.objects.create(company=c, branch=r.branch, user=request.user, action='CREATE', model_name='Route', object_id=str(r.id), description=f'Yo‘nalish yaratildi: {r.name}', metadata={'one_way_km': one_way, 'round_trip_km': round_trip})
    return JsonResponse({'route': _route_json(r)}, status=201)


@csrf_protect
@require_http_methods(['PATCH'])
def route_update(request, pk):
    if not request.user.is_authenticated or not _can_manage(request):
        return JsonResponse({'error': 'Ruxsat yo‘q'}, status=403)
    c = _company(request)
    r = Route.objects.filter(company=c, **branch_kwargs(request), pk=pk).first()
    if not r:
        return JsonResponse({'error': 'Yo‘nalish topilmadi'}, status=404)
    data = _json(request) or {}
    for field in ('name', 'from_location', 'to_location'):
        if field in data:
            setattr(r, field, str(data[field]).strip())
    try:
        if 'one_way_km' in data or 'distance_km' in data:
            r.one_way_km = float(data.get('one_way_km', data.get('distance_km')))
            r.distance_km = r.one_way_km
        if 'round_trip_km' in data:
            r.round_trip_km = float(data['round_trip_km'])
        elif 'one_way_km' in data or 'distance_km' in data:
            r.round_trip_km = r.one_way_km * 2
        if 'standard_tonnage' in data:
            r.standard_tonnage = float(data['standard_tonnage']) if data['standard_tonnage'] not in ('', None) else None
        if 'active' in data:
            r.active = bool(data['active'])
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Kiritilgan sonli qiymat noto‘g‘ri'}, status=400)
    if r.one_way_km <= 0 or r.round_trip_km < r.one_way_km:
        return JsonResponse({'error': 'Masofa qiymatlarini tekshiring'}, status=400)
    r.save()
    AuditLog.objects.create(company=c, branch=r.branch, user=request.user, action='UPDATE', model_name='Route', object_id=str(r.id), description=f'Yo‘nalish yangilandi: {r.name}', metadata={'active': r.active, 'one_way_km': r.one_way_km, 'round_trip_km': r.round_trip_km})
    return JsonResponse({'route': _route_json(r)})


@csrf_protect
@require_http_methods(['DELETE'])
def route_delete(request, pk):
    if not request.user.is_authenticated or not _can_direct(request):
        return JsonResponse({'error': 'Faqat direktor o‘chira oladi'}, status=403)
    c = _company(request)
    r = Route.objects.filter(company=c, **branch_kwargs(request), pk=pk).first()
    if not r:
        return JsonResponse({'error': 'Yo‘nalish topilmadi'}, status=404)
    if r.trips.exists():
        return JsonResponse({'error': 'Bu yo‘nalishga bog‘langan reyslar mavjud. O‘chirish o‘rniga yo‘nalishni faol emas qiling.'}, status=409)
    AuditLog.objects.create(company=c, branch=r.branch, user=request.user, action='DELETE', model_name='Route', object_id=str(r.id), description=f'Yo‘nalish o‘chirildi: {r.name}', metadata={})
    r.delete()
    return JsonResponse({'ok': True})


@csrf_protect
@require_http_methods(['POST'])
def route_toggle(request, pk):
    if not request.user.is_authenticated or not _can_manage(request):
        return JsonResponse({'error': 'Ruxsat yo‘q'}, status=403)
    c = _company(request)
    r = Route.objects.filter(company=c, **branch_kwargs(request), pk=pk).first()
    if not r:
        return JsonResponse({'error': 'Yo‘nalish topilmadi'}, status=404)
    r.active = not r.active
    r.save(update_fields=['active'])
    AuditLog.objects.create(company=c, branch=r.branch, user=request.user, action='UPDATE', model_name='Route', object_id=str(r.id), description=f'Yo‘nalish statusi o‘zgardi: {r.name}', metadata={'active': r.active})
    return JsonResponse({'route': _route_json(r)})


@require_http_methods(['GET'])
def trip_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Autentifikatsiya talab qilinadi'}, status=401)
    c = _company(request)
    if not c:
        return JsonResponse({'count': 0, 'results': []})
    d = getattr(request.user, 'driver_profile', None)
    qs = Trip.objects.filter(company=c, **branch_kwargs(request))
    if d:
        qs = qs.filter(driver=d)
    qs = qs.select_related('route', 'driver', 'vehicle').order_by('-date', '-id')
    return JsonResponse({'count': qs.count(), 'results': [_trip_json(t) for t in qs[:200]]})


@require_http_methods(['GET'])
def trip_meta(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Autentifikatsiya talab qilinadi'}, status=401)
    c = _company(request)
    if not c:
        return JsonResponse({'routes': [], 'drivers': []})
    routes = Route.objects.filter(company=c, **branch_kwargs(request), active=True).order_by('name')
    drivers = DriverProfile.objects.filter(company=c, **branch_kwargs(request), active=True).select_related('vehicle').order_by('full_name')
    return JsonResponse({'routes': [_route_json(r) for r in routes], 'drivers': [_driver_json(d) for d in drivers]})


@csrf_protect
@require_http_methods(['POST'])
def trip_create(request):
    if not request.user.is_authenticated or not _can_manage(request):
        return JsonResponse({'error': 'Ruxsat yo‘q'}, status=403)
    data = _json(request)
    if data is None:
        return JsonResponse({'error': 'Noto‘g‘ri JSON'}, status=400)
    c = _company(request)
    manual_driver = bool(data.get('manual_driver', False))
    route = None
    if data.get('route_id'):
        route = Route.objects.filter(company=c, **branch_kwargs(request), active=True, pk=data['route_id']).first()
        if not route:
            return JsonResponse({'error': 'Yo‘nalish topilmadi'}, status=400)
        origin, destination = route.from_location, route.to_location
        km = route.round_trip_km or route.distance_km or route.one_way_km
    else:
        return JsonResponse({'error': 'Yo‘nalishni tanlang'}, status=400)
    try:
        date = data.get('date') or timezone.localdate().isoformat()
        trip_time = data.get('trip_time') or '08:00'
        cargo = data.get('cargo_t')
        cargo = float(cargo) if cargo not in ('', None) else None
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Reys sanasi yoki yuk qiymati noto‘g‘ri'}, status=400)

    with transaction.atomic():
        if manual_driver:
            driver = DriverProfile.objects.select_related('vehicle').filter(company=c, **branch_kwargs(request), active=True, pk=data.get('driver_id')).first()
            if not driver:
                return JsonResponse({'error': 'Qo‘lda biriktirish uchun haydovchini tanlang'}, status=400)
        else:
            driver = _choose_driver(c)
            if not driver:
                return JsonResponse({'error': 'Hozir reysga tayyor haydovchi topilmadi'}, status=409)
        if not driver.vehicle_id or not driver.vehicle.active:
            return JsonResponse({'error': 'Haydovchiga faol avtomobil biriktirilmagan'}, status=400)
        if driver.is_suspended:
            return JsonResponse({'error': f'{driver.full_name} taqiq ostida'}, status=400)
        trip = Trip.objects.create(company=c, branch=getattr(request, 'active_branch', None), date=date, trip_time=trip_time, route=route, driver=driver,
                                   vehicle=driver.vehicle, from_location=origin, to_location=destination,
                                   km=km, cargo_t=cargo, note=str(data.get('note', '')).strip(), status='PLANNED')
        driver.last_assigned_at = timezone.now()
        driver.save(update_fields=['last_assigned_at'])
        _audit(request, trip, 'CREATE', f'Reys yaratildi: {trip.trip_no or trip.id}', {'status': trip.status, 'driver_id': driver.id, 'vehicle_id': driver.vehicle_id, 'route_id': route.id})
        for profile in UserProfile.objects.filter(company=c, role=UserProfile.ROLE_DRIVER, user=driver.user, is_active=True):
            _notify(profile, 'Yangi reys biriktirildi', f'{trip.date:%d.%m.%Y} {trip.trip_time:%H:%M} — {origin} → {destination}. Masofa: {km:g} km.')
    return JsonResponse({'trip': _trip_json(trip)}, status=201)


@csrf_protect
@require_http_methods(['POST'])
def trip_accept(request, pk):
    d = getattr(request.user, 'driver_profile', None)
    if not d:
        return JsonResponse({'error': 'Faqat haydovchi'}, status=403)
    t = Trip.objects.select_related('driver', 'vehicle', 'route').filter(company=d.company, driver=d, pk=pk).first()
    if not t:
        return JsonResponse({'error': 'Reys topilmadi'}, status=404)
    if t.status != 'PLANNED':
        return JsonResponse({'error': 'Bu reysni qabul qilib bo‘lmaydi'}, status=400)
    if d.is_suspended:
        return JsonResponse({'error': f'Reysga chiqish taqiqlangan: {d.suspended_until:%d.%m.%Y} gacha'}, status=400)
    t.status = 'CONFIRMED'; t.accepted_at = timezone.now(); t.save(update_fields=['status', 'accepted_at'])
    _audit(request, t, 'STATUS', 'Reys haydovchi tomonidan qabul qilindi', {'from': 'PLANNED', 'to': 'CONFIRMED'})
    return JsonResponse({'trip': _trip_json(t)})


@csrf_protect
@require_http_methods(['POST'])
def trip_start(request, pk):
    d = getattr(request.user, 'driver_profile', None)
    if not d:
        return JsonResponse({'error': 'Faqat haydovchi'}, status=403)
    t = Trip.objects.select_related('driver', 'vehicle', 'route').filter(company=d.company, driver=d, pk=pk).first()
    if not t:
        return JsonResponse({'error': 'Reys topilmadi'}, status=404)
    if t.status != 'CONFIRMED':
        return JsonResponse({'error': 'Avval reysni qabul qilish kerak'}, status=400)
    if d.is_suspended:
        return JsonResponse({'error': 'Haydovchi vaqtincha cheklangan'}, status=400)
    t.status = 'IN_PROGRESS'
    t.save(update_fields=['status'])
    _audit(request, t, 'STATUS', 'Reys yo‘lga chiqdi', {'from': 'CONFIRMED', 'to': 'IN_PROGRESS'})
    return JsonResponse({'trip': _trip_json(t)})


@csrf_protect
@require_http_methods(['POST'])
def trip_cancel(request, pk):
    d = getattr(request.user, 'driver_profile', None)
    if not d:
        return JsonResponse({'error': 'Faqat haydovchi'}, status=403)
    t = Trip.objects.select_related('driver', 'vehicle', 'route').filter(company=d.company, driver=d, pk=pk).first()
    if not t:
        return JsonResponse({'error': 'Reys topilmadi'}, status=404)
    if t.status not in {'PLANNED', 'CONFIRMED'}:
        return JsonResponse({'error': 'Bu reysni bekor qilib bo‘lmaydi'}, status=400)
    data = _json(request) or {}
    reason = str(data.get('reason', '')).strip()
    if len(reason) < 5:
        return JsonResponse({'error': 'Sabab kamida 5 belgidan iborat bo‘lishi kerak'}, status=400)
    t.status = 'CANCELLED'; t.cancellation_reason = reason; t.cancelled_at = timezone.now(); t.cancellation_review = 'PENDING'
    t.save(update_fields=['status', 'cancellation_reason', 'cancelled_at', 'cancellation_review'])
    _audit(request, t, 'CANCEL', 'Reys haydovchi tomonidan bekor qilindi', {'reason': reason, 'to': 'CANCELLED'})
    for p in UserProfile.objects.filter(company=d.company, role__in=[UserProfile.ROLE_DIRECTOR, UserProfile.ROLE_MANAGER], is_active=True):
        _notify(p, 'Haydovchi reysni bekor qildi', f'{d.full_name}: {reason}')
    return JsonResponse({'trip': _trip_json(t)})


@csrf_protect
@require_http_methods(['POST'])
def trip_review_cancel(request, pk):
    if not request.user.is_authenticated or not _can_direct(request):
        return JsonResponse({'error': 'Faqat direktor'}, status=403)
    c = _company(request)
    t = Trip.objects.select_related('driver', 'vehicle', 'route').filter(company=c, **branch_kwargs(request), pk=pk).first()
    if not t:
        return JsonResponse({'error': 'Reys topilmadi'}, status=404)
    if t.status != 'CANCELLED' or not t.cancellation_reason:
        return JsonResponse({'error': 'Ko‘rib chiqish uchun bekor qilingan reys bo‘lishi kerak'}, status=400)
    data = _json(request) or {}
    decision = data.get('decision')
    if decision not in {'JUSTIFIED', 'UNJUSTIFIED'}:
        return JsonResponse({'error': 'Qarorni tanlang'}, status=400)
    note = str(data.get('review_note', '')).strip()
    t.cancellation_review = decision; t.cancellation_review_note = note; t.reviewed_at = timezone.now(); t.reviewed_by = request.user
    if decision == 'UNJUSTIFIED':
        try:
            days = max(1, min(3, int(data.get('suspend_days', 1))))
        except (TypeError, ValueError):
            days = 1
        until = timezone.localdate() + timedelta(days=days - 1)
        t.driver.suspended_until = until
        t.driver.save(update_fields=['suspended_until'])
    t.save(update_fields=['cancellation_review', 'cancellation_review_note', 'reviewed_at', 'reviewed_by'])
    _audit(request, t, 'REVIEW', f'Bekor qilish ko‘rib chiqildi: {decision}', {'decision': decision, 'suspend_days': data.get('suspend_days')})
    return JsonResponse({'trip': _trip_json(t)})


@csrf_protect
@require_http_methods(['DELETE'])
def trip_delete(request, pk):
    if not request.user.is_authenticated or not _can_direct(request):
        return JsonResponse({'error': 'Faqat direktor o‘chira oladi'}, status=403)
    c = _company(request)
    t = Trip.objects.filter(company=c, **branch_kwargs(request), pk=pk).first()
    if not t:
        return JsonResponse({'error': 'Reys topilmadi'}, status=404)
    if t.status == 'IN_PROGRESS':
        return JsonResponse({'error': 'Yo‘ldagi reysni o‘chirib bo‘lmaydi'}, status=400)
    _audit(request, t, 'DELETE', f'Reys o‘chirildi: {t.trip_no or t.id}', {'status': t.status})
    t.delete()
    return JsonResponse({'ok': True})


@csrf_protect
@require_http_methods(['POST'])
def trip_complete(request, pk):
    d = getattr(request.user, 'driver_profile', None)
    if not d:
        return JsonResponse({'error': 'Faqat haydovchi'}, status=403)
    t = Trip.objects.select_related('vehicle', 'route', 'driver').filter(company=d.company, driver=d, pk=pk).first()
    if not t:
        return JsonResponse({'error': 'Reys topilmadi'}, status=404)
    if t.status != 'IN_PROGRESS':
        return JsonResponse({'error': 'Faqat yo‘ldagi reysni yakunlash mumkin'}, status=400)
    t.status = 'DONE'; t.save(update_fields=['status'])
    t.vehicle.current_mileage = float(t.vehicle.current_mileage or 0) + float(t.km or 0)
    t.vehicle.save(update_fields=['current_mileage'])
    _audit(request, t, 'STATUS', 'Reys yakunlandi', {'from': 'IN_PROGRESS', 'to': 'DONE', 'km_added': t.km})
    return JsonResponse({'trip': _trip_json(t)})
