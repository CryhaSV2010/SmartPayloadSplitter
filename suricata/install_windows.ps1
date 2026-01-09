# Скрипт установки Suricata для Windows
# Внимание: Suricata на Windows требует WSL или виртуальной машины

Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Установка Suricata для тестирования Smart Payload       ║" -ForegroundColor Cyan
Write-Host "║  Splitter (Windows)                                        ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Проверка прав администратора
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[-] Ошибка: скрипт должен быть запущен от имени администратора" -ForegroundColor Red
    Write-Host "    Щелкните правой кнопкой мыши и выберите 'Запуск от имени администратора'" -ForegroundColor Yellow
    exit 1
}

Write-Host "[*] Suricata на Windows требует WSL или виртуальной машины" -ForegroundColor Yellow
Write-Host "[*] Рекомендуется использовать Docker или WSL2" -ForegroundColor Yellow
Write-Host ""

# Проверка наличия WSL
$wslInstalled = Get-Command wsl -ErrorAction SilentlyContinue

if ($wslInstalled) {
    Write-Host "[+] WSL обнаружен" -ForegroundColor Green
    Write-Host "[*] Для установки Suricata в WSL выполните:" -ForegroundColor Yellow
    Write-Host "    wsl sudo ./suricata/install.sh" -ForegroundColor Cyan
} else {
    Write-Host "[-] WSL не установлен" -ForegroundColor Red
    Write-Host "[*] Рекомендуется использовать Docker:" -ForegroundColor Yellow
    Write-Host "    docker-compose up -d" -ForegroundColor Cyan
}

# Проверка наличия Docker
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue

if ($dockerInstalled) {
    Write-Host "[+] Docker обнаружен" -ForegroundColor Green
    Write-Host "[*] Для запуска с Docker выполните:" -ForegroundColor Yellow
    Write-Host "    docker-compose up -d" -ForegroundColor Cyan
} else {
    Write-Host "[-] Docker не установлен" -ForegroundColor Red
    Write-Host "[*] Установите Docker Desktop с https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[*] Альтернативный вариант: используйте виртуальную машину с Linux" -ForegroundColor Yellow
Write-Host ""
