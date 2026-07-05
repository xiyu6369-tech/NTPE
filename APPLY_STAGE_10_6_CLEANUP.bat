@echo off
cd /d "%~dp0"
python tools\maintenance\project_cleanup.py
pause
