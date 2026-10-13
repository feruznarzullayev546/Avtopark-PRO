
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import (
    Vehicle,
    DriverProfile,
    Part,
    Receipt,
    Issue,
    WarehouseReturn,
    WarehouseAdjustment,
    Route,
    Trip,
    FuelEntry,
    OtherExpense,
)

BRANCH_MODELS = (
    Vehicle,
    DriverProfile,
    Part,
    Receipt,
    Issue,
    WarehouseReturn,
    WarehouseAdjustment,
    Route,
    Trip,
    FuelEntry,
    OtherExpense,
)


@receiver(pre_save)
def assign_default_branch(sender, instance, **kwargs):
    if sender not in BRANCH_MODELS:
        return

    # Filial oldindan belgilangan bo'lsa, uni o'zgartirmaymiz.
    if getattr(instance, "branch_id", None):
        return

    # Kompaniya biriktirilmagan bo'lsa, chiqib ketamiz.
    company_id = getattr(instance, "company_id", None)
    if not company_id:
        return

    company = getattr(instance, "company", None)

    if company is None:
        from .models import Company

        company = (
            Company.objects
            .filter(pk=company_id)
            .only("default_branch_id")
            .first()
        )

    # Kompaniyaning standart filiali mavjud bo'lsa, biriktiramiz.
    if company and company.default_branch_id:
        instance.branch_id = company.default_branch_id