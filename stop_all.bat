@echo off
echo Stopping all A11ySense AI services...
call pm2 stop ecosystem.config.js
call pm2 delete ecosystem.config.js
echo.
echo All services stopped!
pause
