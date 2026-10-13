# AVTOPARK PRO V70.2 — vizual moslashtirish

## Ushbu bosqichdagi o'zgarishlar
- Ilovaning yuqori navigatsiya paneli qo'shildi: sana, kompaniya/filial konteksti, menyu qidiruvi, bildirishnomalar va foydalanuvchi profili.
- Menyu qidiruvi funksional: yozilgan matnga qarab ruxsat etilgan yon menyu bo'limlari filtrlanadi.
- Desktop, planshet va mobil ekranlar uchun yuqori panel va kontent oralig'i moslashtirildi.
- Yon menyudagi rolga asoslangan ko'rinish filtri aniqroq yozildi; serverdagi API ruxsatlarini bu UI filtri almashtirmaydi.
- Avvalgi sahifalar, API xizmatlari va mavjud backend fayllari saqlandi.

## Tekshiruv
- Manba kodiga o'zgartirishlar kiritildi.
- Ushbu muhitda frontend dependency'lari o'rnatilmaganligi sababli `npm run build` bajarilmadi. Ishga tushirishdan oldin `cd frontend && npm install && npm run build` bilan tekshiring.
- Backend serverida integratsion test va WebSocket testi bajarilmagan. Buni ishlayotgan muhitda alohida tekshirish zarur.
