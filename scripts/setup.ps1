# Oracle Fusion + Claude Code — Setup Script (PowerShell)
# This is a convenience wrapper. It just calls the main setup script in mcp-servers/fusion-mcp/.
# Run it from the project root: powershell -File scripts\setup.ps1

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'mcp-servers\fusion-mcp\setup-fusion.ps1')
