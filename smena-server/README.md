# smena-server: бэкенд прогресса + мост Ren'Py ↔ сервер

## Что внутри
- `backend/` - Spring Boot 3.5 (Java 17, Maven), PostgreSQL через Flyway, Dockerfile, docker-compose.
- `FRONTEND_HANDOFF.md` - контракт API и список правок для того, кто делает фронтенд.

## 1. База данных
Вариант А (pgAdmin, свой PostgreSQL): в Query Tool под суперпользователем выполните
`backend/db/01-create-database.sql` (создаёт роль и БД `smena`; смените пароль).
Таблицы вручную не создавайте - их создаст Flyway при первом старте бэкенда.

Вариант Б (всё в Docker): `docker compose up --build` в папке `backend/` поднимет PostgreSQL
(для pgAdmin: localhost:5433, БД/пользователь `smena`) и приложение.

## 2. Запуск локально
- Docker: `cd backend && docker compose up --build` -> http://localhost:8080
- Без Docker (со своим PostgreSQL): `cd backend && mvn spring-boot:run`
  Настройки через переменные: `DB_URL` (jdbc:postgresql://localhost:5432/smena), `DB_USER`, `DB_PASSWORD`, `PORT`.

## 3. Игра в браузере
Веб-сборку Ren'Py (делает фронтенд-разработчик) положите в `backend/src/main/resources/static/`:
тогда игра и API работают с одного адреса. Если игра на другом домене - задайте `CORS_ALLOWED_ORIGINS`.

## API
- `POST /api/login` `{"nickname":"Анна"}` -> `{nickname, isNew, progress}` (создаёт игрока, если нет)
- `PUT /api/progress` `{"nickname":"Анна","progress":{gameStarted,unlockedChapters,ending,state}}` -> `{"ok":true}`
- Ошибки: `{"error":"текст"}` (400 - ник/данные, 404 - нет игрока).
Ник: 2-20 символов, буквы/цифры/пробел/`_-.`; регистр не важен ("Анна" = "АННА").

## Важно
Аккаунт = только ник, без пароля: любой, кто знает ник, может открыть и перезаписать его прогресс.
Для визуальной новеллы это обычно приемлемо, но не храните за ником ничего личного.
