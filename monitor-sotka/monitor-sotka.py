#!/usr/bin/env python3
"""Мониторинг канала @sotka2044 — извлекает новые посты, контакты, возможности."""

import json
import re
import ssl
import os
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

CHANNEL = "sotka2044"
CHAT_ID = "6061411038"
TOKEN_FILE = Path.home() / ".claude/channels/telegram/.env"
STATE_FILE = Path(__file__).parent / "state.json"
LOG_FILE = Path(__file__).parent / "sotka-log.md"

MSK = timezone(timedelta(hours=3))

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def load_token():
    with open(TOKEN_FILE) as f:
        for line in f:
            m = re.match(r"TELEGRAM_BOT_TOKEN=(.+)", line.strip())
            if m:
                return m.group(1)
    raise ValueError("TELEGRAM_BOT_TOKEN не найден")


def fetch_channel(before_id=None):
    url = f"https://t.me/s/{CHANNEL}"
    if before_id:
        url += f"?before={before_id}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; bot)"},
    )
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=15) as resp:
        return resp.read().decode("utf-8")


def parse_posts(html):
    posts = []
    # Разбиваем на блоки по каждому сообщению
    blocks = re.split(r'(?=<div class="tgme_widget_message_wrap)', html)
    for block in blocks:
        id_match = re.search(r'data-post="[^/]+/(\d+)"', block)
        if not id_match:
            continue
        post_id = int(id_match.group(1))

        # Текст поста (убираем HTML-теги)
        text_match = re.search(
            r'<div class="tgme_widget_message_text[^"]*">(.*?)</div>',
            block,
            re.DOTALL,
        )
        text = ""
        if text_match:
            raw = text_match.group(1)
            # Сохраняем переносы строк
            raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
            text = re.sub(r"<[^>]+>", "", raw).strip()
            text = re.sub(r"\n{3,}", "\n\n", text)

        # Дата
        date_match = re.search(r'datetime="([^"]+)"', block)
        date_raw = date_match.group(1) if date_match else ""

        if post_id and (text or date_raw):
            posts.append({"id": post_id, "text": text, "date": date_raw})

    return sorted(posts, key=lambda p: p["id"])


def extract_entities(text):
    contacts = list(set(re.findall(r"@[\w]{3,}", text)))
    phones = list(set(re.findall(r"(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", text)))

    # Ключевые слова-возможности
    opp_keywords = {
        "маяк": "маяк/партнёр",
        "партнёр": "маяк/партнёр",
        "коннект": "коннект",
        "знакомств": "знакомство",
        "выход на": "выход",
        "клиент": "клиент",
        "сделк": "сделка",
        "пилот": "пилот",
        "фаундер": "фаундер",
        "проект": "проект",
        "инвест": "инвестиции",
        "партнёрств": "партнёрство",
    }
    found_opps = []
    for kw, label in opp_keywords.items():
        if kw.lower() in text.lower() and label not in found_opps:
            found_opps.append(label)

    # Упоминания компаний (слова с заглавной буквы, не в начале предложения — эвристика)
    companies = list(set(re.findall(r"(?<!\. )(?<!\n)([А-ЯA-Z][а-яёa-z]{2,}(?:Base|Tech|Lab|Hub|Fund|Pay|AI|Bot)?)", text)))
    # Фильтруем стоп-слова
    stop = {"Это", "Все", "При", "Как", "Для", "Что", "Когда", "Если", "Там",
            "Уже", "Его", "Они", "Она", "Оно", "Но", "Ещё", "После", "Zoom",
            "YouTube", "Telegram", "Google"}
    companies = [c for c in companies if c not in stop and len(c) > 3][:10]

    return {
        "contacts": contacts,
        "phones": phones,
        "opportunities": found_opps,
        "companies": companies,
    }


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_id": 0}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def append_to_log(new_posts):
    if not new_posts:
        return
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        now = datetime.now(MSK).strftime("%d.%m.%Y %H:%M")
        f.write(f"\n---\n## Обновление {now}\n")
        for p in new_posts:
            e = p["entities"]
            f.write(f"\n### Пост #{p['id']}\n")
            if p["text"]:
                preview = p["text"][:400].replace("\n", " ")
                f.write(f"{preview}\n\n")
            if e["contacts"]:
                f.write(f"**👤 Контакты:** {', '.join(e['contacts'])}\n")
            if e["phones"]:
                f.write(f"**📞 Телефоны:** {', '.join(e['phones'])}\n")
            if e["companies"]:
                f.write(f"**🏢 Компании/проекты:** {', '.join(e['companies'])}\n")
            if e["opportunities"]:
                f.write(f"**💡 Темы:** {', '.join(e['opportunities'])}\n")


def send_telegram(token, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
        return json.loads(resp.read())


def format_notification(posts):
    lines = [f"🔔 <b>Новое в @sotka2044</b> — {len(posts)} пост(ов)\n"]
    for p in posts[:3]:
        e = p["entities"]
        lines.append(f"━━━━━━━━━━━━━━━")
        preview = (p["text"][:200] + "…") if len(p["text"]) > 200 else p["text"]
        if preview:
            lines.append(f"📝 {preview}")
        if e["contacts"]:
            lines.append(f"👤 {', '.join(e['contacts'])}")
        if e["opportunities"]:
            lines.append(f"💡 {', '.join(e['opportunities'])}")
        lines.append(f"🔗 https://t.me/{CHANNEL}/{p['id']}")
    if len(posts) > 3:
        lines.append(f"\n…и ещё {len(posts) - 3} постов")
    return "\n".join(lines)


def main():
    state = load_state()
    token = load_token()

    html = fetch_channel()
    posts = parse_posts(html)

    if not posts:
        return

    new_posts = [p for p in posts if p["id"] > state["last_id"] and p["text"].strip()]

    # При первом запуске — сохраняем текущий максимум, не уведомляем
    if state["last_id"] == 0:
        max_id = max(p["id"] for p in posts)
        save_state({"last_id": max_id})
        send_telegram(token, f"✅ Мониторинг @sotka2044 запущен.\nСлежу за новыми постами каждые 2 часа.\nПоследний пост: #{max_id}")
        return

    if not new_posts:
        return

    # Обогащаем сущностями
    for p in new_posts:
        p["entities"] = extract_entities(p["text"])

    # Сохраняем в лог
    append_to_log(new_posts)

    # Обновляем state
    save_state({"last_id": max(p["id"] for p in new_posts)})

    # Отправляем уведомление
    msg = format_notification(new_posts)
    send_telegram(token, msg)


if __name__ == "__main__":
    main()
