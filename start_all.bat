@echo off
echo Installing pm2 globally if not installed...
call npm install -g pm2

echo Starting all A11ySense AI services...
call pm2 start ecosystem.config.js

echo All services started successfully!
echo.
echo Useful commands:
echo  - pm2 status     (view running services)
echo  - pm2 logs       (view combined logs for all services)
echo  - pm2 stop all   (stop all services)
echo.
pause
