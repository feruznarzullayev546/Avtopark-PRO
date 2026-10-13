import json
from datetime import date
from io import BytesIO

from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

from core.models import MaintenanceSchedule, Vehicle, Part
from core.services import company_of, can_manage, is_super, notify_maintenance_staff, log_action
from .branch_scope import branch_kwargs, relation_branch_kwargs


def _json(request):
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return None


def _date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise ValueError('Sana noto\'g\'ri')


def _num(value, name, minimum=0):
    try:
        n = float(value)
    except (TypeError, ValueError):
        raise ValueError(f'{name} noto\'g\'ri')
    if n < minimum:
        raise ValueError(f'{name} {minimum:g} dan kichik bo\'lishi mumkin emas')
    return n


def _row(s):
    return {
        'id': s.id,
        'vehicle_id': s.vehicle_id,
        'vehicle': s.vehicle.number,
        'model': s.vehicle.model,
        'current_mileage': float(s.vehicle.current_mileage or 0),
        'avg_daily_km': float(s.avg_daily_km),
        'part_id': s.part_id,
        'part': s.part.name if s.part_id else '',
        'name': s.name,
        'interval_km': float(s.interval_km or 0),
        'last_mileage': float(s.last_mileage or 0),
        'last_date': s.last_date.isoformat() if s.last_date else None,
        'due_mileage': float(s.due_mileage),
        'projected_mileage': float(s.projected_mileage),
        'remaining_km': float(s.remaining_km),
        'remaining_days': s.remaining_days,
        'status': s.status_code,
        'status_label': {'YASHIL': 'Yashil', 'SARIQ': 'Sariq', 'QIZIL': 'Qizil'}.get(s.status_code, s.status_code),
        'needs_notification': s.needs_notification,
        'active': s.active,
    }


def _meta(request, c):
    return {
        'vehicles': [
            {'id': v.id, 'number': v.number, 'model': v.model,
             'mileage': float(v.current_mileage or 0), 'avg_daily_km': float(v.avg_daily_km or 0)}
            for v in Vehicle.objects.filter(company=c, **branch_kwargs(request), active=True).order_by('number')
        ],
        'parts': [
            {'id': p.id, 'name': p.name, 'code': p.code, 'unit': p.unit}
            for p in Part.objects.filter(company=c, **branch_kwargs(request)).order_by('name', 'code')
        ],
    }


@require_http_methods(['GET'])
def maintenance_list(request):
    if not request.user.is_authenticated or not can_manage(request):
        return JsonResponse({'error': 'Ruxsat yo\'q'}, status=403)
    c = company_of(request)
    if not c:
        return JsonResponse({'results': [], 'summary': {}, 'meta': {}})
    qs = MaintenanceSchedule.objects.filter(vehicle__company=c, **relation_branch_kwargs(request, 'vehicle__branch')).select_related('vehicle', 'part').order_by('vehicle__number', 'name')
    rows = [_row(x) for x in qs]
    active = [x for x in rows if x['active']]
    return JsonResponse({
        'results': rows,
        'summary': {
            'total': len(active),
            'green': sum(x['status'] == 'YASHIL' for x in active),
            'yellow': sum(x['status'] == 'SARIQ' for x in active),
            'red': sum(x['status'] == 'QIZIL' for x in active),
            'avg_daily_km_set': sum(x['avg_daily_km'] > 0 for x in active),
        },
        'meta': _meta(request, c),
    })


@csrf_protect
@require_http_methods(['POST'])
def maintenance_create(request):
    if not request.user.is_authenticated or not can_manage(request):
        return JsonResponse({'error': 'Ruxsat yo\'q'}, status=403)
    c = company_of(request); data = _json(request) or {}
    try:
        vehicle = Vehicle.objects.get(company=c, **branch_kwargs(request), pk=int(data.get('vehicle_id')), active=True)
        part = Part.objects.filter(company=c, **branch_kwargs(request), pk=int(data['part_id'])).first() if data.get('part_id') else None
        name = str(data.get('name', '')).strip()
        if not name: raise ValueError('Servis nomi majburiy')
        interval = _num(data.get('interval_km'), 'Interval km', 1)
        last_mileage = _num(data.get('last_mileage', vehicle.current_mileage), 'Oxirgi probeg', 0)
        last_date = _date(data.get('last_date'))
        if MaintenanceSchedule.objects.filter(vehicle=vehicle, name=name).exists():
            raise ValueError('Bu avtomobil uchun shu nomdagi servis rejasi allaqachon mavjud')
        s = MaintenanceSchedule.objects.create(vehicle=vehicle, part=part, name=name,
            interval_km=interval, last_mileage=last_mileage, last_date=last_date,
            active=bool(data.get('active', True)))
        log_action(request, 'CREATE', s, f'Servis rejasi: {s.name} / {vehicle.number}')
        return JsonResponse({'item': _row(s)}, status=201)
    except Vehicle.DoesNotExist:
        return JsonResponse({'error': 'Avtomobil topilmadi'}, status=404)
    except (ValueError, TypeError) as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_protect
@require_http_methods(['PATCH'])
def maintenance_update(request, pk):
    if not request.user.is_authenticated or not can_manage(request):
        return JsonResponse({'error': 'Ruxsat yo\'q'}, status=403)
    c = company_of(request); s = MaintenanceSchedule.objects.filter(vehicle__company=c, **relation_branch_kwargs(request, 'vehicle__branch'), pk=pk).select_related('vehicle').first()
    if not s: return JsonResponse({'error': 'Servis rejasi topilmadi'}, status=404)
    data = _json(request) or {}
    try:
        if 'vehicle_id' in data:
            s.vehicle = Vehicle.objects.get(company=c, **branch_kwargs(request), pk=int(data['vehicle_id']), active=True)
        if 'part_id' in data:
            s.part = Part.objects.filter(company=c, **branch_kwargs(request), pk=int(data['part_id'])).first() if data['part_id'] else None
        if 'name' in data:
            name = str(data['name']).strip()
            if not name: raise ValueError('Servis nomi majburiy')
            s.name = name
        if 'interval_km' in data: s.interval_km = _num(data['interval_km'], 'Interval km', 1)
        if 'last_mileage' in data: s.last_mileage = _num(data['last_mileage'], 'Oxirgi probeg', 0)
        if 'last_date' in data: s.last_date = _date(data['last_date'])
        if 'active' in data: s.active = bool(data['active'])
        duplicate = MaintenanceSchedule.objects.filter(vehicle=s.vehicle, name=s.name).exclude(pk=s.pk).exists()
        if duplicate: raise ValueError('Bu avtomobil uchun shu nomdagi servis rejasi mavjud')
        s.save()
        log_action(request, 'UPDATE', s, f'Servis rejasi tahrirlandi: {s.name} / {s.vehicle.number}')
        return JsonResponse({'item': _row(s)})
    except Vehicle.DoesNotExist:
        return JsonResponse({'error': 'Avtomobil topilmadi'}, status=404)
    except (ValueError, TypeError) as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_protect
@require_http_methods(['POST'])
def maintenance_complete(request, pk):
    if not request.user.is_authenticated or not can_manage(request):
        return JsonResponse({'error': 'Ruxsat yo\'q'}, status=403)
    c = company_of(request); s = MaintenanceSchedule.objects.filter(vehicle__company=c, **relation_branch_kwargs(request, 'vehicle__branch'), pk=pk).select_related('vehicle').first()
    if not s: return JsonResponse({'error': 'Servis rejasi topilmadi'}, status=404)
    data = _json(request) or {}
    try:
        mileage = _num(data.get('mileage', s.vehicle.current_mileage), 'Almashtirish probegi', 0)
        dt = _date(data.get('date')) or date.today()
        s.last_mileage = mileage
        s.last_date = dt
        s.save(update_fields=['last_mileage', 'last_date'])
        if mileage > float(s.vehicle.current_mileage or 0):
            s.vehicle.current_mileage = mileage
            s.vehicle.save(update_fields=['current_mileage'])
        log_action(request, 'UPDATE', s, f'Servis bajarildi: {s.name} / {s.vehicle.number} / {mileage:g} km')
        return JsonResponse({'item': _row(s)})
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(['POST'])
def maintenance_check_notifications(request):
    if not request.user.is_authenticated or not can_manage(request):
        return JsonResponse({'error': 'Ruxsat yo\'q'}, status=403)
    c = company_of(request)
    notify_maintenance_staff(c)
    return JsonResponse({'ok': True, 'message': 'Servis ogohlantirishlari tekshirildi'})


@require_http_methods(['GET'])
def maintenance_export(request):
    if not request.user.is_authenticated or not can_manage(request):
        return JsonResponse({'error': 'Ruxsat yo\'q'}, status=403)
    c = company_of(request)
    qs = MaintenanceSchedule.objects.filter(vehicle__company=c, **relation_branch_kwargs(request, 'vehicle__branch')).select_related('vehicle', 'part').order_by('vehicle__number', 'name')
    wb = Workbook(); ws = wb.active; ws.title = 'Servis nazorati'
    headers = ['Avtomobil', 'Model', 'Servis / detal', 'Detal kodi', 'Interval km', 'Oxirgi probeg', 'Oxirgi sana', 'Keyingi probeg', 'Prognoz probeg', 'Qolgan km', 'Qolgan kun', 'Holat']
    ws.append(headers)
    for cell in ws[1]: cell.font = Font(bold=True); cell.alignment = Alignment(horizontal='center')
    for s in qs:
        ws.append([s.vehicle.number, s.vehicle.model, s.name, s.part.code if s.part_id else '', s.interval_km,
                   s.last_mileage, s.last_date.isoformat() if s.last_date else '', s.due_mileage, s.projected_mileage,
                   s.remaining_km, s.remaining_days if s.remaining_days is not None else '', s.status_code])
    for col in ws.columns:
        letter = col[0].column_letter
        ws.column_dimensions[letter].width = min(max(max(len(str(x.value or '')) for x in col) + 2, 12), 28)
    buf = BytesIO(); wb.save(buf); buf.seek(0)
    response = HttpResponse(buf.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="avtopark_servis_nazorati.xlsx"'
    return response
