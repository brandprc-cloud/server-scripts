#!/usr/bin/env python3
# Supabase keep-alive ping — agortex-partners
# Предотвращает приостановку проекта на Free tier (7 дней без активности)
# Запускается раз в 3 дня через systemd timer

import urllib.request
import json
import os
import re
import ssl
from datetime import datetime, timezone, timedelta

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

TOKEN_FILE = os.path.expanduser("~/.claude/channels/telegram/.env")
CHAT_ID = "6061411038"
SUPABASE_URL = "https://asdnltxyuruhqnvyrrst.supabase.co/rest/v1/"
LOG_FILE = os.path.expanduser("~/.claude/channels/telegram/supabase-ping.log")
MSK = timezone(timedelta(hours=3))


def load_token():
    with open(TOKEN_FILE) as f:
        for line in f:
            m = re.match(r'TELEGRAM_BOT_TOKEN=(.+)', line.strip())
            if m:
                return m.group(1)
    raise ValueError("TELEGRAM_BOT_TOKEN not found")


def send_telegram(token, text):
    data = json.dumps({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req, context=SSL_CTX, timeout=15)


def ping_supabase():
    try:
        req = urllib.request.Request(SUPABASE_URL)
        try:
            urllib.request.urlopen(req, context=SSL_CTX, timeout=15)
            return 200
        except urllib.error.HTTPError as e:
            return e.code
    except Exception:
        return 0


def main():
    ts = datetime.now(MSK).strftime('%Y-%m-%d %H:%M:%S MSK')
    code = ping_supabase()

    with open(LOG_FILE, 'a') as f:
        f.write(f"{ts} supabase-ping agortex-partners: HTTP {code}\n")

    if code in (503, 0):
        try:
            token = load_token()
            if code == 503:
                msg = "503 — проект приостановлен. Зайди в dashboard и нажми Restore:\nhttps://supabase.com/dashboard/project/asdnltxyuruhqnvyrrst"
            else:
                msg = "0 — недоступен (таймаут). Проверь статус вручную:\nhttps://supabase.com/dashboard/project/asdnltxyuruhqnvyrrst"
            send_telegram(token, f"⚠️ Supabase agortex-partners: {msg}")
        except Exception as e:
            with open(LOG_FILE, 'a') as f:
                f.write(f"{ts} telegram notify failed: {e}\n")


if __name__ == "__main__":
    main()
