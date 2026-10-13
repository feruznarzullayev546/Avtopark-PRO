from django.db.models import Q, Sum, Value, FloatField
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import (
    AuditLog, CompanyMembership, DriverProfile, Issue, MaintenanceSchedule,
    Notification, UserProfile
)


def profile_of(request):
    if not request.user.is_authenticated or request.user.is_superuser:
        return None
    return UserProfile.objects.filter(user=request.user).first()


def active_membership(request):
    if not request.user.is_authenticated:
        return None
    cid = request.session.get('active_company_id')
    qs = CompanyMembership.objects.filter(
        user=request.user, status=CompanyMembership.STATUS_ACTIVE
    ).select_related('company')
    if cid:
        membership = qs.filter(company_id=cid).first()
        if membership:
            return membership
    profile = profile_of(request)
    if profile and profile.company_id:
        membership = qs.filter(company_id=profile.company_id).first()
        if membership:
            return membership
    return qs.order_by('-is_default', 'company__name').first()


def company_of(request):
    membership = active_membership(request)
    if membership:
        return membership.company
    if request.user.is_authenticated and request.user.is_superuser:
        from .models import Company
        company_id = request.session.get('active_company_id') or request.session.get('super_active_company_id')
        return Company.objects.filter(pk=company_id).first() if company_id else None
    return None


def role_of(request):
    membership = active_membership(request)
    return membership.role if membership else getattr(profile_of(request), 'role', None)


def is_super(request):
    return request.user.is_superuser or getattr(profile_of(request), 'role', None) == UserProfile.ROLE_SUPER_ADMIN


def can_manage(request):
    return is_super(request) or role_of(request) in {
        UserProfile.ROLE_DIRECTOR,
        UserProfile.ROLE_MANAGER,
        'ACCOUNTANT', 'WAREHOUSE', 'DISPATCHER'
    }


def can_direct(request):
    return is_super(request) or role_of(request) == UserProfile.ROLE_DIRECTOR


def log_action(request, action, obj, description):
    company = company_of(request)
    if company:
        AuditLog.objects.create(
            company=company,
            user=request.user,
            action=action,
            model_name=obj.__class__.__name__,
            object_id=str(obj.pk),
            description=description,
        )


def notify_profile(profile, title, message, url='', dedupe_key=''):
    if not profile:
        return
    if dedupe_key and Notification.objects.filter(recipient=profile, dedupe_key=dedupe_key).exists():
        return
    Notification.objects.create(
        company=profile.company,
        recipient=profile,
        title=title,
        message=message,
        url=url,
        dedupe_key=dedupe_key,
    )


def notify_driver(driver, title, message, url='', dedupe_key=''):
    if not driver:
        return
    if dedupe_key and Notification.objects.filter(driver=driver, dedupe_key=dedupe_key).exists():
        return
    Notification.objects.create(
        company=driver.company,
        driver=driver,
        title=title,
        message=message,
        url=url,
        dedupe_key=dedupe_key,
    )


def notify_maintenance_staff(company):
    if not company:
        return
    schedules = MaintenanceSchedule.objects.filter(
        vehicle__company=company,
        vehicle__active=True,
        active=True,
    ).select_related('vehicle', 'part')
    for schedule in schedules:
        if not schedule.needs_notification:
            continue
        status = schedule.status_code
        days = schedule.remaining_days
        detail = f'{max(schedule.remaining_km, 0):,.0f} km qoldi' if days is None else f'{max(days, 0)} kun qoldi'
        text = f'{schedule.vehicle.number} — {schedule.name}: {detail}. Holat: {status}.'
        key = f"maint-{schedule.pk}-{schedule.last_date or 'never'}-{status}"
        for profile in UserProfile.objects.filter(
            company=company,
            role__in=[UserProfile.ROLE_DIRECTOR, UserProfile.ROLE_MANAGER],
            is_active=True,
        ):
            notify_profile(profile, 'Texnik xizmat ogohlantirishi', text, '/maintenance', key)


def sync_maintenance_from_issues(schedule):
    """Recalculate a maintenance schedule from its linked warehouse issues."""
    latest = Issue.objects.filter(maintenance=schedule).order_by('-date', '-id').first()
    if latest:
        schedule.last_mileage = latest.odometer or 0
        schedule.last_date = latest.date
        schedule.save(update_fields=['last_mileage', 'last_date'])
