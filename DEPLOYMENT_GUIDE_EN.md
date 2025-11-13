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