#!/bin/bash
BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
CHAT_ID="${TELEGRAM_CHAT_ID:-6061411038}"

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -d "chat_id=${CHAT_ID}" \
  --data-urlencode "text=Напоминание 🗂

Вчера ты хотел обсудить создание умной CRM с дашбордом по всем проектам:
• Голос Сердца
• Арташес
• Николь
• Вячеслав (100 лидов, Дубай)

Готов проработать архитектуру и начать делать?"
