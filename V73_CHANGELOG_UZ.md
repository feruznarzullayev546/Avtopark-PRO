# AVTOPARK PRO V73 — bildirishnomalar, filiallar va tarif to‘lovi

## Kiritilgan tuzatishlar
- Bildirishnoma API javobida foydalanuvchi roli bo‘yicha yuborish mumkin bo‘lgan rollar aniq qaytariladi. Super Admin va Direktor direktor/manager/haydovchilarni, Manager esa faqat haydovchilarni tanlay oladi.
- Filial yaratish endpointi faol kompaniya direktoriga, eski ro‘yxatdan o‘tgan akkauntlarda OrganizationMembership yo‘q bo‘lsa ham, o‘z kompaniyasi uchun filial ochishga ruxsat beradi.
- Direktor filiallar orasida almashganda alohida BranchMembership yozuvi bo‘lmasa ham, o‘z kompaniyasining filiallarini boshqara oladi.
- Filiallar oynasidagi kompaniya tanlovi faqat mavjud filiallar ro‘yxatiga bog‘liq bo‘lmaydi; kompaniya hali qo‘shimcha filialga ega bo‘lmasa ham tanlanadi.
- Tarif uchun invoice ichida tanlangan tarif kodi va billing sikli saqlanadi. Super Admin to‘lovni tasdiqlaganda obuna aynan shu invoice uchun so‘ralgan tarifga va oy/yil davriga o‘tadi. Oldingi xatoda obuna eski tarif kodida qolib ketishi mumkin edi.

## Tekshiruv
- O‘zgartirilgan Python fayllari `py_compile` tekshiruvidan o‘tdi.
- Django `manage.py check` bajarilmadi: muhitda Django paketi o‘rnatilmagan.
- Frontend build bajarilmadi: mavjud `node_modules` ichida `@types/react` va `@types/react-dom` to‘liq yo‘q. Loyihada `npm ci` bajarib qayta tekshirish kerak.
- Ishlayotgan serverda to‘lov tasdiqlash, role-based yuborish va filiallar yaratishni real akkauntlar bilan alohida smoke-test qilish kerak.
