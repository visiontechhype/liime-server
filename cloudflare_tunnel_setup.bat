@echo off
REM Cloudflare Tunnel Setup for Liime Server

REM 1. Rename cloudflared to cloudflared.exe
ren cloudflared-windows-amd64.exe cloudflared.exe

REM 2. Login to Cloudflare (opens browser)
cloudflared.exe tunnel login

REM 3. Create tunnel
cloudflared.exe tunnel create liime-server

REM 4. Create config file
echo Creating config.yml...
(
echo tunnel: liime-server
echo credentials-file: %%USERPROFILE%%\.cloudflared\credentials.json
echo.
echo ingress:
echo   - hostname: liime.duckdns.org
echo     service: http://localhost:8000
echo   - service: http_status:404
) > config.yml

REM 5. Add DNS record
cloudflared.exe tunnel route dns liime-server liime.duckdns.org

REM 6. Run tunnel (keep this running)
cloudflared.exe tunnel run liime-server
