#!/usr/bin/env python3
# Утренний брифинг — отправляет сообщение в Telegram каждое утро
# Cron: 6:00 UTC = 9:00 MSK

import urllib.request
import urllib.parse
import json
import os
import re
import ssl
from datetime import datetime, timezone, timedelta

# SSL-контекст: обход прокси с самоподписанным сертификатом
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

def read_mentor_action():
    journal_index = os.path.expanduser("~/projects/ai-clone/mastery/journal/INDEX.md")
    try:
        with open(journal_index) as f:
            lines = f.readlines()
        for line in reversed(lines):
            if not line.strip().startswith("|"):
                continue
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cols) < 5:
                continue
            if "Дата" in cols[0] or "---" in cols[0]:
                continue
            action, done = cols[3], cols[4]
            if "[ ]" in done and action and action != "—":
                return action
    except FileNotFoundError:
        pass
    return None

def read_todays_events():
    msk = timezone(timedelta(hours=3))
    today = datetime.now(msk).strftime("%d.%m")
    msk_month = datetime.now(msk).strftime("%B-%Y").lower()
    month_map = {
        "january": "январь", "february": "февраль", "march": "март",
        "april": "апрель", "may": "май", "june": "июнь",
        "july": "июль", "august": "август", "september": "сентябрь",
        "october": "октябрь", "november": "ноябрь", "december": "декабрь",
    }
    en_month, year = msk_month.split("-")
    ru_month = month_map.get(en_month, en_month)
    events_file = os.path.expanduser(f"~/projects/planner/события/{ru_month}-{year}.md")
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
    urllib.request.urlopen(req, timeout=10, context=SSL_CTX)

def main():
    msk = timezone(timedelta(hours=3))
    today_str = datetime.now(msk).strftime("%d.%m.%Y, %A")

    events = read_todays_events()
    events_text = "\n".join(f"  • {e}" for e in events) if events else "  (событий нет)"

    mentor_action = read_mentor_action()
    mentor_block = (
        f"\n\n🎯 <b>Обещание Ментору:</b>\n  {mentor_action}"
    ) if mentor_action else ""

    msg = (
        f"☀️ <b>Доброе утро! {today_str}</b>\n\n"
        f"📅 <b>События сегодня:</b>\n{events_text}"
        f"{mentor_block}\n\n"
        f"Напиши мне <b>«план на сегодня»</b> — подготовлю брифинг с задачами по всем проектам "
        f"с учётом твоей энергии и ключевой цели (быстрая монетизация).\n\n"
        f"Или сначала скажи: во сколько лёг и энергия от 1 до 10?"
    )

    token = load_token()
    send_message(token, msg)

if __name__ == "__main__":
    main()
