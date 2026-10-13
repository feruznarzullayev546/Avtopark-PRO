# AVTOPARK PRO V70 — arxitektura va xavfsizlik auditi

## Qamrov va ishonch darajasi
V78 ZIP ichidagi kod statik ko‘rib chiqildi. PostgreSQL, Redis, brauzer, real OCR va parallel yuklama bilan integratsion/penetratsion testlar bajarilmadi. Kodda ko‘ringan holatlar va tavsiyalar quyida alohida berilgan.

## P0 — productionga chiqarishdan oldin
1. **Tenant isolation:** `BranchContextMiddleware` X-Branch-ID ni tekshiradi, lekin middleware yakka o‘zi tenant xavfsizligini kafolatlamaydi. Har bir GET/PATCH/DELETE/create queryset kompaniya va filial bo‘yicha scope qilinishi shart; object IDOR testlari yo‘q/ko‘rsatilmagan. `active_branch` — UX konteksti, permission manbai emas.
2. **Production settings:** kodda `ALLOWED_HOSTS=["*"]` va `CORS_ALLOW_ALL_ORIGINS=True` bor edi; V79’da env orqali boshqarish va wildcard CORS’ni o‘chirish qo‘shildi. Production `DJANGO_SECRET_KEY`, `ALLOWED_HOSTS`, HTTPS origins va `DEBUG=False` qiymatlarini berishi kerak.
3. **DB:** SQLite development fallback sifatida qoldi; `DATABASE_URL` berilganda PostgreSQL ishlaydi. Production deploy PostgreSQL bilan bajarilsin. SQLite → PostgreSQL ko‘chirish alohida backup, data reconciliation, constraint validation va rollback rehearsal talab qiladi.
4. **OCR/upload:** `api/fuel.py` rasmni base64 orqali qabul qilib request ichida saqlaydi; rasm validatsiyasi MIME headerga tayanadi va OCR background pipeline to‘liq mavjudligi tasdiqlanmadi. V79 Celery bootstrap va task scaffold qo‘shadi, lekin OCR engine/task ichidagi parsing ataylab TODO sifatida qoldi. MIME sniffing, image decode/pixel limit, upload throttling va private object storage zarur.
5. **Channels:** ASGI’da `AuthMiddlewareStack` bor, routing chat consumer’ga ulangan. `REDIS_URL` bo‘lmasa InMemory layer workerlar orasida event tarqatmaydi. Productionda Redis, WebSocket origin validation, rate limits va disconnect/load tests shart.
6. **Billing:** to‘lov tasdiqlash idempotent va server-side bo‘lishi kerak: unique provider reference/idempotency key, atomic transaction, Payment state machine va audit. Frontend yuborgan `PAID` status hech qachon yakka o‘zi subscription’ni faollashtirmasligi kerak.

## P1 — ORM va backend
- FK indekslari Django tomonidan odatda avtomatik yaratiladi; composite indexlar real filter/order naqshlariga asoslanishi kerak. Mavjud `0005_performance_indexes.py`da trip, notification, auditlog va fuel uchun composite indekslar bor. Takroriy indekslarni `EXPLAIN (ANALYZE, BUFFERS)` natijasiz qo‘shmang.
- `fuel.py` `_row()` har bir yozuv uchun `_previous_entry()` so‘rovi yuboradi: listdagi N ta entry uchun N qo‘shimcha query yuzaga kelishi mumkin. Vehicle/date bo‘yicha bulk query yoki window-function annotation ishlating.
- Fuel list `limit=5000` bilan serializatsiya qiladi. Server-side pagination va summary uchun DB aggregate endpointlar qo‘shing.
- FK uchun `select_related`, M2M/reverse FK uchun `prefetch_related`; Python loopdagi sum/count’larni DB `Sum/Count/Avg` bilan almashtiring.
- Tenant resolve’ni `api/tenancy.py` kabi bitta servisga jamlang; har bir mutationda `filter(company=tenant, branch=branch, pk=pk)` bilan scoped lookup ishlating.
- Audit log: actor, tenant, branch, action, object type/id, timestamp, request ID. Secret, session cookie va chek rasm byteslarini loglamang.

## P1 — Channels va Celery
- OCR workflow: image upload → DB commit → `transaction.on_commit(lambda: process_fuel_receipt.delay(entry.pk))`. Task faqat ID olsin; OCR natijasi idempotent yozilsin; `PENDING/PROCESSING/MATCHED/MISMATCH/NEEDS_REVIEW/FAILED` statuslari va timeout/retry metrikalari bo‘lsin.
- WebSocket consumer’da chat ruxsati connect va message yozish paytida qayta tekshiriladi — yaxshi himoya. Shunga qaramay origin validation, per-user throttling, max connection count va multi-worker Redis testlari kerak.

## Frontend / TypeScript
- V79 page-level `React.lazy`/`Suspense` boshlang‘ich split qo‘shadi; build/route smoke-test bilan tekshirish kerak.
- TanStack Query server state uchun: cache, stale time, retry, invalidation va request deduplication. Local form state’ni Reduxga majburan ko‘chirmang; cross-page complex workflow bo‘lsa Redux Toolkit.
- `drf-spectacular` OpenAPI schema + `openapi-typescript` orqali TS DTO generatsiyasi. `api.ts` uchun timeout/AbortSignal, typed errors, `credentials:'include'`, CSRF va API base URL env qo‘shing.
- `RussianResponseMiddleware` HTML body text replace usulida ishlaydi; bu React SPA/API tarjimasi uchun ishonchli i18n emas. Frontend `i18next`/`react-intl` kataloglari bilan almashtiring.

## DevOps / CI
- `infra/` ichiga backend/frontend Dockerfile va PostgreSQL+Redis+Celery+backend+frontend compose qo‘shildi. Productionda TLS reverse proxy, secrets manager, non-root, private network, volume backup/restore va health endpoints qo‘shish zarur.
- CI: `python manage.py check --deploy`, migration check, Ruff, pytest + PostgreSQL service; frontend `npm ci`, `npm run build`, Vitest/React Testing Library.
- DB migration rehearsal: backup → import → row count/hash reconciliation → FK/unique checks → cutover rehearsal → rollback. SQLite faylini PostgreSQL o‘rniga shunchaki ko‘chirib bo‘lmaydi.

## Tavsiya etilgan keyingi tuzilma
```text
backend/config/{settings,asgi,wsgi,celery}.py
backend/api/{serializers,permissions,selectors,services}/
backend/core/{models.py,tasks.py,services/}
backend/tests/{unit,integration,security}/
frontend/src/features/{fleet,fuel,warehouse,billing,reports,chat}/
frontend/src/shared/{api,components,i18n,types}/
infra/{Dockerfile.backend,Dockerfile.frontend,docker-compose.yml}
.github/workflows/ci.yml
```

## Test matritsasi
- Tenant A/B IDOR: GET/PATCH/DELETE other tenant records all return 404/403.
- Branch A/B isolation; director branch policy tested separately.
- Billing only activates subscription after verified payment; duplicate webhook safe.
- Anonymous / wrong-origin / other-tenant WebSocket is rejected.
- OCR invalid MIME, corrupted image, too many pixels, oversized upload, mismatch and duplicate task.
- Fresh PostgreSQL migration from empty DB; query-count regression tests for list endpoints.
- Frontend serializer fixture matches generated TS types.
