@echo off
title ROMUSIC — Midnight Luxe Platform
cd /d "%~dp0"
echo ========================================================
echo  ROMUSIC — NEXT-GENERATION MUSIC STREAMING ARCHITECTURE
echo ========================================================
echo.
echo Starting ROMUSIC local server on http://127.0.0.1:5000 ...
echo.
python app.py
pause

