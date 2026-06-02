#!/bin/bash
# Мониторинг бота claude-telegram — пишет результаты в лог для анализа
# Запускается каждые 30 минут через cron

LOG="/root/bot-monitor.log"
MAX_LINES=2000

ts() { date '+%Y-%m-%d %H:%M:%S'; }

# Состояние сервиса
SERVICE_ACTIVE=$(systemctl is-active claude-telegram 2>/dev/null)

# PID и память процесса (берём сам claude, не обёртку unbuffer/tclsh)
CLAUDE_PID=$(ps aux | grep "/usr/bin/claude.*channels.*telegram" | grep -v grep | grep -v tclsh | awk '{print $2}' | head -1)
if [[ -n "$CLAUDE_PID" ]]; then
    MEM_MB=$(ps -p "$CLAUDE_PID" -o rss --no-headers 2>/dev/null | awk '{printf "%.0f", $1/1024}')
    CPU=$(ps -p "$CLAUDE_PID" -o %cpu --no-headers 2>/dev/null | tr -d ' ')
else
    MEM_MB="—"
    CPU="—"
fi

# Сколько раз перезапускался за последние 24 часа
RESTARTS=$(journalctl -u claude-telegram --since "24 hours ago" --no-pager 2>/dev/null \
    | grep -c "Started claude-telegram")

# Последняя активность в лог-файле (сколько минут назад)
if [[ -f /var/log/claude-telegram.log ]]; then
    LAST_MOD=$(stat -c %Y /var/log/claude-telegram.log 2>/dev/null)
    NOW=$(date +%s)
    LOG_AGE_MIN=$(( (NOW - LAST_MOD) / 60 ))
else
    LOG_AGE_MIN="—"
fi

# Свободная память сервера
FREE_MB=$(free -m | awk '/^Mem:/{print $7}')

echo "$(ts) | svc:${SERVICE_ACTIVE} | pid:${CLAUDE_PID:-none} | mem:${MEM_MB}MB | cpu:${CPU}% | restarts_24h:${RESTARTS} | log_age:${LOG_AGE_MIN}min | server_free:${FREE_MB}MB" >> "$LOG"

# Не даём логу расти бесконечно
if [[ -f "$LOG" ]]; then
    LINES=$(wc -l < "$LOG")
    if (( LINES > MAX_LINES )); then
        tail -n 1000 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
    fi
fi
