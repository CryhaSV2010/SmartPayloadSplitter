#!/bin/bash
# Скрипт установки Suricata для тестирования Smart Payload Splitter

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Установка Suricata для тестирования Smart Payload       ║"
echo "║  Splitter                                                ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo "[-] Ошибка: скрипт должен быть запущен от имени root"
    echo "    Используйте: sudo ./install.sh"
    exit 1
fi

# Определение дистрибутива
if [ -f /etc/debian_version ]; then
    DISTRO="debian"
elif [ -f /etc/redhat-release ]; then
    DISTRO="redhat"
else
    echo "[-] Неподдерживаемый дистрибутив Linux"
    exit 1
fi

echo "[*] Обнаружен дистрибутив: $DISTRO"
echo "[*] Начинаем установку Suricata..."

# Установка для Debian/Ubuntu
if [ "$DISTRO" = "debian" ]; then
    # Обновление пакетов
    apt-get update
    
    # Установка зависимостей
    apt-get install -y \
        software-properties-common \
        wget \
        curl \
        libpcre3 \
        libpcre3-dbg \
        libpcre3-dev \
        build-essential \
        libpcap-dev \
        libnet1-dev \
        libyaml-0-2 \
        libyaml-dev \
        zlib1g \
        zlib1g-dev \
        libcap-ng-dev \
        libcap-ng0 \
        make \
        libmagic-dev \
        libjansson-dev \
        libjansson4 \
        rustc \
        cargo \
        python3-pip
    
    # Добавление репозитория OISF
    add-apt-repository -y ppa:oisf/suricata-stable
    apt-get update
    
    # Установка Suricata
    apt-get install -y suricata
    
# Установка для RedHat/CentOS
elif [ "$DISTRO" = "redhat" ]; then
    # Установка EPEL репозитория
    yum install -y epel-release
    
    # Установка зависимостей
    yum install -y \
        gcc \
        gcc-c++ \
        make \
        libpcap-devel \
        libnet-devel \
        libyaml-devel \
        zlib-devel \
        pcre-devel \
        libcap-ng-devel \
        libmagic-devel \
        jansson-devel \
        rust \
        cargo \
        python3-pip
    
    # Установка Suricata из репозитория
    yum install -y suricata || {
        echo "[*] Suricata не найден в стандартных репозиториях"
        echo "[*] Установка из исходников..."
        # Здесь можно добавить установку из исходников
    }
fi

echo "[+] Suricata установлен"
echo "[*] Проверка версии..."
suricata -V

# Создание директорий для конфигурации
echo "[*] Создание директорий..."
mkdir -p /etc/suricata/rules
mkdir -p /var/log/suricata
mkdir -p /var/lib/suricata/rules

# Копирование правил
echo "[*] Копирование правил..."
if [ -f "./suricata/rules/custom-test.rules" ]; then
    cp ./suricata/rules/custom-test.rules /etc/suricata/rules/
    echo "[+] Правила скопированы"
else
    echo "[-] Предупреждение: файл правил не найден"
fi

# Копирование конфигурации
if [ -f "./suricata/config/suricata.yaml" ]; then
    cp ./suricata/config/suricata.yaml /etc/suricata/suricata.yaml
    echo "[+] Конфигурация скопирована"
else
    echo "[-] Предупреждение: файл конфигурации не найден"
fi

# Обновление правил
echo "[*] Обновление правил Suricata..."
suricata-update

# Проверка конфигурации
echo "[*] Проверка конфигурации..."
suricata -T -c /etc/suricata/suricata.yaml

if [ $? -eq 0 ]; then
    echo "[+] Конфигурация корректна"
else
    echo "[-] Ошибка в конфигурации"
    exit 1
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Установка завершена успешно!                             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Для запуска Suricata используйте:"
echo "  sudo suricata -c /etc/suricata/suricata.yaml -i <интерфейс>"
echo ""
echo "Для просмотра логов:"
echo "  tail -f /var/log/suricata/fast.log"
echo "  tail -f /var/log/suricata/eve.json"
echo ""
