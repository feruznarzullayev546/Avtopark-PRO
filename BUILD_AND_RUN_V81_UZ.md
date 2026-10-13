# AVTOPARK PRO V81 — ishga tushirish va tekshirish

## Frontend (Windows PowerShell)

```powershell
cd frontend
npm ci
npm run build
npm run dev
```

Agar `npm ci` registry/tarmoq sababli ishlamasa, avval internet/proxy va npm registry sozlamalarini tekshiring. `node_modules`ni boshqa operatsion tizimdan ko‘chirib ishlatmang.

## Backend (Windows PowerShell)

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py runserver
```

## Docker (Linux server yoki Docker Desktop)

1. Loyihaning ildizidagi `.env.example` faylidan `.env` yarating.
2. `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` va `CORS_ALLOWED_ORIGINS` qiymatlarini muhitga moslang.
3. `infra/docker-compose.yml` turgan joydan emas, Compose fayliga mos loyiha ildizidan quyidagini bajaring:

```bash
docker compose -f infra/docker-compose.yml up --build
```

## Muhim sinov holati

- `python -m compileall -q backend` sintaksis tekshiruvi muvaffaqiyatli bajarildi.
- Frontend build bu ish muhitida tekshiruvdan o‘tmadi: `@types/react` va `@types/react-dom` tip deklaratsiyalari yo‘q/yaroqsiz ko‘rindi; npm registry orqali qayta o‘rnatish ham vaqt chekloviga uchradi. Shuning uchun production build muvaffaqiyatli deb hisoblanmaydi.
- PostgreSQL, Redis, Celery, brauzer va real tenantlar bilan end-to-end testlar bajarilmagan.
- OCR task hozircha integratsiya nuqtasi/skelet; OCR providerini ulash, natijani saqlash va mismatch workflow’ni alohida yakunlash kerak.

## Xavfsizlik eslatmalari

- `DEBUG=False` holatida development secret bilan ishga tushirmang.
- Productionda HTTPS, aniq `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` va CORS originlarini belgilang.
- Tenant va branch ruxsatlarini faqat middlewarega topshirmang: har bir query va mutation scoped queryset/object permission bilan himoyalangan bo‘lishi shart.
