# AVTOPARK PRO — gaz zapravkasi nazorati

## Kiritilgan imkoniyatlar
- Kompaniya bo‘yicha gaz stansiyalarini ro‘yxatga olish va haydovchi tanlashi.
- Haydovchi biriktirilgan avtomobili uchun nasos displeyi suratini va m³ miqdorini yuboradi.
- Sana va vaqt brauzerdan olinmaydi: backend `Asia/Tashkent` server vaqtini yozadi.
- Asl surat saqlanadi; OCR mavjud bo‘lsa `pytesseract` orqali matn/qiymat o‘qishga urinadi, kiritilgan qiymat bilan taxminan solishtiradi. OCR natijasi avtomatik yakuniy tasdiq emas; `MISMATCH`/`UNREADABLE` yozuvlarini rahbar tekshirishi kerak.
- Direktor hisobotida barcha yoki bir nechta avtomobil bo‘yicha zapravkalar, rasm soni, m³ va haydovchilar ko‘rsatiladi.
- XLSX eksportida `Avtomobillar` va `Zapravkalar` varaqlari mavjud.
- `python manage.py cleanup_fuel_photos --dry-run` bir yildan eski rasmlarni sanaydi; `python manage.py cleanup_fuel_photos` fayllarni o‘chirib, hisob yozuvlarini qoldiradi.

## O‘rnatish
1. `pip install -r requirements.txt`
2. `python manage.py migrate`
3. OCR uchun serverga Tesseract OCR executable ham o‘rnatilib, PATH ga qo‘shilishi kerak. Kutubxona yoki executable bo‘lmasa, zapravka yozuvi baribir saqlanadi, OCR holati `PENDING` bo‘ladi.
4. Production da media fayllarini private object storage yoki autentifikatsiyalangan media endpoint orqali berish kerak. `MEDIA_URL` ni ommaga ochiq qoldirish maxfiylik talablariga mos kelmasligi mumkin.
5. Foto saqlash siyosati: 365 kundan eski rasmlarni cleanup buyrug‘i bilan o‘chirish; raqamli hisobot satrlarini saqlash. Buyruqni scheduler/cron orqali rejalashtirish deployment vaqtida sozlanadi.

## Eslatma
OCR ishonchliligi haqiqiy gaz dispenserlari suratlari bilan sinovdan o‘tkazilishi shart. OCR topgan sonlardan eng yaqin qiymat tanlanadi, shu sababli natija tekshiruv uchun yordamchi signal hisoblanadi, rasmning o‘rnini bosmaydi.
