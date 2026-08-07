@echo off
REM Cross-platform Python launcher for AI log hooks (Windows cmd.exe).
REM Prefer the project's venv, then try py/python/python3 on PATH.
REM Fail loudly when no interpreter works so logging cannot disappear silently.

setlocal EnableDelayedExpansion
set "VENV_PY=%~dp0..\.venv\Scripts\python.exe"

if exist "%VENV_PY%" (
  "%VENV_PY%" -c "import sys" >nul 2>nul
  if not errorlevel 1 (
    "%VENV_PY%" %*
    exit /b !ERRORLEVEL!
  )
)

set "CODEX_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%CODEX_PY%" (
  "%CODEX_PY%" -c "import sys" >nul 2>nul
  if not errorlevel 1 (
    "%CODEX_PY%" %*
    exit /b !ERRORLEVEL!
  )
)

where py >nul 2>nul
if not errorlevel 1 (
  py -3 -c "import sys" >nul 2>nul
  if not errorlevel 1 (
    py -3 %*
    exit /b !ERRORLEVEL!
  )
)

for %%P in (python python3) do (
  where %%P >nul 2>nul
  if not errorlevel 1 (
    %%P -c "import sys" >nul 2>nul
    if not errorlevel 1 (
      %%P %*
      exit /b !ERRORLEVEL!
    )
  )
)

echo [ai-log] No working Python interpreter found. Recreate .venv or install Python 3.11+. 1>&2
exit /b 127
