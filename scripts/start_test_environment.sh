#!/bin/bash
# Скрипт запуска тестового окружения

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Запуск тестового окружения Smart Payload Splitter      ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "[-] Docker не установлен"
    echo "[*] Установите Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "[-] Docker Compose не установлен"
    echo "[*] Установите Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Создание необходимых директорий
echo "[*] Создание директорий для логов..."
mkdir -p suricata/logs
mkdir -p logs

# Запуск контейнеров
echo "[*] Запуск контейнеров..."
docker-compose up -d

# Ожидание запуска сервисов
echo "[*] Ожидание запуска сервисов..."
sleep 5

# Проверка статуса
echo "[*] Проверка статуса контейнеров..."
docker-compose ps

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Тестовое окружение запущено!                            ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Сервер доступен на: http://localhost:5000"
echo ""
echo "Для просмотра логов Suricata:"
echo "  docker logs -f suricata_ids"
echo ""
echo "Для просмотра логов сервера:"
echo "  docker logs -f smart_payload_server"
echo ""
echo "Для остановки:"
echo "  docker-compose down"
echo ""
