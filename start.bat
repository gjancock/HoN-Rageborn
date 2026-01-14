@echo off
cd /d "%~dp0"
call venv\Scripts\activate
start "" /HIGH python ragebirth.py
