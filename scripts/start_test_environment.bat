@echo off
chcp 65001 >nul
echo ╔═══════════════════════════════════════════════════════════╗
echo ║  Запуск тестового окружения Smart Payload Splitter      ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Переход в директорию проекта (где находится docker-compose.yml)
cd /d "%~dp0\.."
if not exist "docker-compose.yml" (
    echo [-] Ошибка: файл docker-compose.yml не найден
    echo [*] Убедитесь, что вы запускаете скрипт из директории проекта
    echo [*] Текущая директория: %CD%
    pause
    exit /b 1
)

echo [*] Рабочая директория: %CD%
echo.

REM Проверка наличия Docker
echo [*] Проверка наличия Docker...
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [-] Docker не установлен или не найден в PATH
    echo [*] Установите Docker Desktop: https://www.docker.com/products/docker-desktop
    echo [*] Убедитесь, что Docker Desktop запущен
    pause
    exit /b 1
)
echo [+] Docker найден

REM Проверка Docker Compose
echo [*] Проверка наличия Docker Compose...
docker compose version >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set DOCKER_COMPOSE_CMD=docker compose
    echo [+] Docker Compose найден (docker compose)
) else (
    where docker-compose >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set DOCKER_COMPOSE_CMD=docker-compose
        echo [+] Docker Compose найден (docker-compose)
    ) else (
        echo [-] Docker Compose не установлен
        echo [*] Установите Docker Desktop, который включает Docker Compose
        pause
        exit /b 1
    )
)

REM Создание директорий
echo [*] Создание директорий для логов...
if not exist "suricata\logs" mkdir suricata\logs
if not exist "logs" mkdir logs

REM Проверка, что Docker запущен
echo [*] Проверка, что Docker запущен...
docker info >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [-] Docker не запущен или недоступен
    echo [*] Запустите Docker Desktop и попробуйте снова
    pause
    exit /b 1
)
echo [+] Docker запущен

REM Создание директорий
echo [*] Создание директорий для логов...
if not exist "suricata\logs" mkdir suricata\logs
if not exist "logs" mkdir logs

REM Запуск контейнеров
echo [*] Запуск контейнеров...
%DOCKER_COMPOSE_CMD% up -d
if %ERRORLEVEL% NEQ 0 (
    echo [-] Ошибка при запуске контейнеров
    echo [*] Проверьте логи: %DOCKER_COMPOSE_CMD% logs
    pause
    exit /b 1
)

REM Ожидание запуска
echo [*] Ожидание запуска сервисов (5 секунд)...
timeout /t 5 /nobreak >nul

REM Проверка статуса
echo [*] Проверка статуса контейнеров...
%DOCKER_COMPOSE_CMD% ps

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║  Тестовое окружение запущено!                            ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo Сервер доступен на: http://localhost:5000
echo.
echo Для просмотра логов Suricata:
echo   docker logs -f suricata_ids
echo.
echo Для просмотра логов сервера:
echo   docker logs -f smart_payload_server
echo.
echo Для остановки:
echo   %DOCKER_COMPOSE_CMD% down
echo.
echo Для просмотра логов всех контейнеров:
echo   %DOCKER_COMPOSE_CMD% logs -f
echo.
pause
