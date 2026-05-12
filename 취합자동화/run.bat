@echo off
chcp 65001 > nul
echo ================================================
echo   취합 자동화 시스템 시작
echo ================================================

cd /d "%~dp0"

REM Python 가상환경 확인
if not exist "venv\Scripts\python.exe" (
    echo [1/2] 가상환경 생성 중...
    python -m venv venv
    echo [2/2] 패키지 설치 중...
    venv\Scripts\pip install -r requirements.txt
    echo.
    echo 설치 완료!
)

echo.
echo 서버 시작 중... (http://localhost:8000)
echo 종료하려면 Ctrl+C 를 누르세요.
echo.

venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
