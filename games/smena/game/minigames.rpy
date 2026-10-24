# ============================================
# minigames.rpy — мини-игры к главам 1, 4 и 5
# ============================================
#   play_triage            — сортировка пациентов в приёмном (глава 1)
#   play_ppe("don"/"doff") — надевание и снятие СИЗ (глава 4)
#   play_breathing         — дыхание в ритм (глава 5)
#   play_deescalate(ключ)  — шкала деэскалации: "relative" (гл. 1), "mother" (гл. 4), "psych" (гл. 5)
#
# Итоги мини-игр лежат в переменных mg_*, br_*, ppe_*, deesc_* (см. вызовы в script.rpy).
#
# ОФОРМЛЕНИЕ. Всё сделано в стиле самой игры: размытая фотография отделения под белой
# вуалью (как окно диалога), белые панели с тёмно-синей рамкой #003366, бумажные бланки
# цвета #f3efe4 (как «Лист оценки практиканта»), цвета статусов те же, что в дневнике смены.
# Картинки панелей лежат в game/gui/mg/ (можно заменить своими, размер не важен —
# они растягиваются как Frame). Кольцо и ядра дыхания: images/br_*.png.

define mg_navy = "#003366"
define mg_grey = "#707070"
define mg_ink = "#1f2933"
define mg_green = "#2e7d4f"
define mg_amber = "#b26a00"
define mg_red = "#b3261e"
define mg_blue = "#2b5fb3"
define mg_track = "#c9d3de"

default mg_correct = 0
default mg_red_ok = False
default mg_pts = 0


# --------------------------------------------
# Общие стили и куски экранов
# --------------------------------------------

style mg_button is button:
    background Frame("gui/mg/panel.png", 6, 6)
    hover_background Frame("gui/mg/panel_navy.png", 6, 6)
    insensitive_background Frame("gui/mg/panel_ok.png", 6, 6)
    padding (40, 14, 40, 14)

style mg_button_text is button_text:
    size 36
    color mg_navy
    hover_color "#ffffff"
    insensitive_color mg_green

# Фон: фото отделения, поверх — светлая вуаль, как у окна диалога.
screen mg_backdrop(bg="priem"):
    add bg
    add Solid("#ffffffc7")

# Заголовок мини-игры в белой панели с синей рамкой.
screen mg_header(title, hint=""):
    frame:
        background Frame("gui/mg/panel.png", 6, 6)
        xalign 0.5
        ypos 24
        xsize 1500
        padding (30, 14, 30, 16)
        vbox:
            spacing 6
            text title size 44 bold True color mg_navy xalign 0.5
            if hint:
                text hint size 27 color mg_grey xalign 0.5 text_align 0.5

# Шкала: value от 0 до 1, w/h — размеры, fill — цвет заливки, yo — сдвиг по вертикали.
screen mg_meter(value, w=700, h=18, fill="#003366", yo=0):
    fixed:
        xysize (w, h)
        yoffset yo
        add Solid(mg_track, xsize=w, ysize=h)
        add Solid(fill, xsize=max(1, int(w * max(0.0, min(1.0, value)))), ysize=h)


# ============================================
# 1. СОРТИРОВКА В ПРИЁМНОМ
# ============================================

default triage_time = 25.0
default triage_assign = {}

init python:
    TRIAGE_TIME = 25.0

    # (id, заголовок, жалобы, пульс, правильная зона)
    TRIAGE_CARDS = [
        ("chest", "Мужчина, 68 лет", "Боль в груди, бледность, холодный пот", "Пульс 118", "red"),
        ("leg",   "Парень, 24 года",  "Перебинтованная нога, боль слабая",   "Пульс 82",  "green"),
        ("cold",  "Женщина, 45 лет",  "Насморк, температура 37,2",           "Пульс 76",  "green"),
        ("belly", "Девушка, 19 лет",  "Сильная боль в животе, рвота",        "Пульс 104", "yellow"),
    ]

    # (id, заголовок зоны, x, картинка лотка, цвет заголовка)
    TRIAGE_ZONES = [
        ("red",    "КРАСНЫЙ — сразу",    60,   "gui/mg/tray_red.png",    "#b3261e"),
        ("yellow", "ЖЁЛТЫЙ — скоро",     680,  "gui/mg/tray_yellow.png", "#b26a00"),
        ("green",  "ЗЕЛЁНЫЙ — подождёт", 1300, "gui/mg/tray_green.png",  "#2e7d4f"),
    ]

    TRIAGE_ZONE_NAMES = {"red": "красный", "yellow": "жёлтый", "green": "зелёный"}

    def triage_tick():
        s = renpy.store
        s.triage_time = max(0.0, s.triage_time - 0.1)
        if s.triage_time <= 0:
            return "time"

    def triage_dragged(drags, drop):
        d = drags[0]
        cid = d.drag_name
        a = renpy.store.triage_assign
        if drop is None:
            a.pop(cid, None)
        else:
            a[cid] = drop.drag_name
            n = sum(1 for k, v in a.items() if v == drop.drag_name and k != cid)
            d.snap(drop.x + 60, drop.y + 70 + n * 150, 0.15)
        renpy.restart_interaction()

    def triage_evaluate():
        s = renpy.store
        correct = 0
        red_ok = False
        for cid, _t, _s, _p, zone in TRIAGE_CARDS:
            ok = (s.triage_assign.get(cid) == zone)
            if ok:
                correct += 1
            if zone == "red":
                red_ok = ok
        s.mg_correct = correct
        s.mg_red_ok = red_ok

    def triage_tier():
        s = renpy.store
        if s.mg_red_ok and s.mg_correct >= 4:
            return "good"
        if s.mg_red_ok and s.mg_correct == 3:
            return "ok"
        if s.mg_red_ok:
            return "weak"
        return "bad"


screen triage_game():
    modal True
    zorder 60
    style_prefix "mg"

    use mg_backdrop("priem")
    use mg_header("Сортировка в приёмном", "Перетащите карточки в зоны: красный — сразу, жёлтый — скоро, зелёный — подождёт.")

    timer 0.1 repeat True action Function(triage_tick)

    hbox:
        xalign 0.5
        ypos 168
        spacing 28
        text "Время" size 28 color mg_navy yoffset 2
        use mg_meter(triage_time / TRIAGE_TIME, 700, 18, (mg_navy if triage_time > 8 else mg_red), 10)
        text "Распределено: {} из {}".format(len(triage_assign), len(TRIAGE_CARDS)) size 28 color mg_navy yoffset 2

    if len(triage_assign) == len(TRIAGE_CARDS):
        textbutton "Готово":
            xpos 1900
            xanchor 1.0
            ypos 1066
            yanchor 1.0
            padding (40, 8, 40, 8)
            text_size 32
            action Return("done")

    draggroup:
        for z in TRIAGE_ZONES:
            drag:
                drag_name z[0]
                draggable False
                droppable True
                xpos z[2]
                ypos 470
                frame:
                    xysize (560, 500)
                    background Frame(z[3], 6, 6)
                    text z[1] size 32 bold True color z[4] xalign 0.5 ypos 14

        for i, c in enumerate(TRIAGE_CARDS):
            drag:
                drag_name c[0]
                droppable False
                drag_raise True
                dragged triage_dragged
                xpos (50 + i * 465)
                ypos 225
                frame:
                    xysize (440, 170)
                    background Frame("gui/mg/paper.png", 6, 6)
                    padding (18, 12)
                    vbox:
                        spacing 4
                        text c[1] size 28 bold True color mg_navy
                        text c[2] size 23 color mg_ink xsize 404
                        text c[3] size 26 bold True color mg_red


screen triage_summary():
    modal True
    zorder 60
    style_prefix "mg"

    use mg_backdrop("priem")

    frame:
        background Frame("gui/mg/paper.png", 6, 6)
        xalign 0.5
        yalign 0.5
        xsize 1180
        padding (60, 40, 60, 40)

        vbox:
            spacing 22
            text "ИТОГ СОРТИРОВКИ" size 44 bold True color mg_ink xalign 0.0
            add Solid("#8a8573", xsize=1060, ysize=2)

            for c in TRIAGE_CARDS:
                $ got = triage_assign.get(c[0])
                $ ok = (got == c[4])
                use diary_row("good" if ok else "bad", "{}: нужен {}, у вас — {}".format(c[1], TRIAGE_ZONE_NAMES[c[4]], TRIAGE_ZONE_NAMES.get(got, "не успели")), "")

            textbutton "Продолжить":
                xalign 1.0
                text_size 34
                action Return("ok")


label play_triage:
    $ renpy.block_rollback()
    $ triage_time = TRIAGE_TIME
    $ triage_assign = {}
    call screen triage_game
    $ triage_evaluate()
    call screen triage_summary
    return


# ============================================
# 2. СИЗ: НАДЕТЬ И СНЯТЬ
# ============================================

default ppe_mode = "don"
default ppe_order = []
default ppe_tray = []
default ppe_done = []
default ppe_errors = 0
default ppe_msg = ""
default ppe_infected = False

init python:
    # Порядок надевания. Снятие идёт в обратном порядке.
    PPE_DON = ["Защитный костюм", "Респиратор", "Защитные очки", "Перчатки"]

    def ppe_setup(mode):
        s = renpy.store
        s.ppe_mode = mode
        s.ppe_order = list(PPE_DON) if mode == "don" else list(reversed(PPE_DON))
        tray = list(PPE_DON)
        renpy.random.shuffle(tray)
        s.ppe_tray = tray
        s.ppe_done = []
        s.ppe_errors = 0
        s.ppe_msg = ""

    def ppe_pick(name):
        s = renpy.store
        if name in s.ppe_done:
            return
        step = len(s.ppe_done)
        if name == s.ppe_order[step]:
            s.ppe_done.append(name)
            s.ppe_msg = ""
            if len(s.ppe_done) == len(s.ppe_order):
                return "done"
        else:
            s.ppe_errors += 1
            s.ppe_msg = "Нарушен порядок! Контакт с заражённой поверхностью."

    def ppe_tier():
        e = renpy.store.ppe_errors
        return "good" if e == 0 else ("ok" if e == 1 else "bad")


screen ppe_game():
    modal True
    zorder 60
    style_prefix "mg"

    use mg_backdrop("infection")

    if ppe_mode == "don":
        use mg_header("Надевание СИЗ", "Выбирайте элементы комплекта в правильном порядке.")
    else:
        use mg_header("Снятие СИЗ", "Снимите комплект правильно. Любая ошибка — контакт с заражённой стороной.")

    hbox:
        xalign 0.5
        ypos 230
        spacing 120

        # левая колонка — комплект
        vbox:
            spacing 20
            text "Комплект" size 36 bold True color mg_navy
            for name in ppe_tray:
                if name in ppe_done:
                    textbutton ("✓  " + name):
                        sensitive False
                        xminimum 520
                        action NullAction()
                else:
                    textbutton name:
                        xminimum 520
                        action Function(ppe_pick, name)

        # правая колонка — бланк с порядком действий
        frame:
            background Frame("gui/mg/paper.png", 6, 6)
            xsize 640
            padding (40, 28, 40, 34)
            vbox:
                spacing 18
                text ("ПОРЯДОК НАДЕВАНИЯ" if ppe_mode == "don" else "ПОРЯДОК СНЯТИЯ") size 30 bold True color mg_ink
                add Solid("#8a8573", xsize=560, ysize=2)
                for i in range(len(ppe_order)):
                    if i < len(ppe_done):
                        text "{}.  {}".format(i + 1, ppe_done[i]) size 36 color mg_green
                    else:
                        text "{}.  ______________".format(i + 1) size 36 color "#9a9484"

    if ppe_msg:
        frame:
            background Frame("gui/mg/panel_err.png", 6, 6)
            xalign 0.5
            ypos 780
            padding (36, 14, 36, 14)
            text "[ppe_msg]" size 34 color mg_red

    frame:
        background Frame("gui/mg/panel.png", 6, 6)
        xalign 0.5
        ypos 900
        padding (34, 10, 34, 12)
        text "Нарушений: [ppe_errors]" size 32 color (mg_navy if ppe_errors == 0 else mg_red)


label play_ppe(mode):
    $ renpy.block_rollback()
    $ ppe_setup(mode)
    call screen ppe_game
    return


# ============================================
# 3. ДЫХАНИЕ В РИТМ
# ============================================
# Кольцо сужается к кругу. В момент, когда оно совпало с кругом, нажмите
# (клик, пробел или касание). Вдох и выдох чередуются. После промахов
# ритм начинает «плыть» — это и есть растущее напряжение пациентки.

default br_t = 0.0
default br_t0 = 0.0
default br_i = 0
default br_start = 0.0
default br_end = 2.2
default br_hits = 0
default br_early = 0
default br_tension = 0.0
default br_zoom = 1.0
default br_label = "Вдох"
default br_fb = ""
default br_fb_color = "#003366"
default br_last_click = -10.0
default br_score = 0

init python:
    import time

    BR_BEATS = 8        # сколько вдохов и выдохов нужно поймать
    BR_WINDOW = 0.3     # допуск по времени (сек) вокруг идеального момента
    BR_BASE = 2.2       # длительность одного вдоха/выдоха (сек)

    def br_period():
        j = renpy.store.br_tension * 0.3
        return BR_BASE + renpy.random.uniform(-j, j)

    def br_setup():
        s = renpy.store
        s.br_i = 0
        s.br_hits = 0
        s.br_early = 0
        s.br_tension = 0.0
        s.br_t0 = time.time()
        s.br_t = 0.0
        s.br_start = 0.0
        s.br_end = BR_BASE
        s.br_zoom = 1.0
        s.br_label = "Вдох"
        s.br_fb = ""
        s.br_fb_color = "#003366"
        s.br_last_click = -10.0
        s.br_score = 0

    def br_register(hit, quality=""):
        s = renpy.store
        if hit:
            s.br_hits += 1
            s.br_fb = quality or "Ровно"
            s.br_fb_color = "#2e7d4f"
            s.br_tension = max(0.0, s.br_tension - 0.5)
        else:
            s.br_fb = "Ритм сбился"
            s.br_fb_color = "#b3261e"
            s.br_tension = min(3.0, s.br_tension + 1.0)
        s.br_i += 1
        if s.br_i >= BR_BEATS:
            s.br_score = max(0, s.br_hits - s.br_early)
            return "done"
        s.br_start = s.br_end
        s.br_end = s.br_end + br_period()
        s.br_label = "Вдох" if s.br_i % 2 == 0 else "Выдох"
        return None

    def br_tick():
        s = renpy.store
        s.br_t = time.time() - s.br_t0
        dur = max(0.1, s.br_end - s.br_start)
        p = max(0.0, (s.br_t - s.br_start) / dur)
        s.br_zoom = max(0.3, 1.0 - 0.5 * p)
        if s.br_t > s.br_end + BR_WINDOW:
            return br_register(False)

    def br_click():
        s = renpy.store
        if s.br_t - s.br_last_click < 0.3:
            return None
        s.br_last_click = s.br_t
        d = s.br_t - s.br_end
        if abs(d) <= BR_WINDOW:
            if abs(d) <= 0.12:
                q = "Ровно"
            elif d < 0:
                q = "Чуть рано"
            else:
                q = "Чуть поздно"
            return br_register(True, q)
        if d < 0:
            # нажали раньше времени — штраф за суетливость
            s.br_early += 1
            s.br_tension = min(3.0, s.br_tension + 0.5)
            s.br_fb = "Рано"
            s.br_fb_color = "#b26a00"
        return None

    def br_tier():
        sc = renpy.store.br_score
        return "good" if sc >= 6 else ("ok" if sc >= 4 else "bad")


screen breathing_game():
    modal True
    zorder 60
    style_prefix "mg"

    use mg_backdrop("psych")
    use mg_header("Дышите вместе с пациенткой", "Нажмите (клик, пробел или касание), когда кольцо совпадёт с кругом.")

    timer 0.03 repeat True action Function(br_tick)

    button:
        xysize (config.screen_width, config.screen_height)
        background None
        hover_background None
        action Function(br_click)
    key "K_SPACE" action Function(br_click)

    text "[br_label]" size 80 bold True xalign 0.5 ypos 190 color (mg_blue if br_label == "Вдох" else mg_green)

    if br_label == "Вдох":
        add "images/br_core_in.png" align (0.5, 0.58)
    else:
        add "images/br_core_out.png" align (0.5, 0.58)
    add "images/br_ring.png" align (0.5, 0.58) zoom br_zoom

    text "[br_fb]" size 44 bold True color br_fb_color xalign 0.5 ypos 925

    frame:
        background Frame("gui/mg/panel.png", 6, 6)
        xpos 60
        ypos 940
        padding (30, 10, 30, 12)
        text "Попаданий: [br_hits] из [BR_BEATS]" size 30 color mg_navy

    frame:
        background Frame("gui/mg/panel.png", 6, 6)
        xalign 0.97
        ypos 940
        padding (30, 10, 30, 12)
        hbox:
            spacing 20
            text "Напряжение" size 30 color mg_navy
            use mg_meter(br_tension / 3.0, 300, 20, mg_red, 10)


label play_breathing:
    $ renpy.block_rollback()
    $ br_setup()
    call screen breathing_game
    return


# ============================================
# 4. ШКАЛА ДЕЭСКАЛАЦИИ
# ============================================
# У собеседника есть шкала напряжения (0–100). Каждая реплика двигает её.
# 0–35 — безопасная зона, 35–70 — накаляется, 70+ — опасно, 100 — срыв.
# Сцены описываются в DEESC: кто говорит, стартовое напряжение и раунды
# (реплика собеседника + варианты ответа: текст, изменение шкалы, реакция).

default deesc_key = ""
default deesc_who = "relative"
default deesc_title = ""
default deesc_tension = 50
default deesc_last = 0
default deesc_round = 0
default deesc_broke = False
default deesc_tier = "mid"
default deesc_items = []
default deesc_line = ""
default deesc_reaction = ""
default deesc_pick = 0

init python:
    DEESC = {
        "relative": {
            "who": "relative",
            "title": "Напряжение родственника",
            "start": 75,
            "rounds": [
                ("Вы вообще понимаете, что отцу плохо?!", [
                    ("Я вижу, что вы волнуетесь. Давайте я уточню, что с вашим отцом.", -20, "Мужчина шумно выдыхает и называет цифры давления."),
                    ("Пациентов принимают по очереди. Ждите.", 15, "«По очереди?! Да вы...»"),
                    ("Не кричите, здесь люди.", 10, "Он оглядывается, но злость никуда не делась."),
                ]),
                ("Мне просто нужно знать, что происходит!", [
                    ("Сейчас найду его в списке и назову примерное время.", -20, "Он следит за тем, как вы листаете планшет, и немного затихает."),
                    ("Я ничего не решаю.", 20, "Мужчина снова повышает голос."),
                    ("Предложить воды и стул, пока уточняете.", -15, "Он нехотя садится."),
                ]),
                ("Ладно... Но если станет хуже, отвечать будете вы!", [
                    ("Если станет хуже, зовите меня сразу. Я рядом.", -15, "Мужчина кивает."),
                    ("Это не моя ответственность.", 25, "Он смотрит на вас так, будто готов взорваться."),
                    ("Предупредить охрану на всякий случай.", 10, "Охранник подходит ближе, и мужчина мрачнеет."),
                ]),
            ],
        },
        "mother": {
            "who": "mother",
            "title": "Напряжение матери пациента",
            "start": 80,
            "rounds": [
                ("Он там один! Он же мой сын! Откройте дверь!", [
                    ("Я понимаю, вам страшно. Сын под наблюдением, я рядом с ним.", -20, "Женщина всхлипывает и на секунду замолкает."),
                    ("Правила не обсуждаются.", 15, "Она бьёт ладонью по стеклу."),
                    ("Объяснить, чем опасен вход в бокс для неё самой.", -5, "Она слушает, но по лицу видно: слышит только «нельзя»."),
                ]),
                ("Как он? Скажите хоть что-нибудь!", [
                    ("Сказать, что он в сознании, разговаривает и под наблюдением.", -20, "Её плечи опускаются."),
                    ("Информацию даёт только врач.", 15, "Женщина отворачивается и прижимает ладони к лицу."),
                    ("Пообещать, что он обязательно поправится.", 10, "«Вы не можете этого знать!»"),
                ]),
                ("Можно хотя бы поговорить с ним?", [
                    ("Предложить связь через переговорное устройство.", -25, "Она быстро кивает и вытирает глаза."),
                    ("Отказать.", 15, "Женщина снова повышает голос."),
                    ("Позвать лечащего врача, пусть ответит на вопросы.", -15, "Она кивает: «Да, пусть он придёт...»"),
                ]),
            ],
        },
        "psych": {
            "who": "patient",
            "title": "Напряжение пациента",
            "start": 55,
            "rounds": [
                ("Они заменили врачей... Ты тоже один из них, да?", [
                    ("Я ваш медбрат. Можно сесть рядом?", -15, "Он смотрит исподлобья, но не кричит."),
                    ("Никто вас не подменял. Это неправда.", 25, "Он вздрагивает и сжимает кулаки."),
                    ("Промолчать и наблюдать.", 5, "Он продолжает раскачиваться, не сводя с вас глаз."),
                ]),
                ("Они слушают нас через лампы...", [
                    ("Понимаю, что вам страшно. Я побуду здесь.", -20, "Он чуть тише шепчет."),
                    ("Да, лампы действительно слушают.", 15, "Он оживляется: «Значит, ты знаешь!..» — и становится ещё тревожнее."),
                    ("Это бред.", 30, "Он вскакивает с кровати."),
                ]),
                ("Ты правда не уйдёшь?", [
                    ("Я здесь, пока вы не успокоитесь. Давайте помолчим вместе.", -20, "Он медленно опускается обратно."),
                    ("Мне нужно идти, у меня много дел.", 15, "Его лицо искажается."),
                    ("Попросить Елену Викторовну заглянуть.", -5, "Он поглядывает на дверь, но остаётся на месте."),
                ]),
            ],
        },
    }

    def deesc_setup(key):
        s = renpy.store
        sc = DEESC[key]
        s.deesc_key = key
        s.deesc_who = sc["who"]
        s.deesc_title = sc["title"]
        s.deesc_tension = sc["start"]
        s.deesc_last = 0
        s.deesc_round = 0
        s.deesc_broke = False
        s.deesc_tier = "mid"
        s.deesc_reaction = ""

    def deesc_char():
        return getattr(renpy.store, renpy.store.deesc_who)

    def deesc_prepare_round():
        s = renpy.store
        rnd = DEESC[s.deesc_key]["rounds"][s.deesc_round]
        s.deesc_line = rnd[0]
        items = [(opt[0], i) for i, opt in enumerate(rnd[1])]
        renpy.random.shuffle(items)
        s.deesc_items = items

    def deesc_apply(idx):
        s = renpy.store
        opt = DEESC[s.deesc_key]["rounds"][s.deesc_round][1][idx]
        s.deesc_last = opt[1]
        s.deesc_tension = max(0, min(100, s.deesc_tension + opt[1]))
        s.deesc_reaction = opt[2]
        s.deesc_round += 1
        if s.deesc_tension >= 100:
            s.deesc_broke = True

    def deesc_finish():
        s = renpy.store
        t = s.deesc_tension
        if s.deesc_broke:
            s.deesc_tier = "broke"
        elif t <= 35:
            s.deesc_tier = "good"
        elif t <= 65:
            s.deesc_tier = "mid"
        else:
            s.deesc_tier = "bad"

    def deesc_points(max_pts):
        tier = renpy.store.deesc_tier
        if tier == "good":
            return max_pts
        if tier == "mid":
            return max(0, max_pts - 1)
        if tier == "bad":
            return 0
        return -1


# Шкала напряжения собеседника: белая панель с синей рамкой над сценой.
# Зоны окрашены теми же цветами, что и отметки в «Листе оценки практиканта».
screen deesc_bar():
    zorder 55

    $ bw = 820
    $ t = max(0, min(100, deesc_tension))
    $ zone_w = int(bw * 0.35)
    $ zone_col = mg_green if t <= 35 else (mg_amber if t <= 70 else mg_red)
    $ zone_txt = "Безопасная зона" if t <= 35 else ("Накаляется" if t <= 70 else "Опасно")

    frame:
        background Frame("gui/mg/panel.png", 6, 6)
        xalign 0.5
        ypos 24
        padding (36, 16, 36, 18)

        vbox:
            spacing 12

            fixed:
                xysize (bw, 40)
                text "[deesc_title]" size 30 bold True color mg_navy yalign 0.5
                hbox:
                    xalign 1.0
                    yalign 0.5
                    spacing 22
                    if deesc_last < 0:
                        text "[deesc_last]" size 30 bold True color mg_green
                    elif deesc_last > 0:
                        text "+[deesc_last]" size 30 bold True color mg_red
                    text "[zone_txt]" size 30 bold True color zone_col

            fixed:
                xysize (bw, 38)
                add Solid(mg_green, xsize=zone_w - 2, ysize=22) ypos 8
                add Solid(mg_amber, xsize=zone_w - 2, ysize=22) pos (zone_w, 8)
                add Solid(mg_red, xsize=bw - 2 * zone_w, ysize=22) pos (2 * zone_w, 8)
                # ползунок: белая подложка, поверх — синий штрих
                add Solid("#ffffff", xsize=12, ysize=38) xpos (int(bw * t / 100.0) - 6)
                add Solid(mg_navy, xsize=6, ysize=38) xpos (int(bw * t / 100.0) - 3)


label play_deescalate(key):
    $ renpy.block_rollback()
    $ deesc_setup(key)
    show screen deesc_bar

    while deesc_round < len(DEESC[deesc_key]["rounds"]) and not deesc_broke:
        $ deesc_prepare_round()
        $ renpy.say(deesc_char(), deesc_line)
        $ deesc_pick = renpy.display_menu(deesc_items)
        $ deesc_apply(deesc_pick)
        $ renpy.say(None, deesc_reaction)

    $ deesc_finish()
    pause 0.5
    hide screen deesc_bar
    return
