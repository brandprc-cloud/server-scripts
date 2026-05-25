#!/bin/bash
# Watchdog для Telegram бота — проверяет каждые 2 минуты и перезапускает если завис

BOT_TOKEN="8932583755:AAFcANi4ekDfLHYRlSAeBxz0U5aTNcQ8MSI"
CHAT_ID="6061411038"
CHECK_INTERVAL=120
HIGH_CPU_FILE="/tmp/tg_high_cpu_count"
LOG_FILE="/var/log/claude-telegram.log"
SILENT_THRESHOLD=900  # 15 минут без активности лога = бот завис

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $1"; }

is_bot_responsive() {
    RESULT=$(curl -s --max-time 10 \
        "https://api.telegram.org/bot${BOT_TOKEN}/getMe" \
        | grep -o '"ok":true')
    [[ "$RESULT" == '"ok":true' ]]
}

get_claude_pid() {
    ps aux | grep "claude.*channels.*telegram" | grep -v grep | awk '{print $2}' | head -1
}

is_claude_running() {
    [[ -n "$(get_claude_pid)" ]]
}

is_claude_silent() {
    # Проверяет: лог не обновлялся SILENT_THRESHOLD+ секунд при живом процессе
    # Признак зависания на мёртвом TCP-соединении (типичный сценарий после краша клиента)
    [[ ! -f "$LOG_FILE" ]] && return 1

    NOW=$(date +%s)

    # Сколько секунд назад последний раз обновлялся лог
    LAST_MOD=$(stat -c %Y "$LOG_FILE" 2>/dev/null || echo "$NOW")
    LOG_AGE=$(( NOW - LAST_MOD ))

    # Сколько секунд работает сервис (по wall-clock времени)
    START_TS=$(systemctl show claude-telegram --property=ActiveEnterTimestamp --value 2>/dev/null)
    START_EPOCH=$(date -d "$START_TS" +%s 2>/dev/null || echo "$NOW")
    SERVICE_UPTIME=$(( NOW - START_EPOCH ))

    # Флаг только если сервис работает дольше порога И лог молчит дольше порога
    # Также проверяем есть ли необработанные сообщения в Telegram
    if (( SERVICE_UPTIME > SILENT_THRESHOLD && LOG_AGE > SILENT_THRESHOLD )); then
        PENDING=$(curl -s --max-time 5 \
            "https://api.telegram.org/bot${BOT_TOKEN}/getUpdates?limit=1&timeout=0" \
            2>/dev/null | grep -o '"update_id"' | wc -l)
        (( PENDING > 0 ))  # зависание только если есть необработанные сообщения
    else
        return 1
    fi
}

is_claude_stuck() {
    PID=$(get_claude_pid)
    [[ -z "$PID" ]] && return 1
    # Получаем CPU% из /proc (среднее за последние секунды через ps)
    CPU=$(ps -p "$PID" -o %cpu --no-headers 2>/dev/null | tr -d ' ')
    CPU_INT=${CPU%.*}
    if [[ -n "$CPU_INT" ]] && (( CPU_INT > 80 )); then
        COUNT=$(cat "$HIGH_CPU_FILE" 2>/dev/null || echo 0)
        COUNT=$((COUNT + 1))
        echo "$COUNT" > "$HIGH_CPU_FILE"
        log "Высокая нагрузка CPU: ${CPU}% (счётчик: ${COUNT}/3)"
        (( COUNT >= 3 ))  # зависание подтверждено после 3 проверок подряд
    else
        echo 0 > "$HIGH_CPU_FILE"
        return 1
    fi
}

restart_bot() {
    local REASON="${1:-неизвестна}"
    log "Перезапускаю бот (причина: $REASON)..."
    echo 0 > "$HIGH_CPU_FILE"
    systemctl restart claude-telegram
    sleep 8
    if is_claude_running; then
        log "Бот перезапущен успешно"
        curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
            -H "Content-Type: application/json" \
            -d "{\"chat_id\":\"${CHAT_ID}\",\"text\":\"⚠️ Бот перезапущен автоматически — причина: ${REASON}\"}" > /dev/null
    else
        log "ОШИБКА: Не удалось перезапустить бот"
    fi
}

log "Watchdog запущен (CPU + лог-активность)"
echo 0 > "$HIGH_CPU_FILE"

while true; do
    if ! is_bot_responsive; then
        log "Telegram API недоступен — пропускаю проверку"
    elif ! is_claude_running; then
        log "Бот не работает — перезапускаю"
        restart_bot "процесс упал"
    elif is_claude_stuck; then
        log "Бот завис (высокий CPU 3 проверки подряд) — перезапускаю"
        restart_bot "высокий CPU"
    elif is_claude_silent; then
        log "Бот завис (нет активности лога 15+ мин) — перезапускаю"
        restart_bot "нет активности (мёртвое TCP-соединение?)"
    else
        log "Бот работает нормально"
    fi
    sleep $CHECK_INTERVAL
done
