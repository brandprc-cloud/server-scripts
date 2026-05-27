#!/bin/bash
# Снимает мобильный скриншот сайта и отправляет в Telegram
# Использование: ./mobile-screenshot.sh [url] [caption]

BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
CHAT_ID="${TELEGRAM_CHAT_ID:-6061411038}"
URL="${1:-https://consulting-site-opal-gamma.vercel.app}"
CAPTION="${2:-📱 Мобильная версия сайта}"
FNAME="mobile_shot_$$.png"
# snap chromium пишет в свою папку
SNAP_TMP="/tmp/snap-private-tmp/snap.chromium/tmp/$FNAME"

echo "Снимаю: $URL"
chromium-browser \
  --headless \
  --no-sandbox \
  --disable-gpu \
  --disable-dev-shm-usage \
  --window-size=390,844 \
  --screenshot="/tmp/$FNAME" \
  "$URL" 2>/dev/null

# ждём файл (snap пишет в свою tmp)
sleep 1
if [ -f "$SNAP_TMP" ]; then
  SHOT="$SNAP_TMP"
elif [ -f "/tmp/$FNAME" ]; then
  SHOT="/tmp/$FNAME"
else
  echo "Ошибка: файл не найден"
  exit 1
fi

echo "Отправляю в Telegram..."
RESULT=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendPhoto" \
  -F "chat_id=${CHAT_ID}" \
  -F "photo=@${SHOT}" \
  -F "caption=${CAPTION}")

echo "$RESULT" | grep -o '"ok":[^,]*'
rm -f "$SHOT"
echo "Готово"
