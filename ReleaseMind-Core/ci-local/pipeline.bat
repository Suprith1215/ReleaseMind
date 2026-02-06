@echo off
echo === ReleaseMind Local CI Simulation ===

REM ---------------- CONTEXT (simulating CI metadata) ----------------
set INTENT=feature
set SERVICE=order
set EXPERIENCE=senior
set OWNS_SERVICE=true
set CONFIG_DRIFT=false
set PEAK_HOURS=false

echo Change Intent: %INTENT%
echo Service: %SERVICE%
echo Contributor: %EXPERIENCE%
echo --------------------------------------------------

REM ---------------- CREATE REQUEST PAYLOAD ----------------
(
echo {
echo   "change": {
echo     "intent": "%INTENT%",
echo     "services": ["%SERVICE%"]
echo   },
echo   "human": {
echo     "experience": "%EXPERIENCE%",
echo     "owns_service": %OWNS_SERVICE%
echo   },
echo   "environment": {
echo     "config_drift": %CONFIG_DRIFT%,
echo     "resource_drift": false
echo   },
echo   "timing": {
echo     "peak_hours": %PEAK_HOURS%,
echo     "weekend": false
echo   }
echo }
) > request.json

REM ---------------- CALL RELEASEMIND ----------------
curl -s -X POST http://localhost:7000/decide ^
-H "Content-Type: application/json" ^
-d @request.json > response.json

echo.
echo === ReleaseMind Response ===
type response.json
echo.

REM ---------------- CHECK STRATEGY ----------------
findstr /C:"\"deployment_strategy\":\"BLOCK\"" response.json > nul
if %errorlevel%==0 (
  echo ❌ Deployment BLOCKED by ReleaseMind
  exit /b 1
)

echo ✅ Deployment ALLOWED
exit /b 0
