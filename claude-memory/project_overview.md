---
name: project-overview
description: "Все проекты Андрея — состояние на 05.06.2026, GitHub org, техническое состояние"
metadata: 
  node_type: memory
  type: project
  originSessionId: fc7fff26-f327-448b-9f42-7e592b2d9c73
---

Все проекты в `/home/claudeuser/projects/`, GitHub org: `brandprc-cloud`.

**Why:** Сервер сменился (старый был `/root/`, новый `/home/claudeuser/`). Проекты восстановлены из GitHub-бэкапов.

**How to apply:** Пути всегда `/home/claudeuser/projects/<name>/`, не `/root/`.

**Состояние на 05.06.2026:**
- SSH-ключ `/home/claudeuser/.ssh/github_brandprc` работает → push через `GIT_SSH_COMMAND`
- `AI-SCHOOL` — запущен через PM2, embedded-postgres, порт 3003
- Telegram-бот @vIbecodebot_bot — новый токен записан в `.env`, плагин отключён (false), авторизация Claude протухла → бот не работает до переавторизации
- Планер работает: папки задачи/, события/, партнёры/, контакты/

**Новое на 05.06.2026:**
- Добавлен проект AI-WORKSHOP в CLAUDE.md (тренинг по AI в Дубае, Андрей — продюсер, Арташес — эксперт)
- Создана система партнёров в планере: `planner/партнёры/` + `planner/контакты/`
- Вячеслав Крючков (ArtPromo) — подрядчик по лидам, 0 лидов за 130 дней, письмо готово к отправке 06.06 утром
- Анастасия СММ — планерка 08.06 в 13:30, файл подготовки в `партнёры/анастасия/ai-workshop/`
- Правила безопасности добавлены в CLAUDE.md (предыдущий сервер был взломан)
- Новый токен Telegram-бота записан в `.env` (старый отозван в BotFather)
