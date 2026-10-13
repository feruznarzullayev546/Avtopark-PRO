@echo off
cd /d %~dp0
python manage.py check_maintenance_notifications
