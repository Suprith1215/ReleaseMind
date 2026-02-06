@echo off
echo === ReleaseMind Kubernetes Deployment Hook ===

REM Expect response.json in this directory
if not exist response.json (
  echo ❌ response.json not found. Copy it from ci-local first.
  exit /b 1
)

findstr /C:"\"deployment_strategy\":\"ROLLING\"" response.json > nul
if %errorlevel%==0 (
  echo 🚀 Applying ROLLING deployment
  kubectl apply -f deploy-rolling.yaml
  exit /b 0
)

findstr /C:"\"deployment_strategy\":\"CANARY\"" response.json > nul
if %errorlevel%==0 (
  echo 🟡 Applying CANARY deployment
  kubectl apply -f deploy-canary.yaml
  exit /b 0
)

findstr /C:"\"deployment_strategy\":\"BLUE_GREEN\"" response.json > nul
if %errorlevel%==0 (
  echo 🔵 Applying BLUE-GREEN deployment
  kubectl apply -f deploy-blue-green.yaml
  exit /b 0
)

findstr /C:"\"deployment_strategy\":\"BLOCK\"" response.json > nul
if %errorlevel%==0 (
  echo ❌ Deployment BLOCKED — no Kubernetes changes applied
  exit /b 1
)

echo ⚠️ Unknown deployment strategy
exit /b 1
