@echo off
echo === ReleaseMind Controlled Pipeline ===

echo Calling ReleaseMind Brain...

curl -s -X POST http://127.0.0.1:7000/decide ^
-H "Content-Type: application/json" ^
-d "{\"change\":{\"intent\":\"refactor\",\"services\":[\"auth\"]},\"human\":{\"experience\":\"new\",\"owns_service\":false},\"environment\":{\"config_drift\":true,\"resource_drift\":false},\"timing\":{\"peak_hours\":true,\"weekend\":false}}" > decision.json

type decision.json

for /f "tokens=2 delims=:," %%A in ('findstr /i "deployment_strategy" decision.json') do set STRATEGY=%%~A
set STRATEGY=%STRATEGY:"=%

echo.
echo Deployment strategy decided by ReleaseMind: %STRATEGY%
echo.

if "%STRATEGY%"=="BLOCK" (
    echo ❌ Deployment BLOCKED by ReleaseMind
    exit /b 1
)

if "%STRATEGY%"=="CANARY" (
    echo 🟡 Canary deployment would run here
)

if "%STRATEGY%"=="BLUE_GREEN" (
    echo 🔵🟢 Blue-Green deployment would run here
)

if "%STRATEGY%"=="FAST" (
    echo ⚡ Fast deployment would run here
)

echo ✅ Pipeline completed successfully
