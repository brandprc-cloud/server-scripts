#!/usr/bin/env python3
import os
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import anthropic

load_dotenv(Path(__file__).parent / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "6061411038"))

PROJECTS_ROOT = Path("/home/claudeuser/projects")
PLANNER = PROJECTS_ROOT / "planner"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

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
- Не придумывай то, чего нет в данных.
- Если вопрос про задачи — используй данные из планировщика, не фантазируй.
"""


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
            l.strip() for l in content.split("\n")
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
        parts.append("**Энергия (последняя запись):**\n" + "\n".join(last))

    today = datetime.now()
    month_file = PLANNER / "события" / f"{today.year}-{today.month:02d}.md"
    events = read_file_safe(month_file)
    if events:
        parts.append(f"**События на {today.strftime('%d.%m.%Y')}:**\n" + events[:600])

    parts.append("**Открытые задачи:**\n" + read_open_tasks())

    return "\n\n".join(parts)


def is_allowed(user_id: int) -> bool:
    return user_id == ALLOWED_USER_ID


async def send_long(update: Update, text: str) -> None:
    """Отправляет сообщение, разбивая на части если > 4000 символов."""
    limit = 4000
    if len(text) <= limit:
        try:
            await update.message.reply_text(text, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(text)
        return
    for i in range(0, len(text), limit):
        chunk = text[i:i + limit]
        try:
            await update.message.reply_text(chunk, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(chunk)


async def call_claude(user_id: int, user_message: str, extra_context: str = "") -> str:
    history = conversation_history.get(user_id, [])
    content = user_message
    if extra_context:
        content = f"{extra_context}\n\nЗапрос: {user_message}"
    history.append({"role": "user", "content": content})
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        reply = response.content[0].text
        history.append({"role": "assistant", "content": reply})
        conversation_history[user_id] = history[-20:]
        return reply
    except Exception as e:
        logger.error("Anthropic API error: %s", type(e).__name__)
        raise


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
    try:
        reply = await call_claude(
            update.effective_user.id,
            "Сделай утренний брифинг. Что важно сегодня? Топ-3 задачи по монетизации.",
            extra_context=ctx,
        )
        await msg.delete()
        await send_long(update, reply)
    except Exception:
        await msg.edit_text("Ошибка при обращении к API. Попробуй снова.")


async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return
    task_text = read_open_tasks()
    await send_long(update, task_text)


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return
    conversation_history.pop(update.effective_user.id, None)
    await update.message.reply_text("История диалога сброшена.")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return
    try:
        reply = await call_claude(update.effective_user.id, update.message.text)
        await send_long(update, reply)
    except Exception:
        await update.message.reply_text("Ошибка при обращении к API. Попробуй снова.")


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан в .env")
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY не задан в .env")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("brief", brief))
    app.add_handler(CommandHandler("tasks", tasks))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    logger.info("Claude personal bot started. Allowed user: %d", ALLOWED_USER_ID)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
