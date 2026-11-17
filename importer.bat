@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Importation des memoires
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
  echo Python est introuvable. Installez Python 3 depuis https://www.python.org puis relancez.
  pause
  exit /b 1
)
set "SRC=%~1"
if "%SRC%"=="" set /p "SRC=Chemin du fichier a importer (.xlsx ou .db) : "
set "SRC=%SRC:"=%"
set "OPT=--excel"
for %%F in ("%SRC%") do (
  if /i "%%~xF"==".db" set "OPT=--base"
  if /i "%%~xF"==".sqlite" set "OPT=--base"
  if /i "%%~xF"==".sqlite3" set "OPT=--base"
)
%PY% catalogue.py importer %OPT% "%SRC%" %2
pause
