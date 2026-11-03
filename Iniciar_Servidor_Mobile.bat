@echo off
title Night City RPG Mobile - Servidor de Sincronizacao (Obsidian + Mobile)
color 0B
echo ============================================================================
echo   NIGHT CITY RPG MOBILE // SERVIDOR DE SINCRONIZACAO ANDROID + OBSIDIAN
echo ============================================================================
echo.
echo Iniciando ponte em tempo real na porta 8077...
echo Abra no navegador (PC ou Android conectado ao mesmo Wi-Fi):
echo.
echo     http://localhost:8077
echo.
cd /d "%~dp0"
python server.py
pause
