# Деплой Agortex Webhook

## 1. Вписать токен и chat_id

```bash
nano /etc/systemd/system/agortex-webhook.service
# Заменить ВСТАВИТЬ_ТОКЕН и ВСТАВИТЬ_CHAT_ID
```

## 2. Установить сервис

```bash
cp /root/SCRIPTS/agortex-webhook/agortex-webhook.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable agortex-webhook
systemctl start agortex-webhook
systemctl status agortex-webhook
```

## 3. Проверить что работает

```bash
curl http://localhost:8080/health
# Должно вернуть: {"status": "ok", "service": "agortex-webhook"}
```

## 4. Тест отправки заявки

```bash
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"name":"Тест","contact_type":"telegram","contact":"@test_user"}'
# В Telegram должно прийти уведомление
```

## 5. Открыть порт (если закрыт)

```bash
ufw allow 8080/tcp
```

## 6. Как получить свой chat_id

Написать боту @userinfobot в Telegram — он пришлёт ваш chat_id.

## Структура POST-запроса от формы

```json
{
  "name": "Иван Иванов",
  "contact_type": "telegram",   // telegram | phone | whatsapp
  "contact": "@ivan_business"
}
```

## Что приходит в Telegram

```
🔔 Новая заявка — Agortex
━━━━━━━━━━━━━━━━━━
👤 Имя: Иван Иванов
📱 Связь: Telegram
📬 Контакт: @ivan_business
━━━━━━━━━━━━━━━━━━
Ответить в первые 15 минут ⚡
```
