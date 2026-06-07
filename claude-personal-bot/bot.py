#!/usr/bin/env python3
import asyncio
import logging
import os
import re
import subprocess
from datetime import datetime, time
from pathlib import Path

import pytz
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv(Path(__file__).parent / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID    = int(os.getenv("ALLOWED_USER_ID", "6061411038"))
ANDREI_CHAT_ID     = int(os.getenv("ANDREI_CHAT_ID", "0"))

CLAUDE_BIN  = "/usr/bin/claude"
ROOT        = Path("/home/claudeuser")
PROJECTS    = ROOT / "projects"
PLANNER     = PROJECTS / "planner"
AI_CLONE    = PROJECTS / "ai-clone"
MSK         = pytz.timezone("Europe/Moscow")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

conversation_history: dict[int, list] = {}
andrei_chat_id: int = ANDREI_CHAT_ID  # обновляется при первом /start

# Маппинг ключевых слов → папки/файлы проектов
PROJECT_MAP = {
    "ai-school":    PROJECTS / "AI-SCHOOL",
    "ai school":    PROJECTS / "AI-SCHOOL",
    "school":       PROJECTS / "AI-SCHOOL",
    "школа":        PROJECTS / "AI-SCHOOL",
    "ai-workshop":  PROJECTS / "AI-WORKSHOP",
    "ai workshop":  PROJECTS / "AI-WORKSHOP",
    "workshop":     PROJECTS / "AI-WORKSHOP",
    "воркшоп":      PROJECTS / "AI-WORKSHOP",
    "дубай":        PROJECTS / "AI-WORKSHOP",
    "тренинг":      PROJECTS / "AI-WORKSHOP",
    "revivebase":   PROJECTS / "REVIVEBASE",
    "reactivate":   PROJECTS / "REVIVEBASE",
    "реактивация":  PROJECTS / "REVIVEBASE",
    "consulting":   PROJECTS / "CONSULTING",
    "agortex":      PROJECTS / "CONSULTING",
    "консалтинг":   PROJECTS / "CONSULTING",
    "агортекс":     PROJECTS / "CONSULTING",
    "planner":      PLANNER,
    "планировщик":  PLANNER,
    "задачи":       PLANNER,
    "партнёры":     PLANNER / "партнёры",
    "подрядчики":   PLANNER / "партнёры",
}

# Маппинг проектов → файлы задач в planner
TASKS_FILE_MAP = {
    "ai-school":   "AI-SCHOOL",
    "ai school":   "AI-SCHOOL",
    "школа":       "AI-SCHOOL",
    "ai-workshop": "AI-WORKSHOP",
    "workshop":    "AI-WORKSHOP",
    "воркшоп":     "AI-WORKSHOP",
    "дубай":       "AI-WORKSHOP",
    "тренинг":     "AI-WORKSHOP",
    "revivebase":  "REVIVEBASE",
    "реактивация": "REVIVEBASE",
    "consulting":  "CONSULTING",
    "agortex":     "CONSULTING",
    "консалтинг":  "CONSULTING",
    "агортекс":    "CONSULTING",
    "reactivate":  "REACTIVATE-LANDING",
}


# ─── Чтение файлов ───────────────────────────────────────────────────────────

def read_file_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def load_clone_context() -> str:
    """Загружает ключевые файлы ai-clone для системного промпта."""
    parts = []

    role = read_file_safe(AI_CLONE / "role.md")
    if role:
        parts.append("=== Кто такой Андрей (role.md) ===\n" + role)

    priorities = read_file_safe(AI_CLONE / "action" / "priorities.md")
    if priorities:
        parts.append("=== Приоритеты Андрея ===\n" + priorities[:800])

    decision = read_file_safe(AI_CLONE / "thinking" / "decision-making.md")
    if decision:
        parts.append("=== Как Андрей принимает решения ===\n" + decision[:600])

    # Последние 6 feedback-файлов (самые свежие правила работы)
    feedback_dir = AI_CLONE / "feedback"
    if feedback_dir.exists():
        feedback_files = sorted(feedback_dir.glob("*.md"))[-6:]
        fb_texts = []
        for f in feedback_files:
            if f.name != "CANON.md" and f.name != "INDEX.md":
                content = read_file_safe(f)
                if content:
                    fb_texts.append(f"--- {f.stem} ---\n{content[:300]}")
        if fb_texts:
            parts.append("=== Правила работы (feedback) ===\n" + "\n\n".join(fb_texts))

    return "\n\n".join(parts)


# Кэш контекста клона — читаем один раз при старте
_CLONE_CONTEXT = load_clone_context()

SYSTEM_PROMPT = f"""Ты — личный ИИ-ассистент Андрея Брезгина в Telegram.

{_CLONE_CONTEXT}

---

Проекты:
- AI-SCHOOL: онлайн-курс по AI/Claude. Готов. Осталось: Prodamus (оплата).
- CONSULTING/Agortex: консалтинг. 7 репозиториев.
- REVIVEBASE: AI-платформа реактивации клиентов. 5 репозиториев.
- AI-WORKSHOP: тренинг по AI в Дубае (Андрей — продюсер, Арташес — эксперт).

Правила ответов:
- Коротко и по делу. Без воды.
- Всегда на русском языке.
- Данные из файлов форматируй читаемо, выдели главное.
- Не придумывай то, чего нет в данных."""


# ─── Задачи ──────────────────────────────────────────────────────────────────

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


def add_task_to_file(project_key: str, task_text: str) -> str:
    """Добавляет задачу в нужный файл planner/задачи/. Возвращает результат."""
    filename = TASKS_FILE_MAP.get(project_key.lower())
    if not filename:
        return None, "Проект не распознан"

    tasks_file = PLANNER / "задачи" / f"{filename}.md"
    if not tasks_file.exists():
        return None, f"Файл задач не найден: {filename}.md"

    content = read_file_safe(tasks_file)
    new_line = f"- [ ] {task_text}"

    # Вставляем после строки "## Открытые задачи" или в начало
    if "## Открытые задачи" in content:
        content = content.replace(
            "## Открытые задачи\n",
            f"## Открытые задачи\n\n{new_line}\n",
            1,
        )
    else:
        content = new_line + "\n\n" + content

    tasks_file.write_text(content, encoding="utf-8")
    return filename, None


# ─── Брифинг ─────────────────────────────────────────────────────────────────

def read_brief_context() -> str:
    parts = []

    energy = read_file_safe(PLANNER / "энергия.md")
    if energy:
        last = [l for l in energy.split("\n") if l.strip()][-6:]
        parts.append("Энергия (последняя запись):\n" + "\n".join(last))

    today = datetime.now(MSK)
    month_file = PLANNER / "события" / f"{today.year}-{today.month:02d}.md"
    events = read_file_safe(month_file)
    if events:
        parts.append(f"События на {today.strftime('%d.%m.%Y')}:\n" + events[:600])

    parts.append("Открытые задачи:\n" + read_open_tasks())
    return "\n\n".join(parts)


# ─── Контекст проектов ───────────────────────────────────────────────────────

def detect_project_context(message: str) -> str:
    msg_lower = message.lower()
    found_paths: list[Path] = []

    for keyword, path in PROJECT_MAP.items():
        if keyword in msg_lower:
            found_paths.append(path)

    if not found_paths:
        return ""

    found_paths = list(dict.fromkeys(found_paths))
    parts = []

    for path in found_paths[:2]:
        if not path.exists():
            continue

        if path.is_file():
            content = read_file_safe(path)
            if content:
                parts.append(f"=== {path.name} ===\n{content[:2000]}")
            continue

        for index_name in ("CLAUDE.md", "INDEX.md"):
            idx = path / index_name
            if idx.exists():
                parts.append(f"=== {path.name}/{index_name} ===\n{read_file_safe(idx)[:1500]}")
                break

        tasks_file = PLANNER / "задачи" / f"{path.name}.md"
        if tasks_file.exists():
            parts.append(f"=== Задачи {path.name} ===\n{read_file_safe(tasks_file)[:1500]}")

        if path == PLANNER:
            parts.append("=== Все открытые задачи ===\n" + read_open_tasks())
            partners_dir = path / "партнёры"
            if partners_dir.exists():
                for f in sorted(partners_dir.glob("*.md"))[:3]:
                    parts.append(f"=== Партнёр: {f.stem} ===\n{read_file_safe(f)[:800]}")

        if path.name in ("CONSULTING", "REVIVEBASE"):
            for sub in sorted(path.iterdir()):
                if sub.is_dir():
                    idx = sub / "CLAUDE.md"
                    if idx.exists():
                        parts.append(f"=== {sub.name} ===\n{read_file_safe(idx)[:500]}")

    return "\n\n".join(parts)


# ─── Claude CLI ──────────────────────────────────────────────────────────────

def build_prompt(history: list, new_message: str, extra_context: str = "") -> str:
    lines = [SYSTEM_PROMPT, ""]
    if extra_context:
        lines.append("Данные из файлов на сервере:")
        lines.append(extra_context)
        lines.append("")
    if history:
        lines.append("История диалога:")
        for msg in history[-8:]:
            role = "Андрей" if msg["role"] == "user" else "Claude"
            lines.append(f"{role}: {msg['content']}")
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
            cwd=str(ROOT),
            env={**os.environ, "HOME": str(ROOT)},
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "claude вернул ошибку")
        return result.stdout.strip()

    return await loop.run_in_executor(None, _run)


# ─── Утилиты Telegram ────────────────────────────────────────────────────────

def is_allowed(user_id: int) -> bool:
    return user_id == ALLOWED_USER_ID


async def send_long(update: Update, text: str) -> None:
    limit = 4000
    for i in range(0, len(text), limit):
        chunk = text[i: i + limit]
        try:
            await update.message.reply_text(chunk, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(chunk)


# ─── Хэндлеры ────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global andrei_chat_id
    if not is_allowed(update.effective_user.id):
        return
    andrei_chat_id = update.effective_chat.id
    await update.message.reply_text(
        "Привет, Андрей. Готов работать.\n\n"
        "/brief — утренний брифинг\n"
        "/tasks — все открытые задачи\n"
        "/add — добавить задачу\n"
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
        "/add AI-SCHOOL Подключить Prodamus до 15.06 — добавить задачу\n"
        "/clear — сбросить историю диалога\n\n"
        "Просто пиши — если упомянешь проект, я сам прочитаю нужные файлы."
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
        await msg.edit_text("Ошибка при запросе к Claude.")


async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return
    await send_long(update, read_open_tasks())


async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return

    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            "Формат: /add ПРОЕКТ Текст задачи\n\n"
            "Примеры:\n"
            "/add AI-SCHOOL Подключить Prodamus до 15.06\n"
            "/add AI-WORKSHOP Созвон с Арташесом в пятницу\n"
            "/add REVIVEBASE Добавить онбординг\n"
            "/add CONSULTING Подготовить оффер"
        )
        return

    project_key = args[0].lower()
    task_text = " ".join(args[1:])

    filename, error = add_task_to_file(project_key, task_text)
    if error:
        await update.message.reply_text(f"Ошибка: {error}")
        return

    await update.message.reply_text(f"Задача добавлена в {filename}:\n— {task_text}")


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return
    conversation_history.pop(update.effective_user.id, None)
    await update.message.reply_text("История диалога сброшена.")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return
    user_id = update.effective_user.id
    message = update.message.text
    history = conversation_history.get(user_id, [])
    file_context = detect_project_context(message)
    try:
        prompt = build_prompt(history, message, extra_context=file_context)
        reply = await run_claude(prompt)
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})
        conversation_history[user_id] = history[-20:]
        await send_long(update, reply)
    except Exception as e:
        logger.error("chat error: %s", e)
        await update.message.reply_text("Ошибка при запросе к Claude.")


# ─── Авто-брифинг ────────────────────────────────────────────────────────────

async def auto_brief(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = andrei_chat_id or ANDREI_CHAT_ID
    if not chat_id:
        logger.warning("auto_brief: ANDREI_CHAT_ID не задан, пропускаю")
        return
    ctx = read_brief_context()
    try:
        prompt = build_prompt(
            [],
            "Сделай утренний брифинг. Что важно сегодня? Топ-3 задачи по монетизации.",
            extra_context=ctx,
        )
        reply = await run_claude(prompt)
        limit = 4000
        for i in range(0, len(reply), limit):
            chunk = reply[i: i + limit]
            try:
                await context.bot.send_message(chat_id=chat_id, text=chunk, parse_mode="Markdown")
            except Exception:
                await context.bot.send_message(chat_id=chat_id, text=chunk)
    except Exception as e:
        logger.error("auto_brief error: %s", e)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан в .env")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("brief", brief))
    app.add_handler(CommandHandler("tasks", tasks))
    app.add_handler(CommandHandler("add", add_task))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Авто-брифинг в 9:00 MSK каждый день
    app.job_queue.run_daily(
        auto_brief,
        time=time(hour=9, minute=0, tzinfo=MSK),
        name="daily_brief",
    )

    logger.info("Bot started. Allowed user: %d", ALLOWED_USER_ID)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
