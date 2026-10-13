@echo off
setlocal
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py repair_avtopark
python manage.py createsuperuser
python manage.py runserver
