# ============================================
# api.rpy — связь с сервером прогресса
# ============================================
# Веб-сборка: JS fetch через модуль emscripten (обычные сетевые библиотеки Python
# в браузере не работают), ответ опрашивается в цикле renpy.pause(0.1, hard=True).
# ПК (для отладки): urllib.

# Адрес API. Пусто = тот же адрес, с которого загружена игра
# (веб-сборка лежит в backend/src/main/resources/static/).
# Если игра на другом домене — сюда нужен полный адрес сервера,
# а домен игры должен быть в CORS_ALLOWED_ORIGINS на бэкенде.
define api_base_url = ""

# Адрес для запуска на ПК, когда api_base_url пустой.
define api_desktop_url = "http://localhost:8080"

# Сколько секунд ждать ответ сервера.
define api_timeout = 15.0

default api_nickname = ""
default api_offline = False


init python:
    import json

    # ВАЖНО: имена JSON-полей сверить с FRONTEND_HANDOFF.md.
    # (ключ на сервере, где хранится, имя переменной, значение по умолчанию)
    API_PROGRESS_FIELDS = [
        ("unlockedChapters", "persistent", "unlocked_chapters", 1),
        ("gameStarted",      "persistent", "game_started",      False),
        ("ending",           "store",      "ending",            ""),
        ("priemScore",       "store",      "priem_score",       0),
        ("priemAttitude",    "store",      "priem_attitude",    0),
        ("therapyScore",     "store",      "therapy_score",     0),
        ("therapyAttitude",  "store",      "therapy_attitude",  0),
        ("pediatricsScore",  "store",      "pediatrics_score",  0),
        ("pediatricsAttitude", "store",    "pediatrics_attitude", 0),
        ("infectionScore",   "store",      "infection_score",   0),
        ("infectionAttitude", "store",     "infection_attitude", 0),
        ("psychScore",       "store",      "psych_score",       0),
        ("psychAttitude",    "store",      "psych_attitude",    0),
    ]

    _api_counter = [0]

    def _api_target(kind):
        return persistent if kind == "persistent" else renpy.store

    def _api_coerce(value, default):
        if value is None:
            return default
        try:
            if isinstance(default, bool):
                return bool(value)
            if isinstance(default, int):
                return int(value)
            return str(value)
        except (TypeError, ValueError):
            return default

    def api_apply_progress(progress):
        # Серверные значения перезаписывают локальные. Если поле не пришло,
        # ставим значение по умолчанию, а не оставляем чужое локальное.
        progress = progress if isinstance(progress, dict) else {}
        for key, kind, name, default in API_PROGRESS_FIELDS:
            setattr(_api_target(kind), name, _api_coerce(progress.get(key), default))

    def api_progress_payload():
        payload = {"nickname": renpy.store.api_nickname}
        for key, kind, name, default in API_PROGRESS_FIELDS:
            payload[key] = getattr(_api_target(kind), name, default)
        return payload

    def _api_url(path):
        base = renpy.store.api_base_url
        if not base and not renpy.emscripten:
            base = renpy.store.api_desktop_url
        return base.rstrip("/") + path

    def _api_fetch_web(method, url, payload):
        import emscripten

        _api_counter[0] += 1
        rid = _api_counter[0]

        js = (
            "window.__smenaApi = window.__smenaApi || {};"
            "(function(id){"
            "var s = window.__smenaApi[id] = {done:false, status:0, text:''};"
            "var o = {method:" + json.dumps(method) + ", headers:{'Content-Type':'application/json'}};"
            "var b = " + json.dumps(payload) + ";"
            "if (b !== null) { o.body = b; }"
            "fetch(" + json.dumps(url) + ", o)"
            ".then(function(r){ s.status = r.status; return r.text(); })"
            ".then(function(t){ s.text = t; s.done = true; })"
            ".catch(function(e){ s.status = 0; s.text = String(e); s.done = true; });"
            "})(" + str(rid) + ");"
        )
        emscripten.run_script(js)

        waited = 0.0
        finished = False
        while waited < renpy.store.api_timeout:
            renpy.pause(0.1, hard=True)
            waited += 0.1
            if emscripten.run_script_int("window.__smenaApi[%d].done ? 1 : 0" % rid) == 1:
                finished = True
                break

        if not finished:
            return 0, "", "Сервер не отвечает"

        raw = emscripten.run_script_string("JSON.stringify(window.__smenaApi[%d])" % rid)
        emscripten.run_script("delete window.__smenaApi[%d];" % rid)
        try:
            result = json.loads(raw)
        except ValueError:
            return 0, "", "Некорректный ответ браузера"
        return int(result.get("status", 0)), result.get("text", ""), ""

    def _api_fetch_desktop(method, url, payload):
        import urllib.request
        import urllib.error

        data = payload.encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data, method=method,headers={"Content-Type": "application/json"})
        try:
            resp = urllib.request.urlopen(req, timeout=renpy.store.api_timeout)
            return resp.getcode(), resp.read().decode("utf-8"), ""
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace"), ""
        except Exception as e:
            return 0, "", "Сервер недоступен"

    def api_request(method, path, body=None):
        # Возвращает {"ok": bool, "status": int, "data": dict, "error": str}.
        # status == 0: до сервера достучаться не удалось.
        url = _api_url(path)
        payload = json.dumps(body) if body is not None else None

        renpy.show_screen("api_busy")
        try:
            if renpy.emscripten:
                status, text, net_error = _api_fetch_web(method, url, payload)
            else:
                status, text, net_error = _api_fetch_desktop(method, url, payload)
        finally:
            renpy.hide_screen("api_busy")

        data = {}
        if text:
            try:
                data = json.loads(text)
            except ValueError:
                data = {}
        if not isinstance(data, dict):
            data = {}

        ok = 200 <= status < 300
        error = ""
        if not ok:
            error = data.get("error") if isinstance(data.get("error"), str) else ""
            if not error:
                error = net_error or ("Сервер недоступен" if status == 0 else "Ошибка сервера (%d)" % status)

        return {"ok": ok, "status": status, "data": data, "error": error}

    def api_login(nickname):
        res = api_request("POST", "/api/login", {"nickname": nickname})
        if res["ok"]:
            d = res["data"]
            res["progress"] = d["progress"] if isinstance(d.get("progress"), dict) else d
            res["nickname"] = d["nickname"] if isinstance(d.get("nickname"), str) and d["nickname"] else nickname
        return res

    def api_put_progress():
        return api_request("PUT", "/api/progress", api_progress_payload())


screen api_busy():
    zorder 200
    frame:
        align (0.5, 0.5)
        padding (40, 25)
        text "Соединение с сервером…" size 32


# ============================================
# ВХОД
# ============================================
# Пустой ник не подменяем общим значением — игрока просим ввести ник заново,
# иначе все такие игроки получили бы один аккаунт.

label api_login_flow:
    scene black
    $ api_offline = False
    $ api_nickname = ""

label api_ask_nickname:
    $ api_input = renpy.input("Введите ваш никнейм:", length=20).strip()
    if api_input == "":
        "Никнейм не может быть пустым."
        jump api_ask_nickname

label api_try_login:
    $ api_res = api_login(api_input)
    if api_res["ok"]:
        $ api_nickname = api_res["nickname"]
        $ api_apply_progress(api_res["progress"])
        return

    $ api_err = api_res["error"]
    if api_res["status"] == 0 or api_res["status"] >= 500:
        "Не удалось связаться с сервером: [api_err!q]"
        menu:
            "Повторить":
                jump api_try_login
            "Играть без сохранения":
                $ api_offline = True
                return
    else:
        # Сервер ответил отказом (например, недопустимый ник) — просим ввести заново.
        "[api_err!q]"
        jump api_ask_nickname


# ============================================
# СОХРАНЕНИЕ ПРОГРЕССА
# ============================================

label api_save:
    if api_offline or api_nickname == "":
        return

label api_save_try:
    $ api_res = api_put_progress()
    if api_res["ok"]:
        return

    $ api_err = api_res["error"]
    "Не удалось сохранить прогресс: [api_err!q]"
    menu:
        "Повторить":
            jump api_save_try
        "Играть без сохранения":
            $ api_offline = True
            return
