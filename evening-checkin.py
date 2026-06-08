#!/usr/bin/env python3
# Вечерний чекин — отправляет сообщение в Telegram каждый вечер
# Cron: 19:00 UTC = 22:00 MSK

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

def send_message(token, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10, context=SSL_CTX)

def main():
    msk = timezone(timedelta(hours=3))
    today_str = datetime.now(msk).strftime("%d.%m")

    msg = (
        f"🌙 <b>Вечерний чекин — {today_str}</b>\n\n"
        f"Ответь на несколько вопросов — займёт 2 минуты:\n\n"
        f"1️⃣ <b>Энергия за день</b> — от 1 до 10?\n"
        f"2️⃣ <b>Доход сегодня</b> — сколько рублей принёс день? (0 если ничего)\n"
        f"3️⃣ <b>Главное обещание себе</b> — что планировал сделать сегодня? Выполнил?\n"
        f"4️⃣ <b>Что сделал</b> из запланированного?\n"
        f"5️⃣ <b>Что пропустил</b> — и почему?\n"
        f"6️⃣ <b>Лучшие часы</b> — когда был в потоке?\n"
        f"7️⃣ <b>Во сколько планируешь лечь?</b>\n\n"
        f"Можно ответить одним голосовым или текстом в свободной форме — я сам запишу в журнал."
    )

    token = load_token()
    send_message(token, msg)

if __name__ == "__main__":
    main()

