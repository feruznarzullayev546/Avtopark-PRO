# AVTOPARK PRO — hozircha SQLite

Hozircha Django'ning standart SQLite bazasi ishlatiladi:
`backend/db.sqlite3`.

## Ishga tushirish
1. `backend` papkasiga kiring.
2. Virtual environmentni faollashtiring.
3. `pip install -r requirements.txt`
4. `python manage.py migrate`
5. `python manage.py runserver`

Birinchi ishga tushishda `db.sqlite3` Django tomonidan migratsiyalar asosida yaratiladi. Mavjud `db.sqlite3` faylingiz bo'lsa, uni o'chirmang va yangi arxivdan ustiga ko'chirmang — mavjud ma'lumotlar bazasini alohida zaxiralang.

`DATABASE_URL` orqali PostgreSQL majburan tanlanmaydi; sozlamalarda SQLite aniq belgilangan. PostgreSQL'ga o'tish keyin alohida, zaxira nusxa va ma'lumotlarni solishtirish bilan amalga oshiriladi.

## Eslatma
SQLite hozirgi ishlab chiqish bosqichi uchun qoldirildi. Bir vaqtning o'zida ko'p yozuvlar, Celery workerlar va yuqori parallel yuklama oshsa, `database is locked` holatlari yuz berishi mumkin. Bunday yuklamada keyinchalik PostgreSQL'ga rejalashtirilgan migratsiya kerak bo'ladi.
