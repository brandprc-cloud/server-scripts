#!/usr/bin/env python3
"""
Agortex — webhook для формы заявки
Форма → этот скрипт → Telegram-уведомление владельцу

Запуск: uvicorn webhook:app --host 0.0.0.0 --port 8080
"""

import os
import json
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = os.environ.get("AGORTEX_BOT_TOKEN", "ВСТАВИТЬ_ТОКЕН")
OWNER_CHAT_ID = os.environ.get("AGORTEX_CHAT_ID", "ВСТАВИТЬ_CHAT_ID")

CONTACT_LABELS = {
    "telegram": "Telegram",
    "phone": "Телефон",
    "whatsapp": "WhatsApp",
}


def send_telegram(text: str) -> bool:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = json.dumps({
        "chat_id": OWNER_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


def send_client_confirmation(contact_type: str, contact: str) -> None:
    """Автоответ клиенту в Telegram (только если контакт — Telegram @username)."""
    if contact_type != "telegram" or not contact.startswith("@"):
        return
    username = contact.lstrip("@")
    # Получаем chat_id по username невозможно через Bot API без предварительного диалога.
    # Автоответ работает только если клиент уже писал боту.
    # Оставляем как заглушку — реализуем через CRM/Zapier позже.
    pass


def format_lead_message(name: str, contact_type: str, contact: str) -> str:
    label = CONTACT_LABELS.get(contact_type, contact_type.capitalize())
    return (
        "🔔 <b>Новая заявка — Agortex</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 Имя: <b>{name}</b>\n"
        f"📱 Связь: {label}\n"
        f"📬 Контакт: <code>{contact}</code>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Ответить в первые 15 минут ⚡"
    )


class WebhookHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        if self.path != "/webhook":
            self._respond(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            content_type = self.headers.get("Content-Type", "")
            if "application/json" in content_type:
                data = json.loads(body)
            else:
                parsed = urllib.parse.parse_qs(body.decode())
                data = {k: v[0] for k, v in parsed.items()}
        except Exception:
            self._respond(400, {"error": "bad request"})
            return

        name = data.get("name", "Не указано").strip()
        contact_type = data.get("contact_type", "").strip().lower()
        contact = data.get("contact", "Не указано").strip()

        message = format_lead_message(name, contact_type, contact)
        success = send_telegram(message)

        if success:
            print(f"[OK] Заявка от {name} ({contact_type}: {contact})")
            self._respond(200, {"status": "ok"})
        else:
            print(f"[ERR] Не удалось отправить Telegram для {name}")
            self._respond(500, {"error": "telegram failed"})

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {"status": "ok", "service": "agortex-webhook"})
        else:
            self._respond(404, {"error": "not found"})

    def _respond(self, code: int, body: dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "https://agortex.com")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}")


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8080))
    print(f"Agortex webhook запущен на {host}:{port}")
    print(f"Bot token: {'OK' if BOT_TOKEN != 'ВСТАВИТЬ_ТОКЕН' else '⚠ НЕ ЗАДАН'}")
    print(f"Chat ID:   {'OK' if OWNER_CHAT_ID != 'ВСТАВИТЬ_CHAT_ID' else '⚠ НЕ ЗАДАН'}")
    server = HTTPServer((host, port), WebhookHandler)
    server.serve_forever()
