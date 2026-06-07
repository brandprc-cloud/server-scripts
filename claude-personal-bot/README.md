# Claude Personal Bot

Личный Telegram-бот для управления задачами и общения с Claude.

## Текущая версия: CLI (без доп. оплаты)

Работает через `claude --print` — использует существующую подписку claude.ai.
Не требует Anthropic API-ключа.

> **Платная альтернатива:** можно переделать на Anthropic API (`ANTHROPIC_API_KEY`).
> Преимущество — сессия никогда не умирает. Скажи Claude: *«Переделай бота на API»*.

---

## Автономность

Бот работает как systemd user service и **не зависит** от открытых сессий
Claude Code, VSCode или терминала. Закрывай всё — бот продолжает работать.

При перезагрузке сервера поднимается автоматически.
При краше — systemd перезапускает через 15 секунд.

---

## Причины остановки и что делать

| Причина | Вероятность | Решение |
|---|---|---|
| Истекла сессия claude.ai | Раз в несколько недель | `claude` в терминале → браузерная авторизация |
| Сервер перезагрузился | Редко | Поднимается сам |
| Краш бота | Редко | Поднимается сам (15 сек) |
| Telegram API недоступен | Очень редко | Само проходит |

На сервере уже стоит `claude-token-refresh.timer` — обновляет токен каждые 30 минут,
что сильно снижает вероятность истечения сессии.

---

## Команды бота

| Команда | Что делает |
|---|---|
| `/brief` | Утренний брифинг: энергия + события + топ-задачи |
| `/tasks` | Все открытые задачи по проектам |
| `/clear` | Сбросить историю диалога |
| Текст | Свободный чат с контекстом проектов |

---

## Управление сервисом

```bash
# Статус
systemctl --user status claude-personal-bot

# Перезапуск
systemctl --user restart claude-personal-bot

# Логи
journalctl --user -u claude-personal-bot -f
```

---

## Структура

```
claude-personal-bot/
  bot.py            — основной код (CLI-режим)
  .env              — токены (не в git)
  .env.example      — шаблон переменных
  requirements.txt  — зависимости Python
  .gitignore
```

## Установка с нуля

```bash
uv venv .venv --python 3.12
uv pip install -r requirements.txt
cp .env.example .env
# заполни TELEGRAM_BOT_TOKEN и ALLOWED_USER_ID в .env
systemctl --user enable --now claude-personal-bot
```
