#!/usr/bin/env python3
import re, json, ssl, urllib.request
from pathlib import Path

TOKEN_ENV    = Path.home() / ".claude/channels/telegram/.env"
CONTACTS_FILE = Path(__file__).parent / "smyslokod_contacts.md"
MONITOR_CHAT = -1003955860040

def load_token():
    with open(TOKEN_ENV) as f:
        for line in f:
            m = re.match(r'TELEGRAM_BOT_TOKEN=(.+)', line.strip())
            if m:
                return m.group(1)

def send(token, text):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    payload = json.dumps({
        "chat_id": MONITOR_CHAT,
        "text": text,
        "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        return json.load(r)

token = load_token()
text = CONTACTS_FILE.read_text(encoding="utf-8")

# Разбиваем по блокам контактов чтобы не резать на середине
blocks = text.split("\n---\n")
chunk = ""
for block in blocks:
    if len(chunk) + len(block) + 5 > 4000:
        send(token, chunk.strip())
        chunk = block
    else:
        chunk += "\n---\n" + block if chunk else block

if chunk.strip():
    send(token, chunk.strip())

print(f"Отправлено. Всего символов: {len(text)}")
