#!/usr/bin/env python3
"""
Двухшаговая авторизация userbot без интерактивного ввода.
Шаг 1: python3 auth_userbot.py step1 +7XXXXXXXXXX
Шаг 2: python3 auth_userbot.py step2 +7XXXXXXXXXX КОД ХЭШ
"""

import asyncio, sys, json
from pathlib import Path

sys.path.insert(0, '/home/claudeuser/projects/server-scripts/monitor-venv/lib/python3.12/site-packages')
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError

SESSION_FILE  = Path(__file__).parent / "userbot.session"
STATE_FILE    = Path(__file__).parent / "auth_state.json"

API_ID   = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"


async def step1(phone: str):
    string_session = StringSession()
    client = TelegramClient(string_session, API_ID, API_HASH)
    await client.connect()
    result = await client.send_code_request(phone)
    session_str = string_session.save()
    state = {
        "phone": phone,
        "phone_code_hash": result.phone_code_hash,
        "session_str": session_str,
    }
    STATE_FILE.write_text(json.dumps(state))
    print(f"✅ Код отправлен на {phone}")
    await client.disconnect()


async def step2(code: str):
    if not STATE_FILE.exists():
        print("❌ Сначала запусти step1")
        return
    state = json.loads(STATE_FILE.read_text())
    phone            = state["phone"]
    phone_code_hash  = state["phone_code_hash"]
    session_str      = state["session_str"]

    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    await client.connect()
    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
    except SessionPasswordNeededError:
        # Сохраняем session_str для step2fa
        mid_session = StringSession.save(client.session)
        state["mid_session"] = mid_session
        STATE_FILE.write_text(json.dumps(state))
        print("2FA_REQUIRED")
        await client.disconnect()
        return

    me = await client.get_me()
    final_session = StringSession.save(client.session)
    SESSION_FILE.write_text(final_session)
    print(f"✅ Авторизация успешна! Аккаунт: {me.first_name} (@{me.username})")
    STATE_FILE.unlink(missing_ok=True)
    await client.disconnect()


async def step2fa(password: str):
    if not STATE_FILE.exists():
        print("❌ Сначала запусти step1 и step2")
        return
    state = json.loads(STATE_FILE.read_text())
    mid_session = state.get("mid_session")
    if not mid_session:
        print("❌ mid_session не найден, запусти step1 заново")
        return

    client = TelegramClient(StringSession(mid_session), API_ID, API_HASH)
    await client.connect()
    await client.sign_in(password=password)
    me = await client.get_me()
    final_session = StringSession.save(client.session)
    SESSION_FILE.write_text(final_session)
    print(f"✅ Авторизация успешна! Аккаунт: {me.first_name} (@{me.username})")
    STATE_FILE.unlink(missing_ok=True)
    await client.disconnect()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:\n  step1 +7XXXXXXXXXX\n  step2 КОД")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "step1":
        asyncio.run(step1(sys.argv[2]))
    elif cmd == "step2":
        asyncio.run(step2(sys.argv[2]))
    elif cmd == "step2fa":
        asyncio.run(step2fa(sys.argv[2]))
    else:
        print(f"Неизвестная команда: {cmd}")
