#!/usr/bin/env python3
"""
Мониторинг Мастермайнд Смыслокод.

Режимы:
  python3 monitor-smyslokod.py collect   — собрать новые сообщения + алерты + обновить базу
  python3 monitor-smyslokod.py digest    — дайджест за день → канал
"""

import asyncio, sys, json, re, ssl, subprocess, urllib.request
sys.path.insert(0, '/home/claudeuser/projects/server-scripts/monitor-venv/lib/python3.12/site-packages')

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageService
from pathlib import Path
from datetime import datetime, timezone, timedelta

SESSION_FILE   = Path(__file__).parent / "userbot.session"
STATE_FILE     = Path(__file__).parent / "smyslokod_state.json"
BUFFER_FILE    = Path(__file__).parent / "smyslokod_buffer.json"
CONTACTS_FILE  = Path(__file__).parent / "smyslokod_contacts.md"
TOKEN_ENV      = Path.home() / ".claude/channels/telegram/.env"

API_ID        = 2040
API_HASH      = "b18441a1ff607e10a989891a5462e627"
GROUP_ID      = -1003787023644
MONITOR_CHAT  = -1003955860040
MSK           = timezone(timedelta(hours=3))

TOPICS = {
    1:    "Общий чат",
    3:    "Артемий Вещает",
    3722: "Записи встреч",
    334:  "Готовые решения",
    516:  "Вопросы к Артемию",
    40:   "Расскажи о проекте",
    32:   "Ищу/предлагаю",
    44:   "Знакомства",
}

ANDREI_PROFILE = """Андрей Брезгин — предприниматель, AI-консалтинг и продукты:
- AI-SCHOOL: курс по AI/Claude для предпринимателей и команд
- CONSULTING/Agortex: AI-консалтинг — боты, автоматизация, внедрение AI в бизнес
- REVIVEBASE: AI-реактивация спящих клиентов (e-com, школы, услуги, подписки)
- AI-WORKSHOP: тренинг по AI, Дубай
Ищет: клиентов на консалтинг/продукты, партнёров для продвижения, Python/AI разработчиков."""


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {str(t): 0 for t in TOPICS}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_buffer():
    if BUFFER_FILE.exists():
        return json.loads(BUFFER_FILE.read_text())
    return []


def save_buffer(buf):
    BUFFER_FILE.write_text(json.dumps(buf, ensure_ascii=False, indent=2))


def load_token():
    with open(TOKEN_ENV) as f:
        for line in f:
            m = re.match(r'TELEGRAM_BOT_TOKEN=(.+)', line.strip())
            if m:
                return m.group(1)
    raise ValueError("TELEGRAM_BOT_TOKEN не найден")


def send_telegram(token, text):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for i in range(0, len(text), 4000):
        chunk = text[i:i+4000]
        payload = json.dumps({
            "chat_id": MONITOR_CHAT,
            "text": chunk,
            "disable_web_page_preview": True,
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            json.load(r)


def run_claude(prompt, timeout=120):
    result = subprocess.run(
        ["/usr/bin/claude", "--print", "--dangerously-skip-permissions"],
        input=prompt,
        capture_output=True, text=True,
        timeout=timeout,
        cwd="/home/claudeuser",
        env={**__import__('os').environ, "HOME": "/home/claudeuser"},
    )
    return result.stdout.strip()


def check_alerts(new_msgs, token):
    """Claude анализирует новые сообщения — есть ли что-то срочно релевантное."""
    if not new_msgs:
        return
    text = "\n".join(
        f"[{m['topic']}] {m['from']}: {m['text']}"
        for m in new_msgs
    )
    prompt = f"""Профиль Андрея:
{ANDREI_PROFILE}

Новые сообщения из чата Мастермайнд Смыслокод (последние 3 часа):
{text}

Найди сообщения где человек:
— ищет подрядчика, разработчика, эксперта по AI
— строит продукт/бизнес где нужна автоматизация, бот, CRM, сайт, AI, реактивация клиентов
— предлагает партнёрство или совместный проект
— имеет аудиторию/базу клиентов которым можно предложить AI-School или REVIVEBASE
— прямо подходит как клиент для консалтинга

Если НАШЁЛ — ответь строго в формате:
🚨 АЛЕРТ: [топик] [имя @username]
Почему: (1 предложение)
Написать: (конкретный текст первого сообщения)

Если НИЧЕГО релевантного нет — ответь одним словом: ТИХО"""

    result = run_claude(prompt, timeout=60)
    if result and result.strip() != "ТИХО":
        send_telegram(token, "⚡ Смыслокод — новые алерты\n\n" + result)
        print(f"Алерт отправлен")
    else:
        print("Алертов нет")


def update_contacts(new_msgs):
    """Дополняет карточки контактов если известный человек написал что-то новое."""
    if not CONTACTS_FILE.exists() or not new_msgs:
        return

    contacts_text = CONTACTS_FILE.read_text(encoding="utf-8")
    msgs_by_user = {}
    for m in new_msgs:
        uname_match = re.search(r'@(\w+)', m['from'])
        if uname_match:
            uname = uname_match.group(1).lower()
            if uname not in msgs_by_user:
                msgs_by_user[uname] = []
            msgs_by_user[uname].append(f"[{m['topic']}] {m['text'][:300]}")

    if not msgs_by_user:
        return

    updated = False
    lines = contacts_text.split('\n')
    for uname, user_msgs in msgs_by_user.items():
        for i, line in enumerate(lines):
            if f"@{uname}" in line.lower() and line.startswith("**"):
                update_line = f"  _Обновление {datetime.now(MSK).strftime('%d.%m')}: {'; '.join(user_msgs[:2])}_"
                lines.insert(i + 1, update_line)
                updated = True
                print(f"  Обновлена карточка @{uname}")
                break

    if updated:
        CONTACTS_FILE.write_text('\n'.join(lines), encoding="utf-8")


async def collect():
    session_str = SESSION_FILE.read_text().strip()
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    await client.connect()

    state  = load_state()
    buffer = load_buffer()
    total  = 0
    all_new = []

    for topic_id, topic_name in TOPICS.items():
        last_id = state.get(str(topic_id), 0)
        new_msgs = []

        async for msg in client.iter_messages(
            GROUP_ID, reply_to=topic_id, min_id=last_id, limit=50,
        ):
            if isinstance(msg, MessageService) or not msg.text:
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
            new_msgs.append({
                "id":    msg.id,
                "topic": topic_name,
                "from":  sender,
                "text":  msg.text[:500],
                "date":  msg.date.strftime("%d.%m %H:%M"),
            })

        if new_msgs:
            new_msgs.sort(key=lambda m: m["id"])
            state[str(topic_id)] = max(m["id"] for m in new_msgs)
            buffer.extend(new_msgs)
            all_new.extend(new_msgs)
            total += len(new_msgs)
            print(f"  [{topic_name}] +{len(new_msgs)}")

    save_state(state)
    save_buffer(buffer)
    await client.disconnect()
    print(f"Итого новых: {total}")

    if all_new:
        token = load_token()
        check_alerts(all_new, token)
        update_contacts(all_new)


def make_digest():
    buffer = load_buffer()
    if not buffer:
        print("Буфер пуст")
        return

    today = datetime.now(MSK).strftime("%d.%m.%Y")
    msgs_text = "\n".join(
        f"[{m['topic']}] {m['from']}: {m['text']}"
        for m in buffer[-200:]
    )
    prompt = f"""Профиль Андрея:
{ANDREI_PROFILE}

Сообщения из Мастермайнд Смыслокод за {today}:
{msgs_text}

Дайджест для Андрея — только то, что имеет практическую ценность:
1. Топ-3 возможности (клиенты, партнёры, подрядчики) — имя, @username, суть, почему релевантно
2. Топ-2 полезных инструмента/решения — применимость к его проектам
3. Один инсайт от Артемия (если был)

Коротко, без воды. Заголовок: 📊 Дайджест Смыслокод {today}"""

    digest = run_claude(prompt, timeout=120)
    token  = load_token()
    send_telegram(token, digest)
    save_buffer([])
    print(f"Дайджест отправлен ({len(buffer)} сообщений)")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "collect"
    if mode == "collect":
        asyncio.run(collect())
    elif mode == "digest":
        make_digest()
    else:
        print("Использование: collect | digest")
