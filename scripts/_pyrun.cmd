@echo off
REM Cross-platform Python launcher for AI log hooks (Windows cmd.exe).
REM Prefer the project venv, then PATH Python, then py -3.
REM Exits 0 silently if no Python is found - hooks must never block the AI tool.

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" %*
  exit /b %ERRORLEVEL%
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

where python3 >nul 2>nul
if %ERRORLEVEL%==0 (
  python3 %*
  exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 %*
  exit /b %ERRORLEVEL%
)

exit /b 0
