# REVIVEBASE — навигация

Карта проекта. Читай в начале каждой сессии перед работой с любым суб-проектом.

## Что это

**ReviveBase** — AI-платформа для монетизации существующей базы клиентов малого бизнеса: реактивация спящих → повторная покупка → реферальная программа. Целевая аудитория: офлайн-бизнес русскоязычной диаспоры.

Подробности — `revivebase-app/CLAUDE.md`.

## Структура

```
REVIVEBASE/
├── CLAUDE.md                ← этот файл
├── revivebase/              ← основное Next.js приложение (порт 3002)
├── revivebase-app/          ← полная версия: auth, billing, Supabase, Stripe
├── revivebase-docs/         ← документация: idea → vision → mvp → phases
├── revivebase-lab/          ← эксперименты и прототипы
└── reactivate-landing/      ← лендинг продукта (заготовка, продакшн в /var/www/landing/)
```

## Где что искать

| Что | Куда |
|---|---|
| Рабочее приложение | `revivebase-app/` |
| Концепция, аудитория, MVP | `revivebase-docs/` |
| Технические планы | `revivebase-app/plans/` |
| Схема БД | `revivebase-app/schema.sql` |
| Nginx конфиг | `revivebase/server/` |
| Лендинг | `reactivate-landing/` |

## Правила

- Деплой только по явной команде (`systemctl restart revivebase-app.service`, порт 3002)
- Не читать `.env` целиком — только `grep "^VAR=" .env`
- Не деплоить без явного разрешения
- Всегда отвечать на русском

## Язык

Всегда на русском.
