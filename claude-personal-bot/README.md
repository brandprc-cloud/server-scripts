# Claude Personal Bot

Личный Telegram-бот для управления задачами и общения с Claude.

## Версия: Платная (Anthropic API)

Эта версия использует Anthropic API с ключом (`ANTHROPIC_API_KEY`).
Требует пополненного баланса на [console.anthropic.com](https://console.anthropic.com).

> **Альтернатива:** можно переделать под Claude CLI — бот будет работать
> через существующую подписку claude.ai без дополнительной оплаты.
> Скажи Claude: *«Переделай бота под CLI»* — займёт 10 минут.

## Настройка

1. Скопируй `.env.example` в `.env`
2. Добавь `TELEGRAM_BOT_TOKEN` и `ANTHROPIC_API_KEY`
3. Создай venv: `uv venv .venv --python 3.12`
4. Установи зависимости: `uv pip install -r requirements.txt`
5. Запусти сервис: `systemctl --user enable --now claude-personal-bot`

## Команды бота

| Команда | Что делает |
|---|---|
| `/brief` | Утренний брифинг: энергия + события + топ-задачи |
| `/tasks` | Все открытые задачи по проектам |
| `/clear` | Сбросить историю диалога |
| Текст | Свободный чат с контекстом проектов |

## Файлы

```
claude-personal-bot/
  bot.py          — основной код
  .env            — токены (не в git)
  requirements.txt
  .gitignore
```
