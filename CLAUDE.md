# Сервер — карта и правила

Этот файл читается **первым** в каждой сессии. Он даёт общий контекст сервера: что здесь запущено, где лежат проекты, что можно и нельзя делать.

---

## Старт сессии

Перед любой задачей прочитай слои контекста в этом порядке:

1. `/home/claudeuser/projects/ai-clone/INDEX.md` — **КЛОН**: кто хозяин, как думает, как работать с ним
2. `/home/claudeuser/projects/ai-clone/feedback/` — **ПРАВИЛА**: как вести себя в сессии
3. `CLAUDE.md` этого файла — **СЕРВЕР**: карта проектов и инфраструктуры
4. `projects/<проект>/CLAUDE.md` — **ПРОЕКТ**: правила конкретного репозитория
5. `projects/<проект>/plans/<актуальный план>` — **ЗАДАЧА**: текущая фаза (если есть)

После чтения — одной строкой подтверди готовность. Не начинай задачу, жди следующего сообщения.

---

## Авто-память клона

Если в сессии Андрей научил чему-то новому, поправил ошибку или одобрил неочевидное решение — в конце сессии создай или обнови файл в `projects/ai-clone/feedback/<имя>.md` по формату Rule → Why → How (шаблон: `projects/ai-clone/feedback/CANON.md`). Добавь строку в `projects/ai-clone/feedback/INDEX.md`.

---

## Карта проектов

Все проекты в `/home/claudeuser/projects/`.

### Активные продукты

| Проект | Путь | Описание |
|---|---|---|
| revivebase | `projects/revivebase/` | AI-платформа реактивации клиентов. Next.js, порт 3002 |
| revivebase-app | `projects/revivebase-app/` | Расширенная версия: auth, billing, campaigns. Supabase + Stripe |
| consulting-site | `projects/consulting-site/` | Сайт консалтинга Agortex |
| agortex-site-v2 | `projects/agortex-site-v2/` | Основной сайт Agortex v2 |
| agortex-partners | `projects/agortex-partners/` | Партнёрская программа |
| reactivate-landing | `projects/reactivate-landing/` | Лендинг реактивации |
| AI-SCHOOL | `projects/AI-SCHOOL/` | AI школа |
| agortex-masterclass | `projects/agortex-masterclass/` | Мастер-класс |
| consulting-aggregator | `projects/consulting-aggregator/` | Агрегатор консалтинговых услуг |

### Документация и контекст

| Проект | Путь | Описание |
|---|---|---|
| ai-clone | `projects/ai-clone/` | Личная ОС Андрея — читается первой |
| agortex-business | `projects/agortex-business/` | Бизнес-контекст: продукт, аудитория, экономика |
| consulting-plans | `projects/consulting-plans/` | Планы и история консалтинга |
| revivebase-docs | `projects/revivebase-docs/` | Документация ReviveBase по фазам |
| revivebase-lab | `projects/revivebase-lab/` | Эксперименты и прототипы |
| planner | `projects/planner/` | Личный планировщик задач и целей |

### Инфраструктура и утилиты

| Проект | Путь | Описание |
|---|---|---|
| server-scripts | `projects/server-scripts/` | Скрипты сервера: утренний брифинг, вечерний чекин, мониторинг |
| sendscreen | `projects/sendscreen/` | Отправка скриншотов в Telegram |
| claude-bot-backup | `projects/claude-bot-backup/` | Бэкап конфигурации Telegram-бота |

---

## Инфраструктура

- **Пользователь сервера:** `claudeuser`
- **Рабочая папка:** `/home/claudeuser/`
- **GitHub org:** `brandprc-cloud` — все проекты здесь
- **Nginx:** проксирует проекты на нужные порты
- **ReviveBase:** systemd `revivebase-app.service`, порт 3002
- **Telegram-бот:** `@vIbecodebot_bot`, токен в `~/.claude/channels/telegram/.env`
- **Скрипты cron:** утренний брифинг 9:00 MSK, вечерний чекин 22:00 MSK

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
- Перед сложной задачей — прочитай CLAUDE.md проекта и актуальный план
- Новую функцию — оформляй планом в `plans/` проекта
- В конце сессии — рефлексия и обновление памяти клона

---

## Язык

Всегда отвечай на русском языке. Код и комментарии — на усмотрение проекта.
