@echo off
chcp 65001 > nul
echo 포트 8000 서버 종료 중...

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 " ^| findstr "LISTENING" 2^>nul') do (
    echo PID %%a 종료 중...
    taskkill /F /PID %%a > nul 2>&1
)

echo 완료.
timeout /t 2 > nul
