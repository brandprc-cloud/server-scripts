#!/usr/bin/env python3
"""
Скоринг контактов из базы Смыслокода.
Запуск: python3 score_contacts.py
"""

import json, re, ssl, subprocess, urllib.request
from pathlib import Path

CONTACTS_FILE = Path(__file__).parent / "smyslokod_contacts.md"
SCORED_FILE   = Path(__file__).parent / "smyslokod_scored.md"
TOKEN_ENV     = Path.home() / ".claude/channels/telegram/.env"
MONITOR_CHAT  = -1003955860040

ANDREI_PROFILE = """
Андрей Брезгин — предприниматель, AI-консалтинг и продукты.

Проекты:
- AI-SCHOOL: онлайн-курс по работе с Claude/AI для предпринимателей и команд. Ищет: предпринимателей, которые хотят обучить себя или команду AI-инструментам.
- CONSULTING/Agortex: AI-консалтинг для бизнеса — внедрение AI, автоматизация, боты, системы. Ищет: бизнес с болью в операционке, маркетинге, продажах.
- REVIVEBASE: AI-платформа реактивации "спящих" клиентов. Ищет: бизнес с клиентской базой (e-com, школы, услуги, подписки) где клиенты перестают покупать.
- AI-WORKSHOP: тренинг по AI в Дубае. Аудитория — международные предприниматели.

Что предлагает: AI-стратегия, внедрение Claude/AI в процессы, боты, автоматизация, обучение команд.
Что ищет: клиентов на консалтинг, партнёров для продвижения, подрядчиков (Python/AI разработчики).
"""


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
    blocks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for block in blocks:
        payload = json.dumps({
            "chat_id": MONITOR_CHAT,
            "text": block,
            "disable_web_page_preview": True,
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            json.load(r)


def run_claude(prompt):
    result = subprocess.run(
        ["/usr/bin/claude", "--print", "--dangerously-skip-permissions"],
        input=prompt,
        capture_output=True, text=True, timeout=180,
        cwd="/home/claudeuser",
        env={**__import__('os').environ, "HOME": "/home/claudeuser"},
    )
    return result.stdout.strip()


def main():
    contacts_text = CONTACTS_FILE.read_text(encoding="utf-8")

    prompt = f"""Ты анализируешь базу участников сообщества "Мастермайнд Смыслокод".

Профиль Андрея (для кого делаем скоринг):
{ANDREI_PROFILE}

База участников:
{contacts_text}

Задача: для каждого участника расставь метку и напиши одно предложение — почему.

Метки:
🔥 КЛИЕНТ — у него есть боль, которую закрывает AI-SCHOOL, REVIVEBASE или консалтинг
🤝 ПАРТНЁР — может продвигать продукты Андрея или делать совместные проекты
🛠 ПОДРЯДЧИК — нужен как исполнитель (разработчик, маркетолог и т.д.)
👋 НЕТВОРК — полезный контакт на будущее, прямого пересечения сейчас нет
⬜ НЕРЕЛЕВАНТЕН — нет очевидной синергии

Для меток 🔥 и 🤝 добавь: конкретный повод для первого сообщения (1-2 предложения что написать).

Формат:
**Имя (@username)** — МЕТКА
Почему: ...
Написать: ... (только для 🔥 и 🤝)

В конце: топ-3 самых приоритетных контакта с пояснением."""

    print("Запускаю скоринг через Claude...")
    scored = run_claude(prompt)

    SCORED_FILE.write_text(scored, encoding="utf-8")
    print(f"Сохранено в {SCORED_FILE}")

    token = load_token()
    header = "🎯 Скоринг участников Смыслокод\n\n"
    send_telegram(token, header + scored)
    print("Отправлено в канал")


if __name__ == "__main__":
    main()
