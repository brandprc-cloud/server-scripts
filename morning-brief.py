#!/usr/bin/env python3
# Утренний брифинг — отправляет сообщение в Telegram каждое утро
# Cron: 6:00 UTC = 9:00 MSK

import urllib.request
import urllib.parse
import json
import os
import re
from datetime import datetime, timezone, timedelta

TOKEN_FILE = os.path.expanduser("~/.claude/channels/telegram/.env")
CHAT_ID = "6061411038"

def load_token():
    with open(TOKEN_FILE) as f:
        for line in f:
            m = re.match(r'TELEGRAM_BOT_TOKEN=(.+)', line.strip())
            if m:
                return m.group(1)
    raise ValueError("TELEGRAM_BOT_TOKEN not found")

def read_todays_events():
    msk = timezone(timedelta(hours=3))
    today = datetime.now(msk).strftime("%d.%m")
    events_file = os.path.expanduser("~/Планировщик/события/июнь-2026.md")
    events = []
    try:
        with open(events_file) as f:
            for line in f:
                if line.strip().startswith(f"- {today}") or line.strip().startswith(f"{today}"):
                    events.append(line.strip().lstrip("- "))
    except FileNotFoundError:
        pass
    return events

def send_message(token, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10)

def main():
    msk = timezone(timedelta(hours=3))
    today_str = datetime.now(msk).strftime("%d.%m.%Y, %A")

    events = read_todays_events()
    events_text = "\n".join(f"  • {e}" for e in events) if events else "  (событий нет)"

    msg = (
        f"☀️ <b>Доброе утро! {today_str}</b>\n\n"
        f"📅 <b>События сегодня:</b>\n{events_text}\n\n"
        f"Напиши мне <b>«план на сегодня»</b> — подготовлю брифинг с задачами по всем проектам "
        f"с учётом твоей энергии и ключевой цели (быстрая монетизация).\n\n"
        f"Или сначала скажи: во сколько лёг и энергия от 1 до 10?"
    )

    token = load_token()
    send_message(token, msg)

if __name__ == "__main__":
    main()
