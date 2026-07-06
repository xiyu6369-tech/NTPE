@echo off
setlocal
cd /d %~dp0

echo ====================================
echo NTPE Stage-18.8 Enterprise Deployment Freeze
echo ====================================
python ntpe_stage18_8_enterprise_deployment_freeze_test.py || exit /b 1
python tests\integration\launcher_stage18_8_enterprise_deployment_freeze_test.py || exit /b 1
python tests\smoke\launcher_stage18_8_enterprise_deployment_freeze_smoke_test.py || exit /b 1
python ntpe_validate.py || exit /b 1

echo Stage-18.8 validation completed.
endlocal
