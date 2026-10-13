"""Celery entry points. This is an OCR task scaffold, not a complete OCR engine."""
from celery import shared_task
from django.db import close_old_connections

@shared_task(bind=True, autoretry_for=(OSError,), retry_backoff=True, retry_jitter=True, max_retries=5)
def process_fuel_receipt(self, fuel_entry_id: int) -> dict:
    close_old_connections()
    from core.models import FuelEntry
    entry = FuelEntry.objects.filter(pk=fuel_entry_id).only("id", "receipt_image", "ocr_status").first()
    if not entry:
        return {"ok": False, "reason": "not_found", "id": fuel_entry_id}
    if not entry.receipt_image:
        entry.ocr_status = "NEEDS_REVIEW"
        entry.save(update_fields=["ocr_status"])
        return {"ok": False, "reason": "missing_image", "id": fuel_entry_id}
    # TODO: fetch private object, run OCR adapter, normalize reading, persist status/result.
    return {"ok": True, "queued_for_ocr": True, "id": entry.pk}
