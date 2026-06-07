#!/usr/bin/env python3
# Напоминания по трекеру Анастасии
# Ежедневно: 10:00 MSK (7:00 UTC) — проверить публикации
# Еженедельно: воскресенье 19:00 MSK (16:00 UTC) — итоги недели

import urllib.request
import urllib.parse
import json
import os
import re
import ssl
import sys
from datetime import datetime, timezone, timedelta

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

TOKEN_FILE = os.path.expanduser("~/.claude/channels/telegram/.env")
CHAT_ID = "6061411038"

def load_token():
    with open(TOKEN_FILE) as f:
        for line in f:
            m = re.match(r'TELEGRAM_BOT_TOKEN=(.+)', line.strip())
            if m:
                return m.group(1)
    raise ValueError("TELEGRAM_BOT_TOKEN not found")

def send_message(text):
    token = load_token()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as r:
        return json.loads(r.read())

def daily_reminder():
    msk = timezone(timedelta(hours=3))
    today = datetime.now(msk).strftime("%d.%m.%Y")
    text = (
        f"📋 <b>Трекер Анастасии — {today}</b>\n\n"
        f"Проверь публикации за сегодня:\n"
        f"• Instagram Reels — вышел?\n"
        f"• Сторис — есть публикации?\n"
        f"• Telegram — пост опубликован?\n"
        f"• Threads — пост опубликован?\n"
        f"• YouTube Shorts — вышел?\n\n"
        f"Внеси данные в трекер:\n"
        f"planner/партнёры/анастасия/трекер-контента.md"
    )
    send_message(text)

def weekly_summary():
    msk = timezone(timedelta(hours=3))
    today = datetime.now(msk).strftime("%d.%m.%Y")
    text = (
        f"📊 <b>Итоги недели — Анастасия ({today})</b>\n\n"
        f"Время сделать сверку:\n\n"
        f"<b>1. Количество контента за неделю:</b>\n"
        f"• Instagram Reels: _ из 8\n"
        f"• Сторис: _ из 40\n"
        f"• Telegram: _ из 12\n"
        f"• Threads: _ из 12\n"
        f"• YouTube Shorts: _ из 8\n\n"
        f"<b>2. Задачи</b> — что поставила, что выполнила?\n\n"
        f"<b>3. Контент-план на следующую неделю</b> — прислала?\n\n"
        f"<b>4. Если последняя неделя месяца:</b>\n"
        f"• Итоги месяца по всем каналам\n"
        f"• План на следующий месяц\n"
        f"• Продление договора"
    )
    send_message(text)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    if mode == "weekly":
        weekly_summary()
    else:
        daily_reminder()
