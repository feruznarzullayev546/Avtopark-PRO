@echo off
cd /d %~dp0
python manage.py create_trial_notifications
