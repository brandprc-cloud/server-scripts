# CONSULTING — навигация

Карта проекта. Читай в начале каждой сессии перед работой с любым суб-проектом.

## Что это

**CONSULTING / Agortex** — консалтинговый проект: продажа экспертизы, партнёрская схема, AI-инструменты для бизнеса.

Подробности — `agortex-business/`.

## Структура

```
CONSULTING/
├── CLAUDE.md                  ← этот файл
├── agortex-business/          ← бизнес-контекст: продукт, аудитория, экономика, бренд
├── agortex-site-v2/           ← основной сайт Agortex (Next.js)
├── agortex-masterclass/       ← лендинг мастер-класса (index.html, GitHub Pages)
├── agortex-partners/          ← портал для партнёров (Next.js)
├── consulting-site/           ← сайт консалтинга (Next.js)
├── consulting-aggregator/     ← агрегатор услуг (Next.js)
└── consulting-plans/          ← документация, шаблоны, idea/, architecture/
```

## Где что искать

| Что | Куда |
|---|---|
| Бизнес-контекст, бренд, аудитория | `agortex-business/` |
| Планы, идеи, архитектура | `consulting-plans/` |
| Основной сайт | `agortex-site-v2/` |
| Партнёрский портал | `agortex-partners/` |
| Мастер-класс лендинг | `agortex-masterclass/` |
| Сайт консалтинга | `consulting-site/` |

## Правила

- Бренд и гайдлайны — источник: `agortex-business/brand/`
- Не хардкодить пути к другим проектам — использовать относительные пути внутри CONSULTING/
- Не деплоить без явной команды
- Всегда отвечать на русском

## Язык

Всегда на русском.
