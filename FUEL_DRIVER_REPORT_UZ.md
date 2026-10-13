# Yoqilg‘i cheki va haydovchi hisoboti

- Yoqilg‘i yozuvlariga chek rasmi fayli, miqdor birligi (litr yoki m³) va yozuvni kiritgan foydalanuvchi qo‘shildi.
- Yoqilg‘i sahifasida rasm tanlash/kamera orqali olish, gaz uchun m³, benzin/dizel uchun litr ko‘rsatish va chekni ochish qo‘shildi.
- CSV hisobotiga miqdor birligi, chek rasmi havolasi va kiritgan foydalanuvchi qo‘shildi.
- `backend/core/migrations/0016_fuel_receipt_submission.py` migratsiyasini qo‘llash kerak.

## Ishga tushirish

`cd backend`
`python manage.py migrate`

Media fayllarni ko‘rsatish production serverda web-server orqali `/media/` yo‘lini sozlashni talab qiladi. Yozuvni kiritish endpointi mavjud kompaniya ruxsatlariga bo‘ysunadi; haydovchi akkauntlariga mustaqil yuborish ruxsati berilmagan bo‘lsa, bu alohida rol siyosati sifatida sozlanishi kerak.
