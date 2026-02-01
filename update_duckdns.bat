@echo off
REM DuckDNS Update Script for Windows
REM Run this script every 5 minutes using Task Scheduler

set TOKEN=ad563376-4f86-4423-8b71-c9b5c76af853
set DOMAIN=liime

REM Get current IP
for /f "tokens=*" %%a in ('curl -s ifconfig.me') do set IP=%%a

REM Update DuckDNS
curl -s "https://www.duckdns.org/update?domains=%DOMAIN%&token=%TOKEN%&ip=%IP%"

echo Updated DuckDNS: %DOMAIN%.duckdns.org -> %IP%
