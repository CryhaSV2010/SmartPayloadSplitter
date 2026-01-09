#!/bin/bash
# Скрипт для автоматического тестирования обхода IDS

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Тестирование обхода IDS/IPS                              ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

SERVER_URL="${1:-http://localhost:5000}"
PAYLOAD_FILE="${2:-test_payload.txt}"

if [ ! -f "$PAYLOAD_FILE" ]; then
    echo "[-] Файл пейлоада не найден: $PAYLOAD_FILE"
    exit 1
fi

echo "[*] URL сервера: $SERVER_URL"
echo "[*] Файл пейлоада: $PAYLOAD_FILE"
echo ""

# Очистка старых логов Suricata
echo "[*] Очистка старых логов Suricata..."
if docker ps | grep -q suricata_ids; then
    docker exec suricata_ids sh -c "echo '' > /var/log/suricata/fast.log"
elif [ -f /var/log/suricata/fast.log ]; then
    sudo sh -c "echo '' > /var/log/suricata/fast.log"
fi

# Тест 1: Отправка пейлоада целиком (должен быть обнаружен)
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "ТЕСТ 1: Отправка пейлоада целиком (ожидается обнаружение)"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Кроссплатформенное base64 кодирование
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    PAYLOAD_CONTENT=$(cat "$PAYLOAD_FILE" | base64)
else
    # Linux
    PAYLOAD_CONTENT=$(cat "$PAYLOAD_FILE" | base64 -w 0)
fi
curl -X POST "$SERVER_URL/api/fragment" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"test_full_$(date +%s)\",\"fragment_index\":0,\"total_fragments\":1,\"data\":\"$PAYLOAD_CONTENT\"}" \
    -s -o /dev/null

sleep 2

echo "[*] Проверка логов Suricata..."
if docker ps | grep -q suricata_ids; then
    ALERTS=$(docker exec suricata_ids sh -c "grep -c 'Test Payload' /var/log/suricata/fast.log 2>/dev/null || echo 0")
else
    ALERTS=$(sudo grep -c "Test Payload" /var/log/suricata/fast.log 2>/dev/null || echo 0)
fi

if [ "$ALERTS" -gt 0 ]; then
    echo "[+] Пейлоад обнаружен IDS (ожидаемо): $ALERTS предупреждений"
else
    echo "[-] Пейлоад НЕ обнаружен IDS (неожиданно)"
fi

# Тест 2: Фрагментированная отправка (не должен быть обнаружен)
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "ТЕСТ 2: Фрагментированная отправка (ожидается обход)"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Очистка логов перед вторым тестом
if docker ps | grep -q suricata_ids; then
    docker exec suricata_ids sh -c "echo '' > /var/log/suricata/fast.log"
elif [ -f /var/log/suricata/fast.log ]; then
    sudo sh -c "echo '' > /var/log/suricata/fast.log"
fi

python3 client/payload_fragmenter.py "$PAYLOAD_FILE" \
    -u "$SERVER_URL" \
    --min-size 5 \
    --max-size 20 \
    -d 0.1 \
    --assemble \
    -r "test_report_fragmented.txt"

sleep 2

echo "[*] Проверка логов Suricata..."
if docker ps | grep -q suricata_ids; then
    ALERTS=$(docker exec suricata_ids sh -c "grep -c 'Test Payload' /var/log/suricata/fast.log 2>/dev/null || echo 0")
else
    ALERTS=$(sudo grep -c "Test Payload" /var/log/suricata/fast.log 2>/dev/null || echo 0)
fi

if [ "$ALERTS" -eq 0 ]; then
    echo "[+] УСПЕХ: Фрагментированный пейлоад НЕ обнаружен IDS"
    echo "[+] Обход IDS работает!"
else
    echo "[-] Пейлоад всё ещё обнаружен: $ALERTS предупреждений"
    echo "[-] Возможно, IDS использует поведенческий анализ"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Тестирование завершено"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Для просмотра полных логов Suricata:"
echo "  ./scripts/view_suricata_logs.sh"
echo ""
