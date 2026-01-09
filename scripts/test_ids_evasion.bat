@echo off
REM Скрипт для автоматического тестирования обхода IDS (Windows)

echo ╔═══════════════════════════════════════════════════════════╗
echo ║  Тестирование обхода IDS/IPS                              ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

set SERVER_URL=%1
if "%SERVER_URL%"=="" set SERVER_URL=http://localhost:5000

set PAYLOAD_FILE=%2
if "%PAYLOAD_FILE%"=="" set PAYLOAD_FILE=test_payload.txt

if not exist "%PAYLOAD_FILE%" (
    echo [-] Файл пейлоада не найден: %PAYLOAD_FILE%
    pause
    exit /b 1
)

echo [*] URL сервера: %SERVER_URL%
echo [*] Файл пейлоада: %PAYLOAD_FILE%
echo.

REM Проверка наличия Docker
docker ps | findstr suricata_ids >nul
if %ERRORLEVEL% EQU 0 (
    echo [*] Используется Docker-окружение
    echo [*] Очистка старых логов Suricata...
    docker exec suricata_ids sh -c "echo '' > /var/log/suricata/fast.log"
) else (
    echo [*] Docker не обнаружен, предполагается локальная установка
)

echo.
echo ═══════════════════════════════════════════════════════════
echo ТЕСТ 1: Отправка пейлоада целиком (ожидается обнаружение)
echo ═══════════════════════════════════════════════════════════
echo.

REM Кодирование в base64 (PowerShell)
for /f "delims=" %%i in ('powershell -Command "[Convert]::ToBase64String([System.IO.File]::ReadAllBytes('%PAYLOAD_FILE%'))"') do set PAYLOAD_CONTENT=%%i

curl -X POST "%SERVER_URL%/api/fragment" ^
    -H "Content-Type: application/json" ^
    -d "{\"session_id\":\"test_full_%RANDOM%\",\"fragment_index\":0,\"total_fragments\":1,\"data\":\"%PAYLOAD_CONTENT%\"}" ^
    -s -o nul

timeout /t 2 /nobreak >nul

echo [*] Проверка логов Suricata...
docker exec suricata_ids sh -c "grep -c 'Test Payload' /var/log/suricata/fast.log 2>nul || echo 0" > temp_alerts.txt
set /p ALERTS=<temp_alerts.txt
del temp_alerts.txt

if %ALERTS% GTR 0 (
    echo [+] Пейлоад обнаружен IDS (ожидаемо): %ALERTS% предупреждений
) else (
    echo [-] Пейлоад НЕ обнаружен IDS (неожиданно)
)

echo.
echo ═══════════════════════════════════════════════════════════
echo ТЕСТ 2: Фрагментированная отправка (ожидается обход)
echo ═══════════════════════════════════════════════════════════
echo.

REM Очистка логов перед вторым тестом
docker exec suricata_ids sh -c "echo '' > /var/log/suricata/fast.log" 2>nul

python client/payload_fragmenter.py "%PAYLOAD_FILE%" ^
    -u "%SERVER_URL%" ^
    --min-size 5 ^
    --max-size 20 ^
    -d 0.1 ^
    --assemble ^
    -r "test_report_fragmented.txt"

timeout /t 2 /nobreak >nul

echo [*] Проверка логов Suricata...
docker exec suricata_ids sh -c "grep -c 'Test Payload' /var/log/suricata/fast.log 2>nul || echo 0" > temp_alerts.txt
set /p ALERTS=<temp_alerts.txt
del temp_alerts.txt

if %ALERTS% EQU 0 (
    echo [+] УСПЕХ: Фрагментированный пейлоад НЕ обнаружен IDS
    echo [+] Обход IDS работает!
) else (
    echo [-] Пейлоад всё ещё обнаружен: %ALERTS% предупреждений
    echo [-] Возможно, IDS использует поведенческий анализ
)

echo.
echo ═══════════════════════════════════════════════════════════
echo Тестирование завершено
echo ═══════════════════════════════════════════════════════════
echo.
echo Для просмотра полных логов Suricata:
echo   docker logs -f suricata_ids
echo.
pause
