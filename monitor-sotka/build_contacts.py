#!/usr/bin/env python3
"""Собирает все сообщения из топиков Знакомства и Расскажи о проекте,
строит базу контактов через Claude и сохраняет в файл."""

import asyncio, sys, json, re, ssl, subprocess, urllib.request
sys.path.insert(0, '/home/claudeuser/projects/server-scripts/monitor-venv/lib/python3.12/site-packages')

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageService
from pathlib import Path

SESSION_FILE = Path(__file__).parent / "userbot.session"
OUTPUT_FILE  = Path(__file__).parent / "smyslokod_contacts.md"
TOKEN_ENV    = Path.home() / ".claude/channels/telegram/.env"

API_ID   = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
GROUP_ID = -1003787023644
MONITOR_CHAT = -1003955860040

SCAN_TOPICS = {
    44: "Знакомства",
    40: "Расскажи о проекте",
    32: "Ищу/предлагаю",
}


def load_token():
    with open(TOKEN_ENV) as f:
        for line in f:
            m = re.match(r'TELEGRAM_BOT_TOKEN=(.+)', line.strip())
            if m:
                return m.group(1)


def send_telegram(token, text):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for i in range(0, len(text), 4000):
        chunk = text[i:i+4000]
        payload = json.dumps({
            "chat_id": MONITOR_CHAT,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            json.load(r)


async def collect_all():
    session_str = SESSION_FILE.read_text().strip()
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    await client.connect()

    all_messages = []

    for topic_id, topic_name in SCAN_TOPICS.items():
        msgs = []
        async for msg in client.iter_messages(GROUP_ID, reply_to=topic_id, limit=500):
            if isinstance(msg, MessageService) or not msg.text or len(msg.text) < 30:
                continue
            sender = ""
            if msg.sender:
                s = msg.sender
                first = getattr(s, 'first_name', '') or ''
                last  = getattr(s, 'last_name', '') or ''
                uname = getattr(s, 'username', '') or ''
                sender = f"{first} {last}".strip() or uname or "?"
                if uname:
                    sender += f" (@{uname})"
            msgs.append(f"[{sender}]: {msg.text[:600]}")

        print(f"  [{topic_name}] собрано {len(msgs)} сообщений")
        all_messages.append(f"\n=== {topic_name} ===\n" + "\n\n".join(msgs))

    await client.disconnect()
    return "\n\n".join(all_messages)


def build_contacts(raw_text):
    prompt = f"""Ты анализируешь сообщения из чата "Мастермайнд Смыслокод" — платного сообщества предпринимателей.

Вот сообщения из топиков где люди знакомятся и рассказывают о проектах:

{raw_text[:12000]}

Задача: составь структурированную базу участников.

Для каждого человека выдели:
- Имя и @username (если есть)
- Чем занимается / какой бизнес
- Что ищет / предлагает
- Контакты или ссылки из текста

Формат для каждого участника:
**Имя (@username)**
Бизнес: ...
Ищет/предлагает: ...
Контакт: ...

Пропускай системные сообщения и короткие реплики без информации о человеке.
В конце добавь раздел: **Топ-5 самых интересных для Андрея** (консалтинг, AI-проекты, партнёрства)."""

    result = subprocess.run(
        ["/usr/bin/claude", "--print", "--dangerously-skip-permissions"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=180,
        cwd="/home/claudeuser",
        env={**__import__('os').environ, "HOME": "/home/claudeuser"},
    )
    return result.stdout.strip()


async def main():
    print("Собираю сообщения...")
    raw = await collect_all()

    print("Строю базу контактов через Claude...")
    contacts = build_contacts(raw)

    OUTPUT_FILE.write_text(contacts, encoding="utf-8")
    print(f"Сохранено в {OUTPUT_FILE}")

    token = load_token()
    header = "👥 <b>База участников Мастермайнд Смыслокод</b>\n\n"
    send_telegram(token, header + contacts[:3900])
    print("Отправлено в канал Мониторинг каналов")


asyncio.run(main())
