@echo off
title Connect Oracle Fusion to Claude Code
echo.
echo  Oracle Fusion + Claude Code Setup
echo  ==================================
echo.
echo  This will configure your Fusion connection.
echo  You'll need: pod URL, user name, and password.
echo  (Or set FUSION_POD_URL and FUSION_USER in .env first)
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0mcp-servers\fusion-mcp\setup-fusion.ps1"
echo.
pause
