@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Catalogue public
echo === Catalogue public ===
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
  echo Python est introuvable. Installez Python 3 depuis https://www.python.org puis relancez.
  pause
  exit /b 1
)
if not exist "dist\index.html" (
  echo Premier lancement : construction du site ^(une seule fois, Node.js requis^)...
  where npm >nul 2>nul || (
    echo Node.js est introuvable. Installez la version LTS depuis https://nodejs.org puis relancez.
    pause
    exit /b 1
  )
  if not exist node_modules (
    call npm install
    if errorlevel 1 (
      echo Echec de npm install.
      pause
      exit /b 1
    )
  )
  call npm run build
  if errorlevel 1 (
    echo Echec de la construction du site.
    pause
    exit /b 1
  )
)
%PY% catalogue.py demarrer
pause
