#!/usr/bin/env python3
import asyncio, sys
from pathlib import Path

sys.path.insert(0, '/home/claudeuser/projects/server-scripts/monitor-venv/lib/python3.12/site-packages')
from telethon import TelegramClient
from telethon.sessions import StringSession

SESSION_FILE = Path(__file__).parent / "userbot.session"
API_ID   = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"

async def main():
    session_str = SESSION_FILE.read_text().strip()
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    await client.connect()

    from telethon.tl.functions.contacts import GetContactsRequest
    result = await client(GetContactsRequest(hash=0))
    contacts = result.users
    print(f"Всего контактов: {len(contacts)}\n")

    for u in sorted(contacts, key=lambda x: (x.first_name or "")):
        name = f"{u.first_name or ''} {u.last_name or ''}".strip()
        username = f"@{u.username}" if u.username else "—"
        phone = f"+{u.phone}" if u.phone else "—"
        print(f"{name} | {username} | {phone}")

    await client.disconnect()

asyncio.run(main())
