# Что нужно изменить во фронтенде (для того, кто делает Ren'Py / index.html)

Бэкенд хранит прогресс по нику. Исходный проект `smena/smena/game` в этом архиве НЕ менялся.

## Адрес API
Если веб-сборка Ren'Py лежит в `backend/src/main/resources/static/`, API доступен по тому же адресу
(`/api/...`), CORS не нужен. Если игра на другом домене - сообщите домен, добавим его в `CORS_ALLOWED_ORIGINS`.

## Контракт
`POST /api/login`, тело `{"nickname":"Анна"}` ->
`{"nickname":"Анна","isNew":true,"progress":{"gameStarted":false,"unlockedChapters":1,"ending":"","state":{}}}`
(создаёт игрока, если его нет; возвращает ник в том виде, как он сохранён).

`PUT /api/progress`, тело
`{"nickname":"Анна","progress":{"gameStarted":true,"unlockedChapters":3,"ending":"","state":{"priem_score":5,"therapy_attitude":2}}}` -> `{"ok":true}`

Ошибки всегда `{"error":"текст"}`: 400 - плохой ник/данные (текст можно показать игроку), 404 - игрока нет (нужен login).

Ограничения: ник 2-20 символов (буквы, цифры, пробел, `_ - .`), регистр не важен; `unlockedChapters` 1..5;
`ending` одно из `""`, `priem`, `therapy`, `pediatrics`, `infection`, `psych`;
`state` - до 50 пар `имя -> целое` (имя `[a-z][a-z0-9_]*`, значение по модулю до 1000).
Сервер никогда не уменьшает `unlockedChapters` и не сбрасывает `gameStarted`.

## Правки в script.rpy
1. `label start`: вместо локального `renpy.input` + подстановки "Медбрат" - вызвать `POST /api/login` в цикле,
   пока ник не будет принят (при 400 показать текст ошибки и спросить ник заново). Пустой ник нельзя заменять на
   общий "Медбрат": все такие игроки получили бы один аккаунт.
2. После успешного входа записать ответ в переменные игры:
   `persistent.unlocked_chapters`, `persistent.game_started`, `ending`, и 10 переменных из `state`:
   `priem_score`, `priem_attitude`, `therapy_score`, `therapy_attitude`, `pediatrics_score`, `pediatrics_attitude`,
   `infection_score`, `infection_attitude`, `psych_score`, `psych_attitude` (отсутствующие ключи = 0).
   Серверные значения должны перезаписывать локальный `persistent`, иначе другой ник в том же браузере унаследует чужой прогресс.
3. Вызывать `PUT /api/progress` (все те же поля) после каждой строки
   `$ persistent.unlocked_chapters = max(...)` (конец глав 1-4), после выбора концовки в главе 5 и после
   `persistent.game_started = True` в `label start`.
4. В `label chapter_intro` (ветка "Продолжить") обнулять `<глава>_score` и `<глава>_attitude` входящей главы:
   иначе при повторном прохождении восстановленные с сервера баллы сложатся с новыми (они влияют на текст концовок глав).
5. Если сервер недоступен - предложить "Повторить" или "Играть без сохранения" (тогда не вызывать PUT).

## Как ходить на сервер из веб-сборки Ren'Py
Python-сеть (`urllib`, `requests`) в браузере не работает. Нужен JS `fetch` через модуль `emscripten`
(`emscripten.run_script`, `run_script_int`, `run_script_string`). Схема: Ren'Py запускает `fetch`
и получает номер запроса, затем в цикле опрашивает результат, вызывая `renpy.pause(0.1, hard=True)`
(иначе браузер не получит управления и ответ не придёт). Таймаут для входа лучше 20+ секунд (холодный старт Java).
Если нужен готовый протестированный `api.rpy` с этим мостом, скажите - отдам отдельным файлом.
