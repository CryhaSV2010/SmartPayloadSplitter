#!/bin/bash
# Скрипт для просмотра логов Suricata

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Просмотр логов Suricata                                  ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Проверка режима работы (Docker или локальная установка)
if docker ps | grep -q suricata_ids; then
    echo "[*] Используется Docker-контейнер"
    echo "[*] Просмотр логов в реальном времени..."
    echo ""
    echo "Нажмите Ctrl+C для выхода"
    echo ""
    docker logs -f suricata_ids
elif [ -f /var/log/suricata/fast.log ]; then
    echo "[*] Используется локальная установка"
    echo "[*] Просмотр логов в реальном времени..."
    echo ""
    echo "Нажмите Ctrl+C для выхода"
    echo ""
    tail -f /var/log/suricata/fast.log
else
    echo "[-] Suricata не запущен или логи не найдены"
    echo "[*] Убедитесь, что Suricata запущен"
    exit 1
fi
