<p align="center">
  <img src="docs/logo.png" alt="GradeScan" width="420">
</p>

# GradeScan

Проект делали под хакатон **NEO.HACK 2026**. Идея простая: Telegram-бот, через который команда оценивает навыки коллег, а менеджер смотрит сводку по людям. Всё завязано на PostgreSQL (схема и сиды лежат в `sql/`).

Ниже — как поднять у себя и запустить.

---

## Установка и запуск

### 1. Python и зависимости

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Переменные окружения

Скопируй шаблон и заполни значения (минимум токен бота и доступ к БД):

```powershell
copy .env.example .env
```

Нужны как минимум: `TELEGRAM_BOT_API`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

### 3. База (Docker)

Если стоит Docker Desktop:

```powershell
docker compose up -d
```

При первом запуске на пустом томе подтянутся `sql/schema.sql` и `sql/seed_team101.sql` (команда `101` и тестовые коллеги с `telegram_id` вида `91xxxxxxx` — удобно клацать «Оценить коллег»).

Полный сброс данных (осторожно):

```powershell
docker compose down -v
docker compose up -d
```

### 4. Запуск бота

```powershell
python main.py
```

---

## Полезное для команды

Клон и ветка (пример):

```powershell
git clone https://github.com/Enyx8/GradeScan
cd GradeScan
git fetch origin
git checkout <нужная-ветка>
```

Если схема БД уже жила до обновлений — догоняй недостающие куски из `sql/schema.sql` вручную в pgAdmin или через `psql`, потом при необходимости прогони `sql/seed_team101.sql`.

Если в старой версии осталась колонка `matrix_key` у `user`, её можно убрать:

```sql
ALTER TABLE "user" DROP COLUMN IF EXISTS matrix_key;
```

Проверка контейнера Postgres:

```powershell
docker compose ps
docker compose logs -f postgres
```

Остановка:

```powershell
docker compose down
```
