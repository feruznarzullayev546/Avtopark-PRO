@echo off
setlocal
call .venv\Scripts\activate
python manage.py migrate --noinput
python manage.py repair_avtopark
python manage.py runserver
