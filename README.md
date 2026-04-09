# GradeScan

Telegram-бот для оценки компетенций сотрудников (NEO.HACK 2026).

## 1) Локальный запуск (Python)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Создай `.env` на основе шаблона:

```powershell
copy .env.example .env
```

Заполни в `.env`:

- `TELEGRAM_BOT_API`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

Запуск бота:

```powershell
python main.py
```

## 2) PostgreSQL через Docker (вариант для команды)

Требуется Docker Desktop.

### Запуск БД

```powershell
docker compose up -d
```

Что происходит:

- поднимается контейнер `gradescan-postgres`
- БД доступна на `localhost:5432`
- схема из `sql/schema.sql` применится автоматически при первом запуске чистого тома

### Проверка, что БД работает

```powershell
docker compose ps
docker compose logs -f postgres
```

### Остановить БД

```powershell
docker compose down
```

### Полный сброс БД (осторожно: удаляет данные)

```powershell
docker compose down -v
docker compose up -d
```

## 3) Совместная работа в ветке

### Ты (владелец текущей ветки)

```powershell
git add .
git commit -m "Add DB integration and Docker setup"
git push -u origin feature/postgres-db
```

### Друг (подключается к ветке)

```powershell
git clone https://github.com/Enyx8/GradeScan
cd GradeScan
git fetch origin
git checkout feature/postgres-db
```

Дальше у друга:

1. `docker compose up -d`
2. `copy .env.example .env`
3. вписать токен в `.env`
4. `python -m venv .venv`
5. `.\.venv\Scripts\Activate.ps1`
6. `python -m pip install -r requirements.txt`
7. `python main.py`
