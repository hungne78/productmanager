@echo off

rem This file is UTF-8 encoded, so we need to update the current code page while executing it
for /f "tokens=2 delims=:." %%a in ('"%SystemRoot%\System32\chcp.com"') do (
    set _OLD_CODEPAGE=%%a
)
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" 65001 > nul
)

<<<<<<<< HEAD:productmanager/venv312/Scripts/activate.bat
set VIRTUAL_ENV=C:\venv\productmanager\productmanager\venv312
========
set VIRTUAL_ENV=C:\venvs\productmanager
>>>>>>>> 630479e9d35bab8c912a30730046401a7e139359:productmanager/productmanager/Scripts/activate.bat

if not defined PROMPT set PROMPT=$P$G

if defined _OLD_VIRTUAL_PROMPT set PROMPT=%_OLD_VIRTUAL_PROMPT%
if defined _OLD_VIRTUAL_PYTHONHOME set PYTHONHOME=%_OLD_VIRTUAL_PYTHONHOME%

set _OLD_VIRTUAL_PROMPT=%PROMPT%
<<<<<<<< HEAD:productmanager/venv312/Scripts/activate.bat
set PROMPT=(venv312) %PROMPT%
========
set PROMPT=(productmanager) %PROMPT%
>>>>>>>> 630479e9d35bab8c912a30730046401a7e139359:productmanager/productmanager/Scripts/activate.bat

if defined PYTHONHOME set _OLD_VIRTUAL_PYTHONHOME=%PYTHONHOME%
set PYTHONHOME=

if defined _OLD_VIRTUAL_PATH set PATH=%_OLD_VIRTUAL_PATH%
if not defined _OLD_VIRTUAL_PATH set _OLD_VIRTUAL_PATH=%PATH%

set PATH=%VIRTUAL_ENV%\Scripts;%PATH%
<<<<<<<< HEAD:productmanager/venv312/Scripts/activate.bat
set VIRTUAL_ENV_PROMPT=(venv312) 
========
set VIRTUAL_ENV_PROMPT=(productmanager) 
>>>>>>>> 630479e9d35bab8c912a30730046401a7e139359:productmanager/productmanager/Scripts/activate.bat

:END
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" %_OLD_CODEPAGE% > nul
    set _OLD_CODEPAGE=
)
