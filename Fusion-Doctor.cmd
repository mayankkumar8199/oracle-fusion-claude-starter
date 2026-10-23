@echo off
title Oracle Fusion Connection Doctor
set "KIT=%~dp0mcp-servers\fusion-mcp"
if not exist "%KIT%\.venv\Scripts\python.exe" (
  echo Python environment missing - rebuilding it ...
  where uv >nul 2>&1 && (
    uv --directory "%KIT%" sync --frozen
  ) || (
    "%USERPROFILE%\.local\bin\uv.exe" --directory "%KIT%" sync --frozen
  )
)
"%KIT%\.venv\Scripts\python.exe" "%KIT%\fusion_setup_helper.py" doctor --fix
echo.
pause
