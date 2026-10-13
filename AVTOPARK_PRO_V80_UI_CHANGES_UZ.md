# AVTOPARK PRO v80 — UI/UX o‘zgarishlari

## Joriy etilgan
- `frontend/src/styles/avtopark-design-system.css` qo‘shildi va `App.tsx` oxirgi CSS override qatlamidan keyin import qilindi.
- Umumiy `page-head`, avtomobillar, reyslar va yo‘nalishlar bannerlari uchun yagona dark-blue gradient + tematik transport rasmi, responsiv sarlavha va tugmalar stili kiritildi.
- Sklad banneri mavjud operatsion tuzilmasi saqlangan holda shu dizayn tiliga moslashtirildi.
- Dashboard hero banneri bir xil vizual tizimga moslandi.
- Dashboard KPI’lari rahbariyat uchun: faol avtomobillar, joriy oydagi yoqilg‘i xarajati, bajarilgan reyslar va umumiy xarajat ko‘rsatkichlariga moslashtirildi. Mavjud Django API ma’lumotlari ishlatiladi; yangi soxta statistikalar kiritilmadi.
- `AppShell.tsx` mobil menyusiga `aria` atributlari, Escape bilan yopish va drawer ochilganda fon sahifasini skroll qilishni bloklash qo‘shildi.
- Mobil qurilmalarda sidebar off-canvas drawer ko‘rinishida, overlay bilan ishlaydi. Eski `layout-fix.css` dagi `!important` qoidalari uchun aniqroq yakuniy override yozildi.
- Avtomobillar uchun desktop jadvali saqlanib, mobil ekranlarda kartochkalar ro‘yxati ishlatiladi. Qidiruv, holat, haydovchi, probeg va ruxsatga bog‘liq amallar mavjud ma’lumotlardan olinadi.
- Reys, servis, yoqilg‘i, hisobot, kompaniya a’zolari va sklad jadvallari uchun gorizontal skroll va `min-width: 0` qoidalari mustahkamlandi.
- Mobil formalar, modal oynalar va tugmalar uchun touch-friendly o‘lchamlar qo‘shildi; `prefers-reduced-motion` qo‘llab-quvvatlanadi.

## Tekshiruv holati
- Frontend build urinishida muhitdagi `node_modules` Linux native optional paketlarini o‘z ichiga olmagani sababli Vite/TypeScript build boshlanmadi. Bu koddagi build xatosi ekanini tasdiqlamaydi; loyihani ishlab chiquvchi kompyuterda `npm ci` va `npm run build` bilan tekshirish kerak.
- Django backend, API, model va ma’lumotlar bazasi sxemasiga o‘zgartirish kiritilmadi.
- Rasmlar hozirda Unsplash URL orqali olinadi; tashqi rasm yuklanmasa, bannerning to‘q fon rangi saqlanadi.
