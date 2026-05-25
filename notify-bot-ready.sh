#!/bin/bash
BOT_TOKEN="8932583755:AAFcANi4ekDfLHYRlSAeBxz0U5aTNcQ8MSI"
CHAT_ID="6061411038"
LOG_FILE="/var/log/claude-telegram.log"
MARKER="Listening"
TIMEOUT=120

# Record log size at start to ignore old entries
sleep 1
START_SIZE=$(stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)

for i in $(seq 1 $TIMEOUT); do
    sleep 1
    if tail -c "+$((START_SIZE + 1))" "$LOG_FILE" 2>/dev/null | grep -q "$MARKER"; then
        curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
            -H "Content-Type: application/json" \
            -d "{\"chat_id\":\"${CHAT_ID}\",\"text\":\"✅ Бот готов к работе\"}" > /dev/null
        exit 0
    fi
done

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -H "Content-Type: application/json" \
    -d "{\"chat_id\":\"${CHAT_ID}\",\"text\":\"⚠️ Бот не запустился за ${TIMEOUT} секунд\"}" > /dev/null
exit 1
