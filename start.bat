@echo off
REM ============================================================
REM  Meridian Churn Dashboard - local launcher
REM  Starts the FastAPI backend (port 8137) and the React
REM  frontend (port 5173) in two windows, then opens the browser.
REM ============================================================
setlocal
cd /d "%~dp0"

REM --- pick a Python (prefer 3.13, which matches the trained model) ---
set "PY="
py -3.13 --version >nul 2>&1 && set "PY=py -3.13"
if not defined PY ( py -3 --version >nul 2>&1 && set "PY=py -3" )
if not defined PY ( python --version >nul 2>&1 && set "PY=python" )
if not defined PY (
  echo [ERROR] Python was not found on PATH. Install Python 3.11+ and retry.
  pause & exit /b 1
)
echo Using Python: %PY%

REM --- check Node ---
where npm >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js / npm not found on PATH. Install Node 18+ and retry.
  pause & exit /b 1
)

REM ---------------- BACKEND ----------------
pushd app\backend

echo Checking backend dependencies...
%PY% -c "import fastapi, uvicorn, sklearn, lightgbm, pandas, joblib" >nul 2>&1
if errorlevel 1 (
  echo Installing backend dependencies...
  %PY% -m pip install -r requirements.txt
)

if not exist "artifacts\app_model.joblib" (
  echo Training the model ^(first run, ~30s^)...
  %PY% train.py
)

echo Starting backend on http://localhost:8137 ...
start "Meridian API" cmd /k "%PY% -m uvicorn main:app --port 8137"
popd

REM ---------------- FRONTEND ----------------
pushd app\frontend
if not exist "node_modules" (
  echo Installing frontend dependencies ^(first run, ~1 min^)...
  call npm install
)
echo Starting frontend on http://localhost:5173 ...
start "Meridian UI" cmd /k "npm run dev"
popd

REM --- give the servers a moment, then open the browser ---
timeout /t 8 /nobreak >nul
start "" http://localhost:5173

echo.
echo ============================================================
echo  Both servers are launching in separate windows:
echo    - Meridian API  (backend)  http://localhost:8137
echo    - Meridian UI   (frontend) http://localhost:5173
echo  Close those two windows to stop the servers.
echo ============================================================
endlocal
