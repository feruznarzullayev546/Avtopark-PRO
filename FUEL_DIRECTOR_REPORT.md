# Direktor uchun yoqilg'i hisobotlari

## Ushbu versiyadagi o'zgarishlar
- Yoqilg'i nazorati sahifasiga bir nechta avtomobilni belgilash paneli qo'shildi.
- Tanlangan avtomobillar bo'yicha zapravka yozuvlari va eksport filtrlash qo'llab-quvvatlandi.
- Avtomobil kesimida zapravka soni, mavjud rasm soni, gaz miqdori (m³) va yozuvlardagi turli foydalanuvchilar soni ko'rsatiladi.
- Haydovchi/yozuv kiritgan foydalanuvchi kesimida zapravkalar, rasm dalillari, avtomobillar soni va m³ jamlanadi.
- Backend ro'yxat limiti 500 dan 5000 yozuvgacha oshirildi.

## Tekshiruv holati
- `backend/api/fuel.py` uchun Python sintaksis tekshiruvi o'tdi.
- Django `manage.py check` bajarilmadi: ishchi muhitda Django o'rnatilmagan.
- Frontend build tekshiruvi o'tmadi: `node_modules` yo'q, React va boshqa frontend bog'liqliklari topilmadi. Shuning uchun ushbu arxivni productionga chiqarishdan oldin bog'liqliklarni o'rnatib, build va brauzer sinovini bajarish kerak.

## Muhim eslatma
Hozirgi `submitted_by` maydoni yozuvni tizimga kiritgan foydalanuvchini ko'rsatadi. Agar haydovchi mustaqil zapravka yuborishi kerak bo'lsa, haydovchi roli uchun alohida xavfsiz endpoint va biriktirilgan avtomobilni tekshirish oqimi alohida joriy qilinishi lozim. Joriy hisobot sahifasi yangi OCR tekshiruvi yoki dispenser displeyini majburiy suratga olish jarayonini o'z-o'zidan joriy qilmaydi.
