# Сервер — карта и правила

Этот файл читается **первым** в каждой сессии. Он даёт общий контекст сервера: что здесь запущено, где лежат проекты, что можно и нельзя делать.

---

## Старт сессии

Перед любой задачей прочитай слои контекста в этом порядке:

1. `/home/claudeuser/projects/ai-clone/INDEX.md` — **КЛОН**: кто хозяин, как думает, как работать с ним
2. `/home/claudeuser/projects/ai-clone/feedback/` — **ПРАВИЛА**: как вести себя в сессии
3. `CLAUDE.md` этого файла — **СЕРВЕР**: карта проектов и инфраструктуры
4. `projects/<ПРОЕКТ>/CLAUDE.md` — **ПРОЕКТ**: правила конкретного проекта
5. `projects/<ПРОЕКТ>/<суб-репо>/CLAUDE.md` — **МОДУЛЬ**: правила конкретного репозитория

После чтения — одной строкой подтверди готовность. Не начинай задачу, жди следующего сообщения.

---

## Авто-память клона

Если в сессии Андрей научил чему-то новому, поправил ошибку или одобрил неочевидное решение — в конце сессии создай или обнови файл в `projects/ai-clone/feedback/<имя>.md` по формату Rule → Why → How (шаблон: `projects/ai-clone/feedback/CANON.md`). Добавь строку в `projects/ai-clone/feedback/INDEX.md`.

---

## Карта проектов

Все проекты в `/home/claudeuser/projects/`.

### Три реальных проекта

| Проект | Путь | Что внутри |
|---|---|---|
| **AI-SCHOOL** | `projects/AI-SCHOOL/` | Платформа онлайн-курса по AI/Claude. Разработка завершена (5 фаз). DNS настроен, email (Resend) подключён, Telegram-бот подключён. Осталось: настроить Prodamus (оплата). Порт 3003 |
| **CONSULTING** | `projects/CONSULTING/` | Консалтинг / Agortex. 7 репозиториев |
| **REVIVEBASE** | `projects/REVIVEBASE/` | AI-платформа реактивации клиентов. 5 репозиториев |
| **AI-WORKSHOP** | `projects/AI-WORKSHOP/` | Тренинг по AI в Дубае. Андрей — продюсер, Арташес — эксперт |

### CONSULTING — суб-репозитории

| Репо | Путь |
|---|---|
| agortex-business | `projects/CONSULTING/agortex-business/` |
| agortex-site-v2 | `projects/CONSULTING/agortex-site-v2/` |
| agortex-masterclass | `projects/CONSULTING/agortex-masterclass/` |
| agortex-partners | `projects/CONSULTING/agortex-partners/` |
| consulting-site | `projects/CONSULTING/consulting-site/` |
| consulting-aggregator | `projects/CONSULTING/consulting-aggregator/` |
| consulting-plans | `projects/CONSULTING/consulting-plans/` |

### REVIVEBASE — суб-репозитории

| Репо | Путь |
|---|---|
| revivebase | `projects/REVIVEBASE/revivebase/` |
| revivebase-app | `projects/REVIVEBASE/revivebase-app/` |
| revivebase-docs | `projects/REVIVEBASE/revivebase-docs/` |
| revivebase-lab | `projects/REVIVEBASE/revivebase-lab/` |
| reactivate-landing | `projects/REVIVEBASE/reactivate-landing/` |

### Инфраструктура и личные инструменты

| Папка | Путь | Что это |
|---|---|---|
| ai-clone | `projects/ai-clone/` | Личная ОС Андрея — читается первой |
| contractors | `projects/contractors/` | Подрядчики: профили, договоры, брифы по проектам |
| planner | `projects/planner/` | Личный планировщик задач и целей |
| server-scripts | `projects/server-scripts/` | Скрипты сервера: брифинги, мониторинг, webhook |
| sendscreen | `projects/sendscreen/` | Утилита: скриншоты → Telegram |
| claude-bot-backup | `projects/claude-bot-backup/` | Архив конфигурации Telegram-бота |

---

## Инфраструктура

- **Пользователь сервера:** `claudeuser`
- **Рабочая папка:** `/home/claudeuser/`
- **GitHub org:** `brandprc-cloud`
- **SSH-ключ:** `/home/claudeuser/.ssh/github_brandprc`
- **ReviveBase:** systemd `revivebase-app.service`, порт 3002, nginx на 80
- **Telegram-бот:** `@vIbecodebot_bot`, токен в `~/.claude/channels/telegram/.env`
- **Cron:** утренний брифинг 9:00 MSK, вечерний чекин 22:00 MSK

---

## Безопасность — красная линия

**Контекст:** предыдущий сервер Андрея был взломан. Утечка токенов и доступов — критическая угроза.

### Запрещено категорически
- Выводить токены, пароли, ключи API целиком в ответах или логах
- Читать `.env` целиком — только `grep "^VAR_NAME=" .env`
- Коммитить файлы с секретами (`.env`, `credentials.json`, `*.key`, `*.pem`)
- Передавать токены через незащищённые каналы (HTTP, открытый лог, Telegram)
- Логировать содержимое `.env` или credentials в любые файлы
- Показывать токены в bot.log, morning-brief.log или других логах сервера
- Добавлять секреты в git-историю — даже временно

### При работе с доступами
- Новая база данных → пароль только в `.env`, никогда не в коде и не в CLAUDE.md
- Новый API-ключ → сразу в `.env`, проверить что `.gitignore` закрывает этот файл
- Если токен случайно попал в лог или код → немедленно сообщить Андрею и отозвать его
- Nginx, открытые порты, новые сервисы → проверять что не открывают лишний доступ извне

### При подозрении на взлом или утечку
- Немедленно остановиться и сообщить Андрею — не пытаться "тихо исправить"
- Не удалять следы до того как Андрей решит что делать

---

## Правила

### Нельзя без явного разрешения
- Перезапускать systemd-сервисы (`systemctl restart`)
- Удалять файлы и папки без проверки
- Делать `git push --force`
- Коммитить через `git add .` — только поимённо
- Читать `.env` целиком — только `grep "^VAR_NAME=" .env`

### Всегда
- Отвечай на русском языке
- Перед задачей — прочитай CLAUDE.md проекта и суб-репо
- Новую функцию — оформляй планом в `plans/` нужного репо
- В конце сессии — рефлексия и обновление памяти клона

---

## Язык

Всегда отвечать на русском языке.
