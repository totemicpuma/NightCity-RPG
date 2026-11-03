@echo off
title Compilar APK Standalone - Night City RPG Mobile
color 0E
echo ============================================================================
echo   COMPILANDO NIGHT CITY RPG STANDALONE APK (100%% OFFLINE)
echo ============================================================================
cd /d "%~dp0"
python build_standalone_apk.py
echo.
echo O arquivo NightCityRPG-Standalone.apk foi gerado na pasta dist/!
pause
