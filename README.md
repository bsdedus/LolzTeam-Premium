# 🚀 Руководство по развертыванию бота

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)

> **Полное руководство по установке и настройке LZT Market Bot на Windows и Ubuntu/Linux**

## 📋 Содержание

- [🪟 Установка на Windows](#-установка-на-windows)
  - [Шаг 1: Установка Python](#шаг-1-установка-python)
  - [Шаг 2: Клонирование репозитория](#шаг-2-клонирование-репозитория)
  - [Шаг 3: Установка зависимостей](#шаг-3-установка-зависимостей)
  - [Шаг 4: Настройка конфигурации](#шаг-4-настройка-конфигурации)
  - [Шаг 5: Создание bat-файла](#шаг-5-создание-bat-файла-для-запуска)
  - [Шаг 6: Запуск бота](#шаг-6-запуск-бота)
  - [Шаг 7: Автозапуск](#шаг-7-автозапуск-при-старте-windows)
- [🐧 Установка на Ubuntu/Linux](#-установка-на-ubuntulinux)
  - [Шаг 1: Обновление системы](#шаг-1-обновление-системы)
  - [Шаг 2: Установка зависимостей](#шаг-2-установка-python-и-зависимостей)
  - [Шаг 3: Клонирование репозитория](#шаг-3-клонирование-репозитория)
  - [Шаг 4: Виртуальное окружение](#шаг-4-создание-виртуального-окружения)
  - [Шаг 5: Настройка конфигурации](#шаг-5-настройка-конфигурации)
  - [Шаг 6: Создание скрипта](#шаг-6-создание-скрипта-запуска)
  - [Шаг 7: Запуск в screen](#шаг-7-запуск-в-screen)
  - [Шаг 8: Автозапуск](#шаг-8-автозапуск-при-перезагрузке)
- [📊 Просмотр логов через бота](#-просмотр-логов-через-бота)
- [🔧 Полезные команды](#-полезные-команды)
- [🆘 Решение проблем](#-решение-проблем)

---

# 🪟 Установка на Windows

## Шаг 1: Установка Python

1. Скачайте Python 3.8+ с [python.org](https://www.python.org/downloads/)
2. При установке **обязательно** отметьте ✅ **"Add Python to PATH"**
3. Проверьте установку:

```cmd
python --version
pip --version
```

**Ожидаемый результат:**
```
Python 3.11.0
pip 23.0.1
```

## Шаг 2: Клонирование репозитория

### Вариант 1: Через Git (рекомендуется)

1. Установите [Git для Windows](https://git-scm.com/download/win)
2. Откройте командную строку и выполните:

```cmd
cd C:\
mkdir bots
cd bots
git clone https://github.com/YOUR_USERNAME/lzt-market-bot.git
cd lzt-market-bot
```

### Вариант 2: Скачать ZIP

1. Нажмите кнопку **Code** → **Download ZIP** на GitHub
2. Распакуйте архив в `C:\bots\lzt-market-bot\`
3. Откройте командную строку:

```cmd
cd C:\bots\lzt-market-bot
```

> 💡 **Совет:** Shift + Правая кнопка мыши в папке → "Открыть окно PowerShell здесь"

## Шаг 3: Установка зависимостей

```cmd
pip install -r requirements.txt
```

Если `requirements.txt` нет, установите вручную:
```cmd
pip install python-telegram-bot aiohttp requests
```

## Шаг 4: Настройка конфигурации

Отредактируйте `config.json`:
```json
{
    "telegram_token": "ВАШ_ТОКЕН_БОТА",
    "lzt_token": "ВАШ_LZT_ТОКЕН",
    "user_id": "ВАШ_USER_ID"
}
```

## Шаг 5: Создание bat-файла для запуска

Создайте файл `start_bot.bat` в папке с ботом:

```batch
@echo off
chcp 65001 >nul
title LZT Market Bot
color 0A

echo ========================================
echo    LZT Market Bot - Starting...
echo ========================================
echo.

:start
echo [%date% %time%] Starting bot...
python lzt_market_bot_multilang.py 2>&1 | tee -a bot.log

echo.
echo [%date% %time%] Bot stopped. Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto start
```

**Если команда `tee` не работает**, используйте эту версию:

```batch
@echo off
chcp 65001 >nul
title LZT Market Bot
color 0A

echo ========================================
echo    LZT Market Bot - Starting...
echo ========================================
echo.

:start
echo [%date% %time%] Starting bot... >> bot.log
python lzt_market_bot_multilang.py >> bot.log 2>&1

echo.
echo [%date% %time%] Bot stopped. Restarting in 5 seconds... >> bot.log
timeout /t 5 /nobreak >nul
goto start
```

## Шаг 6: Запуск бота

Просто дважды кликните на `start_bot.bat`

Откроется окно с логами:
```
========================================
   LZT Market Bot - Starting...
========================================

[13.01.2025 18:30:15] Starting bot...
INFO - Bot started successfully
INFO - Listening for updates...
```

## Шаг 7: Автозапуск при старте Windows

### Вариант 1: Через планировщик задач

1. Откройте "Планировщик заданий" (Task Scheduler)
2. Создать задачу → Общие:
   - Имя: "LZT Market Bot"
   - ✅ Выполнять с наивысшими правами
3. Триггеры → Создать:
   - Начать задачу: При входе в систему
4. Действия → Создать:
   - Программа: `C:\bots\lzt_market_bot\start_bot.bat`
   - Рабочая папка: `C:\bots\lzt_market_bot`
5. Условия:
   - ❌ Запускать только при питании от сети
6. Параметры:
   - ✅ Если задача не выполнена, перезапускать через: 1 минута
   - ✅ Останавливать задачу, выполняющуюся более: Не останавливать

### Вариант 2: Через автозагрузку

1. Нажмите `Win + R`
2. Введите: `shell:startup`
3. Скопируйте туда ярлык на `start_bot.bat`

## Шаг 8: Просмотр логов

Логи сохраняются в файл `bot.log` в папке с ботом.

Для просмотра в реальном времени:
```cmd
powershell Get-Content bot.log -Wait -Tail 50
```

Или откройте `bot.log` в любом текстовом редакторе.

---

# 🐧 Установка на Ubuntu/Linux

## Шаг 1: Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

## Шаг 2: Установка Python и зависимостей

```bash
# Установка Python 3, pip и git
sudo apt install python3 python3-pip python3-venv git -y

# Установка screen для фоновой работы
sudo apt install screen -y

# Проверка версий
python3 --version
pip3 --version
git --version
screen --version
```

**Ожидаемый результат:**
```
Python 3.10.12
pip 22.0.2
git version 2.34.1
Screen version 4.09.00
```

## Шаг 3: Клонирование репозитория

### Вариант 1: Через Git (рекомендуется)

```bash
# Создаем директорию для ботов
mkdir -p ~/bots
cd ~/bots

# Клонируем репозиторий
git clone https://github.com/YOUR_USERNAME/lzt-market-bot.git
cd lzt-market-bot
```

### Вариант 2: Скачать и загрузить вручную

```bash
# Создаем директорию
mkdir -p ~/bots/lzt-market-bot
cd ~/bots/lzt-market-bot

# Загружаем файлы через SFTP/SCP
# Например: scp -r /local/path/* user@server:~/bots/lzt-market-bot/
```

> 💡 **Совет:** Для обновления бота используйте `git pull` в директории проекта

## Шаг 4: Создание виртуального окружения

```bash
# Создаем виртуальное окружение
python3 -m venv venv

# Активируем его
source venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

Если `requirements.txt` нет, установите вручную:
```bash
pip install python-telegram-bot aiohttp requests
```

## Шаг 5: Настройка конфигурации

```bash
# Редактируем config.json
nano config.json
```

Вставьте:
```json
{
    "telegram_token": "ВАШ_ТОКЕН_БОТА",
    "lzt_token": "ВАШ_LZT_ТОКЕН",
    "user_id": "ВАШ_USER_ID"
}
```

Сохраните: `Ctrl + X`, затем `Y`, затем `Enter`

## Шаг 6: Создание скрипта запуска

```bash
nano start_bot.sh
```

Вставьте:
```bash
#!/bin/bash

# Переходим в директорию бота
cd ~/bots/lzt-market-bot

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем бота с логированием
while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting bot..." | tee -a bot.log
    python3 lzt_market_bot_multilang.py 2>&1 | tee -a bot.log
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot stopped. Restarting in 5 seconds..." | tee -a bot.log
    sleep 5
done
```

Сделайте скрипт исполняемым:
```bash
chmod +x start_bot.sh
```

## Шаг 7: Запуск в screen

### Создание новой screen-сессии:

```bash
screen -S lzt_bot
```

### Запуск бота:

```bash
./start_bot.sh
```

### Отключение от screen (бот продолжит работать):

Нажмите: `Ctrl + A`, затем `D`

### Подключение к существующей сессии:

```bash
screen -r lzt_bot
```

### Просмотр всех screen-сессий:

```bash
screen -ls
```

### Остановка бота:

```bash
# Подключитесь к сессии
screen -r lzt_bot

# Остановите бот: Ctrl + C
# Выйдите из screen: exit
```

## Шаг 8: Автозапуск при перезагрузке

### Вариант 1: Через systemd (рекомендуется)

Создайте systemd service:
```bash
sudo nano /etc/systemd/system/lzt-bot.service
```

Вставьте:
```ini
[Unit]
Description=LZT Market Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/bots/lzt_market_bot
ExecStart=/home/YOUR_USERNAME/bots/lzt_market_bot/venv/bin/python3 /home/YOUR_USERNAME/bots/lzt_market_bot/lzt_market_bot_multilang.py
Restart=always
RestartSec=5
StandardOutput=append:/home/YOUR_USERNAME/bots/lzt_market_bot/bot.log
StandardError=append:/home/YOUR_USERNAME/bots/lzt_market_bot/bot.log

[Install]
WantedBy=multi-user.target
```

**Замените `YOUR_USERNAME` на ваше имя пользователя!**

Активируйте сервис:
```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable lzt-bot

# Запустите сервис
sudo systemctl start lzt-bot

# Проверьте статус
sudo systemctl status lzt-bot

# Просмотр логов
sudo journalctl -u lzt-bot -f
```

Управление сервисом:
```bash
sudo systemctl start lzt-bot    # Запуск
sudo systemctl stop lzt-bot     # Остановка
sudo systemctl restart lzt-bot  # Перезапуск
sudo systemctl status lzt-bot   # Статус
```

### Вариант 2: Через crontab + screen

```bash
crontab -e
```

Добавьте строку:
```bash
@reboot screen -dmS lzt_bot /home/YOUR_USERNAME/bots/lzt_market_bot/start_bot.sh
```

**Замените `YOUR_USERNAME` на ваше имя пользователя!**

Сохраните и выйдите.

Проверьте:
```bash
crontab -l
```

## Шаг 9: Просмотр логов

### В реальном времени:
```bash
tail -f ~/bots/lzt_market_bot/bot.log
```

### Последние 100 строк:
```bash
tail -n 100 ~/bots/lzt_market_bot/bot.log
```

### Поиск ошибок:
```bash
grep -i "error" ~/bots/lzt_market_bot/bot.log
```

### Очистка старых логов:
```bash
# Создать резервную копию
cp bot.log bot.log.backup

# Очистить файл
> bot.log
```

---

# 📊 Просмотр логов через бота

## Добавление команды /logs в бота

Добавьте этот код в ваш бот (например, в `lzt_market_bot_multilang.py`):

```python
import os
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def send_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка файла логов администратору"""
    user_id = update.effective_user.id
    
    # Проверка прав (замените на ваш user_id)
    ADMIN_ID = 6388847  # Ваш Telegram ID
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для просмотра логов")
        return
    
    log_file = "bot.log"
    
    if not os.path.exists(log_file):
        await update.message.reply_text("❌ Файл логов не найден")
        return
    
    try:
        # Получаем размер файла
        file_size = os.path.getsize(log_file)
        
        if file_size > 50 * 1024 * 1024:  # Если больше 50 МБ
            await update.message.reply_text(
                f"⚠️ Файл логов слишком большой ({file_size / 1024 / 1024:.2f} МБ)\n"
                "Отправляю последние 1000 строк..."
            )
            
            # Читаем последние 1000 строк
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_lines = lines[-1000:]
            
            # Создаем временный файл
            temp_file = "bot_last_1000.log"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.writelines(last_lines)
            
            await update.message.reply_document(
                document=open(temp_file, 'rb'),
                filename="bot_last_1000.log",
                caption=f"📋 Последние 1000 строк логов\n📊 Размер полного файла: {file_size / 1024 / 1024:.2f} МБ"
            )
            
            os.remove(temp_file)
        else:
            # Отправляем весь файл
            await update.message.reply_document(
                document=open(log_file, 'rb'),
                filename="bot.log",
                caption=f"📋 Полный файл логов\n📊 Размер: {file_size / 1024:.2f} КБ"
            )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при отправке логов: {e}")

# Добавьте обработчик в main():
application.add_handler(CommandHandler("logs", send_logs))
```

## Использование команды /logs

Просто отправьте боту:
```
/logs
```

Бот отправит вам файл `bot.log` с логами.

---

# 🔧 Полезные команды

## Windows

### Просмотр процессов Python:
```cmd
tasklist | findstr python
```

### Остановка бота:
```cmd
taskkill /F /IM python.exe
```

### Очистка логов:
```cmd
echo. > bot.log
```

## Linux

### Просмотр процессов:
```bash
ps aux | grep python
```

### Остановка бота:
```bash
pkill -f lzt_market_bot
```

### Мониторинг ресурсов:
```bash
htop
```

### Размер лог-файла:
```bash
du -h bot.log
```

### Ротация логов (автоматическая очистка):
```bash
# Создайте файл /etc/logrotate.d/lzt-bot
sudo nano /etc/logrotate.d/lzt-bot
```

Вставьте:
```
/home/YOUR_USERNAME/bots/lzt_market_bot/bot.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 YOUR_USERNAME YOUR_USERNAME
}
```

---

# 📝 Структура логов

Логи сохраняются в формате:
```
[2025-01-13 18:30:15] INFO - Bot started successfully
[2025-01-13 18:30:16] INFO - Listening for updates...
[2025-01-13 18:30:45] INFO - User 123456789 uploaded 5 accounts
[2025-01-13 18:31:02] ERROR - Failed to upload account: Invalid token
```

---

# 🆘 Решение проблем

## Windows

### Бот не запускается:
1. Проверьте, установлен ли Python: `python --version`
2. Проверьте зависимости: `pip list`
3. Проверьте config.json на ошибки
4. Запустите вручную: `python lzt_market_bot_multilang.py`

### Логи не сохраняются:
1. Проверьте права на запись в папку
2. Запустите cmd от имени администратора

## Linux

### Бот не запускается:
```bash
# Проверьте логи systemd
sudo journalctl -u lzt-bot -n 50

# Проверьте права на файлы
ls -la ~/bots/lzt_market_bot/

# Проверьте виртуальное окружение
source venv/bin/activate
python3 lzt_market_bot_multilang.py
```

### Screen не работает:
```bash
# Переустановите screen
sudo apt remove screen
sudo apt install screen

# Проверьте сессии
screen -ls
```

---

# ✅ Чеклист успешной установки

## Windows:
- [ ] Python установлен и добавлен в PATH
- [ ] Зависимости установлены
- [ ] config.json настроен
- [ ] start_bot.bat создан и работает
- [ ] Логи сохраняются в bot.log
- [ ] Автозапуск настроен (опционально)
- [ ] Команда /logs работает

## Linux:
- [ ] Python 3.8+ установлен
- [ ] Screen установлен
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] config.json настроен
- [ ] start_bot.sh создан и исполняемый
- [ ] Бот запускается в screen
- [ ] Systemd service настроен (опционально)
- [ ] Логи сохраняются в bot.log
- [ ] Команда /logs работает

---

**Версия:** 1.0.0  
**Дата:** 2025-01-13

# 🚀 Bot Deployment Guide

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)

> **Complete guide for installing and configuring LZT Market Bot on Windows and Ubuntu/Linux**

## 📋 Table of Contents

- [🪟 Windows Installation](#-windows-installation)
  - [Step 1: Install Python](#step-1-install-python)
  - [Step 2: Clone Repository](#step-2-clone-repository)
  - [Step 3: Install Dependencies](#step-3-install-dependencies)
  - [Step 4: Configure Settings](#step-4-configure-settings)
  - [Step 5: Create Batch File](#step-5-create-batch-file-for-launch)
  - [Step 6: Start Bot](#step-6-start-the-bot)
  - [Step 7: Auto-start](#step-7-auto-start-on-windows-boot)
- [🐧 Ubuntu/Linux Installation](#-ubuntulinux-installation)
  - [Step 1: Update System](#step-1-update-system)
  - [Step 2: Install Dependencies](#step-2-install-python-and-dependencies)
  - [Step 3: Clone Repository](#step-3-clone-repository)
  - [Step 4: Virtual Environment](#step-4-create-virtual-environment)
  - [Step 5: Configure Settings](#step-5-configure-settings)
  - [Step 6: Create Script](#step-6-create-launch-script)
  - [Step 7: Run in Screen](#step-7-run-in-screen)
  - [Step 8: Auto-start](#step-8-auto-start-on-reboot)
- [📊 Viewing Logs via Bot](#-viewing-logs-via-bot)
- [🔧 Useful Commands](#-useful-commands)
- [🆘 Troubleshooting](#-troubleshooting)

---

# 🪟 Windows Installation

## Step 1: Install Python

1. Download Python 3.8+ from [python.org](https://www.python.org/downloads/)
2. During installation, **make sure** to check ✅ **"Add Python to PATH"**
3. Verify installation:

```cmd
python --version
pip --version
```

**Expected output:**
```
Python 3.11.0
pip 23.0.1
```

## Step 2: Clone Repository

### Option 1: Via Git (recommended)

1. Install [Git for Windows](https://git-scm.com/download/win)
2. Open command prompt and execute:

```cmd
cd C:\
mkdir bots
cd bots
git clone https://github.com/YOUR_USERNAME/lzt-market-bot.git
cd lzt-market-bot
```

### Option 2: Download ZIP

1. Click **Code** → **Download ZIP** button on GitHub
2. Extract archive to `C:\bots\lzt-market-bot\`
3. Open command prompt:

```cmd
cd C:\bots\lzt-market-bot
```

> 💡 **Tip:** Shift + Right-click in folder → "Open PowerShell window here"

## Step 3: Install Dependencies

```cmd
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist, install manually:
```cmd
pip install python-telegram-bot aiohttp requests
```

## Step 4: Configure Settings

Edit `config.json`:
```json
{
    "telegram_token": "YOUR_BOT_TOKEN",
    "lzt_token": "YOUR_LZT_TOKEN",
    "user_id": "YOUR_USER_ID"
}
```

## Step 5: Create Batch File for Launch

Create `start_bot.bat` file in the bot folder:

```batch
@echo off
chcp 65001 >nul
title LZT Market Bot
color 0A

echo ========================================
echo    LZT Market Bot - Starting...
echo ========================================
echo.

:start
echo [%date% %time%] Starting bot...
python lzt_market_bot_multilang.py 2>&1 | tee -a bot.log

echo.
echo [%date% %time%] Bot stopped. Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto start
```

**If `tee` command doesn't work**, use this version:

```batch
@echo off
chcp 65001 >nul
title LZT Market Bot
color 0A

echo ========================================
echo    LZT Market Bot - Starting...
echo ========================================
echo.

:start
echo [%date% %time%] Starting bot... >> bot.log
python lzt_market_bot_multilang.py >> bot.log 2>&1

echo.
echo [%date% %time%] Bot stopped. Restarting in 5 seconds... >> bot.log
timeout /t 5 /nobreak >nul
goto start
```

## Step 6: Start the Bot

Simply double-click `start_bot.bat`

A window with logs will open:
```
========================================
   LZT Market Bot - Starting...
========================================

[01/13/2025 18:30:15] Starting bot...
INFO - Bot started successfully
INFO - Listening for updates...
```

## Step 7: Auto-start on Windows Boot

### Option 1: Via Task Scheduler

1. Open "Task Scheduler"
2. Create Task → General:
   - Name: "LZT Market Bot"
   - ✅ Run with highest privileges
3. Triggers → New:
   - Begin the task: At log on
4. Actions → New:
   - Program: `C:\bots\lzt_market_bot\start_bot.bat`
   - Start in: `C:\bots\lzt_market_bot`
5. Conditions:
   - ❌ Start only if on AC power
6. Settings:
   - ✅ If task fails, restart every: 1 minute
   - ✅ Stop task if runs longer than: Do not stop

### Option 2: Via Startup Folder

1. Press `Win + R`
2. Type: `shell:startup`
3. Copy shortcut to `start_bot.bat` there

## Step 8: View Logs

Logs are saved to `bot.log` file in the bot folder.

To view in real-time:
```cmd
powershell Get-Content bot.log -Wait -Tail 50
```

Or open `bot.log` in any text editor.

---

# 🐧 Ubuntu/Linux Installation

## Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

## Step 2: Install Python and Dependencies

```bash
# Install Python 3 and pip
sudo apt install python3 python3-pip python3-venv -y

# Install screen for background operation
sudo apt install screen -y

# Check versions
python3 --version
pip3 --version
screen --version
```

## Step 3: Prepare Project

```bash
# Create directory for bot
mkdir -p ~/bots/lzt_market_bot
cd ~/bots/lzt_market_bot

# Download project files (if via git)
# git clone https://your-repo-url.git .

# Or upload manually via SFTP/SCP
```

## Step 4: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or manually:
pip install python-telegram-bot aiohttp requests
```

## Step 5: Configure Settings

```bash
# Edit config.json
nano config.json
```

Insert:
```json
{
    "telegram_token": "YOUR_BOT_TOKEN",
    "lzt_token": "YOUR_LZT_TOKEN",
    "user_id": "YOUR_USER_ID"
}
```

Save: `Ctrl + X`, then `Y`, then `Enter`

## Step 6: Create Launch Script

```bash
nano start_bot.sh
```

Insert:
```bash
#!/bin/bash

# Navigate to bot directory
cd ~/bots/lzt_market_bot

# Activate virtual environment
source venv/bin/activate

# Start bot with logging
while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting bot..." | tee -a bot.log
    python3 lzt_market_bot_multilang.py 2>&1 | tee -a bot.log
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot stopped. Restarting in 5 seconds..." | tee -a bot.log
    sleep 5
done
```

Make script executable:
```bash
chmod +x start_bot.sh
```

## Step 7: Run in Screen

### Create new screen session:

```bash
screen -S lzt_bot
```

### Start bot:

```bash
./start_bot.sh
```

### Detach from screen (bot continues running):

Press: `Ctrl + A`, then `D`

### Attach to existing session:

```bash
screen -r lzt_bot
```

### View all screen sessions:

```bash
screen -ls
```

### Stop bot:

```bash
# Attach to session
screen -r lzt_bot

# Stop bot: Ctrl + C
# Exit screen: exit
```

## Step 8: Auto-start on Reboot

### Option 1: Via systemd (recommended)

Create systemd service:
```bash
sudo nano /etc/systemd/system/lzt-bot.service
```

Insert:
```ini
[Unit]
Description=LZT Market Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/bots/lzt_market_bot
ExecStart=/home/YOUR_USERNAME/bots/lzt_market_bot/venv/bin/python3 /home/YOUR_USERNAME/bots/lzt_market_bot/lzt_market_bot_multilang.py
Restart=always
RestartSec=5
StandardOutput=append:/home/YOUR_USERNAME/bots/lzt_market_bot/bot.log
StandardError=append:/home/YOUR_USERNAME/bots/lzt_market_bot/bot.log

[Install]
WantedBy=multi-user.target
```

**Replace `YOUR_USERNAME` with your username!**

Activate service:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable lzt-bot

# Start service
sudo systemctl start lzt-bot

# Check status
sudo systemctl status lzt-bot

# View logs
sudo journalctl -u lzt-bot -f
```

Service management:
```bash
sudo systemctl start lzt-bot    # Start
sudo systemctl stop lzt-bot     # Stop
sudo systemctl restart lzt-bot  # Restart
sudo systemctl status lzt-bot   # Status
```

### Option 2: Via crontab + screen

```bash
crontab -e
```

Add line:
```bash
@reboot screen -dmS lzt_bot /home/YOUR_USERNAME/bots/lzt_market_bot/start_bot.sh
```

**Replace `YOUR_USERNAME` with your username!**

Save and exit.

Verify:
```bash
crontab -l
```

## Step 9: View Logs

### Real-time:
```bash
tail -f ~/bots/lzt_market_bot/bot.log
```

### Last 100 lines:
```bash
tail -n 100 ~/bots/lzt_market_bot/bot.log
```

### Search for errors:
```bash
grep -i "error" ~/bots/lzt_market_bot/bot.log
```

### Clear old logs:
```bash
# Create backup
cp bot.log bot.log.backup

# Clear file
> bot.log
```

---

# 📊 Viewing Logs via Bot

## Adding /logs Command to Bot

Add this code to your bot (e.g., in `lzt_market_bot_multilang.py`):

```python
import os
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def send_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send log file to administrator"""
    user_id = update.effective_user.id
    
    # Check permissions (replace with your user_id)
    ADMIN_ID = 6388847  # Your Telegram ID
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You don't have permission to view logs")
        return
    
    log_file = "bot.log"
    
    if not os.path.exists(log_file):
        await update.message.reply_text("❌ Log file not found")
        return
    
    try:
        # Get file size
        file_size = os.path.getsize(log_file)
        
        if file_size > 50 * 1024 * 1024:  # If larger than 50 MB
            await update.message.reply_text(
                f"⚠️ Log file too large ({file_size / 1024 / 1024:.2f} MB)\n"
                "Sending last 1000 lines..."
            )
            
            # Read last 1000 lines
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_lines = lines[-1000:]
            
            # Create temporary file
            temp_file = "bot_last_1000.log"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.writelines(last_lines)
            
            await update.message.reply_document(
                document=open(temp_file, 'rb'),
                filename="bot_last_1000.log",
                caption=f"📋 Last 1000 lines of logs\n📊 Full file size: {file_size / 1024 / 1024:.2f} MB"
            )
            
            os.remove(temp_file)
        else:
            # Send entire file
            await update.message.reply_document(
                document=open(log_file, 'rb'),
                filename="bot.log",
                caption=f"📋 Complete log file\n📊 Size: {file_size / 1024:.2f} KB"
            )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error sending logs: {e}")

# Add handler in main():
application.add_handler(CommandHandler("logs", send_logs))
```

## Using /logs Command

Simply send to bot:
```
/logs
```

Bot will send you `bot.log` file with logs.

---

# 🔧 Useful Commands

## Windows

### View Python processes:
```cmd
tasklist | findstr python
```

### Stop bot:
```cmd
taskkill /F /IM python.exe
```

### Clear logs:
```cmd
echo. > bot.log
```

## Linux

### View processes:
```bash
ps aux | grep python
```

### Stop bot:
```bash
pkill -f lzt_market_bot
```

### Monitor resources:
```bash
htop
```

### Log file size:
```bash
du -h bot.log
```

### Log rotation (automatic cleanup):
```bash
# Create file /etc/logrotate.d/lzt-bot
sudo nano /etc/logrotate.d/lzt-bot
```

Insert:
```
/home/YOUR_USERNAME/bots/lzt_market_bot/bot.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 YOUR_USERNAME YOUR_USERNAME
}
```

---

# 📝 Log Structure

Logs are saved in format:
```
[2025-01-13 18:30:15] INFO - Bot started successfully
[2025-01-13 18:30:16] INFO - Listening for updates...
[2025-01-13 18:30:45] INFO - User 123456789 uploaded 5 accounts
[2025-01-13 18:31:02] ERROR - Failed to upload account: Invalid token
```

---

# 🆘 Troubleshooting

## Windows

### Bot won't start:
1. Check if Python is installed: `python --version`
2. Check dependencies: `pip list`
3. Check config.json for errors
4. Run manually: `python lzt_market_bot_multilang.py`

### Logs not saving:
1. Check write permissions for folder
2. Run cmd as administrator

## Linux

### Bot won't start:
```bash
# Check systemd logs
sudo journalctl -u lzt-bot -n 50

# Check file permissions
ls -la ~/bots/lzt_market_bot/

# Check virtual environment
source venv/bin/activate
python3 lzt_market_bot_multilang.py
```

### Screen not working:
```bash
# Reinstall screen
sudo apt remove screen
sudo apt install screen

# Check sessions
screen -ls
```

---

# ✅ Successful Installation Checklist

## Windows:
- [ ] Python installed and added to PATH
- [ ] Dependencies installed
- [ ] config.json configured
- [ ] start_bot.bat created and working
- [ ] Logs saving to bot.log
- [ ] Auto-start configured (optional)
- [ ] /logs command working

## Linux:
- [ ] Python 3.8+ installed
- [ ] Screen installed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] config.json configured
- [ ] start_bot.sh created and executable
- [ ] Bot running in screen
- [ ] Systemd service configured (optional)
- [ ] Logs saving to bot.log
- [ ] /logs command working

---

**Version:** 1.0.0  
**Date:** 2025-01-13
