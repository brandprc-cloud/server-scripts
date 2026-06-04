---
name: project-overview
description: "Все 18 проектов Андрея — состояние на 04.06.2026, GitHub org, техническое состояние"
metadata: 
  node_type: memory
  type: project
  originSessionId: fc7fff26-f327-448b-9f42-7e592b2d9c73
---

Все проекты в `/home/claudeuser/projects/`, GitHub org: `brandprc-cloud`.

**Why:** Сервер сменился (старый был `/root/`, новый `/home/claudeuser/`). Проекты восстановлены из GitHub-бэкапов.

**How to apply:** Пути всегда `/home/claudeuser/projects/<name>/`, не `/root/`.

**Состояние на 04.06.2026:**
- Файлы локально = GitHub (побайтовое совпадение, проверено на revivebase и revivebase-app)
- Git init выполнен во всех папках, remote origin прописан с токеном
- HTTPS git-транспорт (`git-remote-https`) не установлен → push/pull через git не работает, только через GitHub API/curl
- SSH-ключ `/home/claudeuser/.ssh/github_brandprc` работает → push через `GIT_SSH_COMMAND` успешен (проверено на planner 04.06.2026)
- Пустые заглушки `brandprc-cloud-<name>-<hash>/` в каждом проекте — артефакт, можно удалить

**Проекты:**
- `revivebase` + `revivebase-app` — AI-платформа реактивации клиентов (Next.js, Supabase)
- `revivebase-lab`, `revivebase-docs` — эксперименты и документация
- `agortex-business`, `agortex-site-v2`, `agortex-masterclass`, `agortex-partners` — Agortex
- `consulting-site`, `consulting-plans`, `consulting-aggregator` — консалтинг
- `AI-SCHOOL`, `ai-clone`, `planner` — личные инструменты. Planner: файловая часть работает, бот (@vIbecodebot_bot) не работает — cron пустой, ~/.claude/channels/telegram/ нет. Настроен post-commit hook → автопуш на GitHub после каждого коммита.
- `reactivate-landing`, `sendscreen`, `claude-bot-backup`, `server-scripts` — утилиты
