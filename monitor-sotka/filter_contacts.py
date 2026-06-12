#!/usr/bin/env python3
"""
Фильтрует 4112 контактов → топ-100 наиболее тёплых и монетизируемых.
Критерии: владелец бизнеса, онлайн-школа, партнёр, AI/автоматизация, личное знакомство.
"""
import asyncio, sys
from pathlib import Path

sys.path.insert(0, '/home/claudeuser/projects/server-scripts/monitor-venv/lib/python3.12/site-packages')
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.contacts import GetContactsRequest

SESSION_FILE = Path(__file__).parent / "userbot.session"
API_ID   = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
OUT_FILE = Path("/home/claudeuser/projects/planner/contacts_hot.md")

def score(name: str, has_username: bool, has_phone: bool) -> tuple[int, list[str]]:
    n = name.lower()
    pts = 0
    reasons = []

    # --- ПЛЮСЫ ---

    # Владелец/руководитель бизнеса → клиент
    if any(w in n for w in ["владелец", "основатель", "директор", "ceo", "owner", "собственник", "предприниматель"]):
        pts += 4; reasons.append("Владелец бизнеса")

    # Онлайн-школа / запуски / продюсер → GetCourse-миграция
    if any(w in n for w in ["онлайн школ", "онлайн-школ", "запуск", "курс", "продюсер", "инфобиз", "getcourse", "гетку"]):
        pts += 4; reasons.append("Онлайн-школа/запуски")

    # AI / автоматизация → AI-аудит
    if any(w in n for w in ["ai", "нейро", "gpt", "автоматиз", "чат-бот", "чатбот", "автоворонк", "бот "]):
        pts += 3; reasons.append("AI/Автоматизация")

    # Сайт / разработка → может купить сайт
    if any(w in n for w in ["сайт", "лендинг", "разработк", "вайкод", "вебсайт"]):
        pts += 2; reasons.append("Нужен сайт")

    # Партнёр → реферал / совместная работа
    if any(w in n for w in ["партнер", "партнёр", "коннектор", "нетворк"]):
        pts += 3; reasons.append("Партнёр")

    # Бизнес в Дубае → AI Workshop + аутрич
    if any(w in n for w in ["дубай", "dubai", "оаэ", "uae", "эмират"]):
        pts += 2; reasons.append("Дубай")

    # Маркетинг / трафик → возможно смежный клиент
    if any(w in n for w in ["маркетолог", "маркетинг", "таргет", "трафик", "smm", "смм"]):
        pts += 1; reasons.append("Маркетинг")

    # Есть username → легко написать
    if has_username:
        pts += 1

    # Есть телефон → ещё один канал
    if has_phone:
        pts += 1

    # --- МИНУСЫ ---

    # Поддержка/сервис → не клиент
    if any(w in n for w in ["поддержк", "support", "service", "сервис"]):
        pts -= 5; reasons.append("❌ Поддержка")

    # Явный подрядчик без других признаков
    if "подрядчик" in n and not any(w in n for w in ["владелец", "основатель", "директор"]):
        pts -= 2; reasons.append("Подрядчик")

    # Второй круг ("от кого-то") — менее тёплый, если нет других плюсов
    if " от " in n and pts < 4:
        pts -= 1

    # Явно нерелевантные
    if any(w in n for w in ["аренда квартир", "такси", "ювелир", "косметолог", "нутрициолог", "фитнес", "визажист"]):
        pts -= 2

    return pts, reasons


async def main():
    session_str = SESSION_FILE.read_text().strip()
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    await client.connect()

    result = await client(GetContactsRequest(hash=0))
    contacts = result.users

    scored = []
    for u in contacts:
        name = f"{u.first_name or ''} {u.last_name or ''}".strip()
        username = f"@{u.username}" if u.username else None
        phone = f"+{u.phone}" if u.phone else None
        pts, reasons = score(name, bool(username), bool(phone))
        if pts >= 3:  # Порог входа в топ
            scored.append((pts, name, username or "—", phone or "—", reasons))

    scored.sort(key=lambda x: -x[0])
    top = scored[:120]  # Берём 120, потом можно урезать

    lines = []
    lines.append("# Горячая база — топ контактов для аутрича\n\n")
    lines.append(f"Отобрано: {len(top)} из 4112 контактов. Порог: 3+ балла.\n\n")
    lines.append("---\n\n")
    lines.append("| Балл | Имя / Аннотация | Username | Телефон | Почему в топе |\n")
    lines.append("|---|---|---|---|---|\n")

    for pts, name, username, phone, reasons in top:
        name_safe = name.replace("|", "/")
        why = ", ".join(reasons)
        lines.append(f"| {pts} | {name_safe} | {username} | {phone} | {why} |\n")

    OUT_FILE.write_text("".join(lines), encoding="utf-8")
    print(f"✅ Горячая база: {len(top)} контактов → {OUT_FILE}")
    print(f"\nТоп-20 предварительно:\n")
    for pts, name, username, phone, reasons in top[:20]:
        print(f"  [{pts}] {name[:60]} | {username} | {', '.join(reasons)}")

    await client.disconnect()

asyncio.run(main())
