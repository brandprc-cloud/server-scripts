#!/bin/bash
# backup-to-github.sh
set -e

BACKUP_DIR="/root/BOT-BACKUP"
cd "$BACKUP_DIR"

cp /root/CLAUDE.md ./CLAUDE.md 2>/dev/null || true
cp /root/backup-to-github.sh ./backup-to-github.sh 2>/dev/null || true
cp /root/start-telegram-bot.sh ./start-telegram-bot.sh 2>/dev/null || true
cp /root/stop-notify-tg.sh ./stop-notify-tg.sh 2>/dev/null || true
cp /root/telegram-watchdog.sh ./telegram-watchdog.sh 2>/dev/null || true

mkdir -p claude-config
cp /root/.claude/settings.json ./claude-config/settings.json 2>/dev/null || true
cp /root/.claude/security-guard.py ./claude-config/security-guard.py 2>/dev/null || true
cp /root/.claude/notify-sound.sh ./claude-config/notify-sound.sh 2>/dev/null || true

mkdir -p systemd
cp /etc/systemd/system/claude-telegram.service ./systemd/claude-telegram.service 2>/dev/null || true
cp /etc/systemd/system/claude-telegram.service.d/limits.conf ./systemd/limits.conf 2>/dev/null || true

git add -A
if git diff --cached --quiet; then
    echo "$(date): nothing changed, skip"
    exit 0
fi
git commit -m "backup $(date '+%Y-%m-%d %H:%M')"
git push -u origin main
echo "$(date): backup pushed"
