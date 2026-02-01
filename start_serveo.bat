@echo off
REM Serveo.net - Free tunnel to localhost
REM No signup, no card, no router needed!

echo Starting Liime server tunnel...
echo.
echo Keep this window open!
echo Your URL will appear below...
echo.
ssh -R 80:localhost:8000 serveo.net

pause
