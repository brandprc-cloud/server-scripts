#!/usr/bin/env python3
"""
Строит полную базу контактов из Telegram с аннотациями.
Сохраняет в /home/claudeuser/projects/planner/contacts_base.md
"""
import asyncio, sys, re
from pathlib import Path

sys.path.insert(0, '/home/claudeuser/projects/server-scripts/monitor-venv/lib/python3.12/site-packages')
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.contacts import GetContactsRequest

SESSION_FILE = Path(__file__).parent / "userbot.session"
API_ID   = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
OUT_FILE = Path("/home/claudeuser/projects/planner/contacts_base.md")

def extract_info(name: str) -> dict:
    """Извлекает ключевые слова из аннотированного имени контакта."""
    name_lower = name.lower()

    tags = []

    # Города/страны
    for loc in ["дубай", "бали", "москва", "питер", "казань", "нидерланды", "дубаи", "эмираты", "турция", "грузия", "тайланд", "израиль"]:
        if loc in name_lower:
            tags.append(loc.capitalize())

    # Сферы деятельности
    spheres = {
        "таргет": "Таргет", "smm": "SMM", "смм": "SMM",
        "продюсер": "Продюсирование", "продюс": "Продюсирование",
        "коуч": "Коучинг", "наставник": "Наставничество",
        "юрист": "Юриспруденция", "адвокат": "Юриспруденция",
        "недвиж": "Недвижимость", "недвижи": "Недвижимость",
        "инвест": "Инвестиции",
        "программ": "Разработка", "developer": "Разработка", "девелоп": "Разработка",
        "дизайн": "Дизайн",
        "маркетолог": "Маркетинг", "маркетинг": "Маркетинг",
        "трафик": "Трафик",
        "бот": "Чат-боты", "чат-бот": "Чат-боты", "автоворонк": "Автоворонки",
        "ai": "AI/Нейросети", "нейро": "AI/Нейросети", "gpt": "AI/Нейросети",
        "онлайн школ": "Онлайн-школа", "онлайн-школ": "Онлайн-школа",
        "запуск": "Запуски",
        "барбершоп": "Барбершоп",
        "ресторан": "Ресторан/HoReCa", "кафе": "Ресторан/HoReCa",
        "визы": "Визы",
        "финансист": "Финансы", "бухгалт": "Финансы",
        "психолог": "Психология",
        "нутрициолог": "Нутрициология",
        "регистрац": "Регистрация компаний",
        "франшиз": "Франшиза",
        "видео": "Видеопроизводство",
        "сайт": "Сайты",
        "копирайт": "Копирайтинг",
        "медиа": "Медиа",
        "подкаст": "Подкасты",
        "пиар": "PR", "pr": "PR",
        "hr": "HR", "рекрутинг": "HR",
    }
    for key, label in spheres.items():
        if key in name_lower and label not in tags:
            tags.append(label)

    # Особые метки
    if any(w in name_lower for w in ["подрядчик", "исполнитель"]):
        tags.append("Подрядчик")
    if any(w in name_lower for w in ["клиент", "покупатель"]):
        tags.append("Клиент")
    if any(w in name_lower for w in ["партнер", "партнёр"]):
        tags.append("Партнёр")
    if any(w in name_lower for w in ["владелец", "основатель", "owner", "ceo", "директор"]):
        tags.append("Владелец/CEO")

    return {"tags": ", ".join(tags) if tags else "—"}


async def main():
    session_str = SESSION_FILE.read_text().strip()
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    await client.connect()

    result = await client(GetContactsRequest(hash=0))
    contacts = result.users
    print(f"Получено контактов: {len(contacts)}")

    # Сортировка по имени
    contacts_sorted = sorted(contacts, key=lambda x: (x.first_name or "яя").lower())

    lines = []
    lines.append("# База контактов Telegram\n")
    lines.append(f"Всего: {len(contacts)} контактов. Обновлено: 12.06.2026\n")
    lines.append("---\n")
    lines.append("| # | Имя / Аннотация | Username | Телефон | Теги |\n")
    lines.append("|---|---|---|---|---|\n")

    for i, u in enumerate(contacts_sorted, 1):
        name = f"{u.first_name or ''} {u.last_name or ''}".strip()
        username = f"@{u.username}" if u.username else "—"
        phone = f"+{u.phone}" if u.phone else "—"
        info = extract_info(name)
        tags = info["tags"]
        # Экранируем | в имени
        name_safe = name.replace("|", "/")
        lines.append(f"| {i} | {name_safe} | {username} | {phone} | {tags} |\n")

    OUT_FILE.write_text("".join(lines), encoding="utf-8")
    print(f"✅ База сохранена: {OUT_FILE}")
    print(f"   Размер: {OUT_FILE.stat().st_size // 1024} KB")

    await client.disconnect()

asyncio.run(main())
