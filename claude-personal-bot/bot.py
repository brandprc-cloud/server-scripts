#!/usr/bin/env python3
import asyncio
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv(Path(__file__).parent / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "6061411038"))

CLAUDE_BIN = "/usr/bin/claude"
PROJECTS_ROOT = Path("/home/claudeuser/projects")
PLANNER = PROJECTS_ROOT / "planner"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

conversation_history: dict[int, list] = {}

SYSTEM_PROMPT = """Ты — личный ИИ-ассистент Андрея Брезгина. Работаешь через Telegram-бот на его сервере.

Андрей — предприниматель. Главный фильтр любой задачи: быстрая монетизация.

Проекты:
- AI-SCHOOL: онлайн-курс по AI/Claude. Готов, DNS настроен. Осталось: Prodamus (оплата).
- CONSULTING/Agortex: консалтинг. 7 репозиториев.
- REVIVEBASE: AI-платформа реактивации клиентов. 5 репозиториев.
- AI-WORKSHOP: тренинг по AI в Дубае (Андрей — продюсер, Арташес — эксперт).

Правила ответов:
- Коротко и по делу. Без воды.
- Всегда на русском языке.
- Когда получаешь данные из файлов — форматируй читаемо, выдели главное.
- Не придумывай то, чего нет в данных."""


def read_file_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def read_open_tasks() -> str:
    tasks_dir = PLANNER / "задачи"
    result = []
    for f in sorted(tasks_dir.glob("*.md")):
        content = read_file_safe(f)
        open_lines = [
            l.strip()
            for l in content.split("\n")
            if l.strip().startswith(("- [ ]", "- [!]", "- [~]"))
        ]
        if open_lines:
            result.append(f"*{f.stem}:*")
            result.extend(open_lines[:5])
    return "\n".join(result) if result else "Открытых задач нет."


def read_brief_context() -> str:
    parts = []

    energy = read_file_safe(PLANNER / "энергия.md")
    if energy:
        last = [l for l in energy.split("\n") if l.strip()][-6:]
        parts.append("Энергия (последняя запись):\n" + "\n".join(last))

    today = datetime.now()
    month_file = PLANNER / "события" / f"{today.year}-{today.month:02d}.md"
    events = read_file_safe(month_file)
    if events:
        parts.append(f"События на {today.strftime('%d.%m.%Y')}:\n" + events[:600])

    parts.append("Открытые задачи:\n" + read_open_tasks())

    return "\n\n".join(parts)


def build_prompt(history: list, new_message: str, extra_context: str = "") -> str:
    lines = [SYSTEM_PROMPT, ""]
    if history:
        lines.append("История диалога:")
        for msg in history[-10:]:
            role = "Андрей" if msg["role"] == "user" else "Claude"
            lines.append(f"{role}: {msg['content']}")
        lines.append("")
    if extra_context:
        lines.append("Данные из файлов:")
        lines.append(extra_context)
        lines.append("")
    lines.append(f"Андрей: {new_message}")
    return "\n".join(lines)


async def run_claude(prompt: str) -> str:
    loop = asyncio.get_event_loop()

    def _run():
        result = subprocess.run(
            [CLAUDE_BIN, "--print"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "HOME": "/home/claudeuser"},
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "claude вернул ошибку")
        return result.stdout.strip()

    return await loop.run_in_executor(None, _run)


def is_allowed(user_id: int) -> bool:
    return user_id == ALLOWED_USER_ID


async def send_long(update: Update, text: str) -> None:
    limit = 4000
    for i in range(0, len(text), limit):
        chunk = text[i : i + limit]
        try:
            await update.message.reply_text(chunk, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(chunk)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return
    await update.message.reply_text(
        "Привет, Андрей. Готов работать.\n\n"
        "/brief — утренний брифинг\n"
        "/tasks — все открытые задачи\n"
        "/clear — сбросить историю диалога\n"
        "/help — список команд"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return
    await update.message.reply_text(
        "Команды:\n"
        "/brief — брифинг: энергия + события + топ-задачи\n"
        "/tasks — все открытые задачи по проектам\n"
        "/clear — сбросить историю диалога\n\n"
        "Или просто пиши — отвечу с контекстом твоих проектов."
    )


async def brief(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return
    msg = await update.message.reply_text("Читаю данные...")
    ctx = read_brief_context()
    user_id = update.effective_user.id
    history = conversation_history.get(user_id, [])
    try:
        prompt = build_prompt(
            history,
            "Сделай утренний брифинг. Что важно сегодня? Топ-3 задачи по монетизации.",
            extra_context=ctx,
        )
        reply = await run_claude(prompt)
        history.append({"role": "user", "content": "утренний брифинг"})
        history.append({"role": "assistant", "content": reply})
        conversation_history[user_id] = history[-20:]
        await msg.delete()
        await send_long(update, reply)
    except Exception as e:
        logger.error("brief error: %s", e)
        await msg.edit_text("Ошибка при запросе к Claude. Проверь сессию: `claude --print 'ping'`")


async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return
    await send_long(update, read_open_tasks())


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return
    conversation_history.pop(update.effective_user.id, None)
    await update.message.reply_text("История диалога сброшена.")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return
    user_id = update.effective_user.id
    history = conversation_history.get(user_id, [])
    try:
        prompt = build_prompt(history, update.message.text)
        reply = await run_claude(prompt)
        history.append({"role": "user", "content": update.message.text})
        history.append({"role": "assistant", "content": reply})
        conversation_history[user_id] = history[-20:]
        await send_long(update, reply)
    except Exception as e:
        logger.error("chat error: %s", e)
        await update.message.reply_text(
            "Ошибка при запросе к Claude. Проверь сессию: `claude --print 'ping'`"
        )


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан в .env")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("brief", brief))
    app.add_handler(CommandHandler("tasks", tasks))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    logger.info("Claude personal bot (CLI mode) started. Allowed user: %d", ALLOWED_USER_ID)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
