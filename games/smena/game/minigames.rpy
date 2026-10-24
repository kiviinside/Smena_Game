# ============================================
# minigames.rpy — мини-игры к главам 1, 4 и 5
# ============================================
#   play_triage            — сортировка пациентов в приёмном (глава 1)
#   play_ppe("don"/"doff") — надевание и снятие СИЗ (глава 4)
#   play_breathing         — дыхание в ритм (глава 5)
#   play_deescalate(ключ)  — шкала деэскалации: "relative" (гл. 1), "mother" (гл. 4), "psych" (гл. 5)
#
# Итоги мини-игр лежат в переменных mg_*, br_*, ppe_*, deesc_* (см. вызовы в script.rpy).
# Картинки колец для дыхания: images/br_ring.png, br_core_in.png, br_core_out.png.

default mg_correct = 0
default mg_red_ok = False
default mg_pts = 0


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

    # (id, заголовок зоны, x, цвет)
    TRIAGE_ZONES = [
        ("red",    "КРАСНЫЙ — сразу",   60,   "#5b1f1f"),
        ("yellow", "ЖЁЛТЫЙ — скоро",    680,  "#5b4a1a"),
        ("green",  "ЗЕЛЁНЫЙ — подождёт", 1300, "#1f4d2e"),
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


screen triage_game():
    modal True
    zorder 60
    add Solid("#0d1218")

    text "Сортировка в приёмном" size 46 color "#ffffff" xalign 0.5 ypos 20
    text "Перетащите карточки в зоны: красный — сразу, жёлтый — скоро, зелёный — подождёт." size 28 color "#b8c4d0" xalign 0.5 ypos 82

    timer 0.1 repeat True action Function(triage_tick)

    fixed:
        xalign 0.5
        ypos 134
        xysize (900, 18)
        add Solid("#2a2f36")
        add Solid("#e0a030" if triage_time > 8 else "#d9442f", xsize=max(1, int(900 * triage_time / TRIAGE_TIME)), ysize=18)

    text "Распределено: {} из {}".format(len(triage_assign), len(TRIAGE_CARDS)) size 28 color "#ffffff" xpos 60 ypos 150

    if len(triage_assign) == len(TRIAGE_CARDS):
        textbutton "Готово":
            xpos 1600
            ypos 140
            text_size 40
            text_color "#ffffff"
            text_hover_color "#8fd19e"
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
                    xysize (560, 560)
                    background Solid(z[3])
                    text z[1] size 32 bold True color "#ffffff" xalign 0.5 ypos 14

        for i, c in enumerate(TRIAGE_CARDS):
            drag:
                drag_name c[0]
                droppable False
                drag_raise True
                dragged triage_dragged
                xpos (50 + i * 465)
                ypos 200
                frame:
                    xysize (440, 170)
                    background Solid("#e9eef3")
                    padding (16, 10)
                    vbox:
                        spacing 4
                        text c[1] size 28 bold True color "#1b2a3a"
                        text c[2] size 23 color "#222222" xsize 408
                        text c[3] size 26 bold True color "#9b1c1c"


screen triage_summary():
    modal True
    zorder 60
    add Solid("#0d1218")

    vbox:
        xalign 0.5
        ypos 110
        spacing 26

        text "Итог сортировки" size 52 color "#ffffff" xalign 0.5

        for c in TRIAGE_CARDS:
            $ got = triage_assign.get(c[0])
            $ ok = (got == c[4])
            hbox:
                spacing 24
                text ("верно" if ok else "ошибка") size 32 bold True color ("#8fd19e" if ok else "#e57373") min_width 150
                text "{}: нужен {}, у вас — {}".format(c[1], TRIAGE_ZONE_NAMES[c[4]], TRIAGE_ZONE_NAMES.get(got, "не успели")) size 32 color "#ffffff"

    textbutton "Продолжить":
        xalign 0.95
        yalign 0.95
        text_size 40
        text_color "#aaaaaa"
        text_hover_color "#ffffff"
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


screen ppe_game():
    modal True
    zorder 60
    add Solid("#0d1218")

    if ppe_mode == "don":
        text "Надевание СИЗ" size 52 color "#ffffff" xalign 0.5 ypos 40
        text "Выбирайте элементы комплекта в правильном порядке." size 30 color "#b8c4d0" xalign 0.5 ypos 112
    else:
        text "Снятие СИЗ" size 52 color "#ffffff" xalign 0.5 ypos 40
        text "Снимите комплект правильно. Любая ошибка — контакт с заражённой стороной." size 30 color "#b8c4d0" xalign 0.5 ypos 112

    hbox:
        xalign 0.5
        ypos 240
        spacing 180

        vbox:
            spacing 20
            text "Комплект" size 36 color "#ffffff"
            for name in ppe_tray:
                if name in ppe_done:
                    textbutton name:
                        sensitive False
                        xminimum 480
                        padding (30, 14)
                        background Solid("#1f4d2e")
                        text_size 38
                        text_color "#8fd19e"
                        text_insensitive_color "#8fd19e"
                        action NullAction()
                else:
                    textbutton name:
                        xminimum 480
                        padding (30, 14)
                        background Solid("#2d3a4a")
                        hover_background Solid("#3f5873")
                        text_size 38
                        text_color "#ffffff"
                        action Function(ppe_pick, name)

        vbox:
            spacing 20
            text ("Порядок надевания" if ppe_mode == "don" else "Порядок снятия") size 36 color "#ffffff"
            for i in range(len(ppe_order)):
                if i < len(ppe_done):
                    text "{}. {}".format(i + 1, ppe_done[i]) size 38 color "#8fd19e"
                else:
                    text "{}. —".format(i + 1) size 38 color "#5d6b7a"

    text "[ppe_msg]" size 38 color "#e57373" xalign 0.5 ypos 790
    text "Нарушений: [ppe_errors]" size 32 color ("#ffffff" if ppe_errors == 0 else "#e57373") xalign 0.5 ypos 860


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
default br_fb_color = "#ffffff"
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
        s.br_fb_color = "#ffffff"
        s.br_last_click = -10.0
        s.br_score = 0

    def br_register(hit, quality=""):
        s = renpy.store
        if hit:
            s.br_hits += 1
            s.br_fb = quality or "Ровно"
            s.br_fb_color = "#8fd19e"
            s.br_tension = max(0.0, s.br_tension - 0.5)
        else:
            s.br_fb = "Ритм сбился"
            s.br_fb_color = "#e57373"
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
            s.br_fb_color = "#e0a030"
        return None


screen breathing_game():
    modal True
    zorder 60
    add Solid("#0b1620")

    timer 0.03 repeat True action Function(br_tick)

    button:
        xysize (config.screen_width, config.screen_height)
        background None
        action Function(br_click)
    key "K_SPACE" action Function(br_click)

    text "Дышите вместе с пациенткой" size 46 color "#ffffff" xalign 0.5 ypos 40
    text "Нажмите (клик, пробел или касание), когда кольцо совпадёт с кругом." size 28 color "#b8c4d0" xalign 0.5 ypos 104

    text "[br_label]" size 90 bold True xalign 0.5 ypos 170 color ("#6fb7e8" if br_label == "Вдох" else "#8fd19e")

    if br_label == "Вдох":
        add "images/br_core_in.png" align (0.5, 0.58)
    else:
        add "images/br_core_out.png" align (0.5, 0.58)
    add "images/br_ring.png" align (0.5, 0.58) zoom br_zoom

    text "[br_fb]" size 44 color br_fb_color xalign 0.5 ypos 930

    hbox:
        xpos 60
        ypos 960
        spacing 30
        text "Попаданий: [br_hits] из [BR_BEATS]" size 32 color "#ffffff"
    hbox:
        xalign 0.97
        ypos 960
        spacing 20
        text "Напряжение" size 32 color "#ffffff"
        fixed:
            xysize (300, 22)
            yoffset 12
            add Solid("#2a2f36")
            add Solid("#d9442f", xsize=max(1, int(300 * br_tension / 3.0)), ysize=22)


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


screen deesc_bar():
    zorder 55

    $ bw = 760
    $ t = max(0, min(100, deesc_tension))

    vbox:
        xalign 0.5
        ypos 30
        spacing 8

        text "[deesc_title]" size 32 color "#ffffff" xalign 0.5 outlines [(2, "#000000", 0, 0)]

        fixed:
            xysize (bw, 30)
            xalign 0.5
            add Solid("#2e8b57", xsize=int(bw * 0.35), ysize=30)
            add Solid("#d4a017", xsize=int(bw * 0.35), ysize=30) xpos int(bw * 0.35)
            add Solid("#b03a2e", xsize=bw - int(bw * 0.70), ysize=30) xpos int(bw * 0.70)
            add Solid("#ffffff", xsize=6, ysize=46) xpos (int(bw * t / 100.0) - 3) ypos -8

        hbox:
            xalign 0.5
            spacing 20
            if t <= 35:
                text "Безопасная зона" size 28 color "#8fd19e" outlines [(2, "#000000", 0, 0)]
            elif t <= 70:
                text "Накаляется" size 28 color "#f0c040" outlines [(2, "#000000", 0, 0)]
            else:
                text "Опасно" size 28 color "#ff7b6b" outlines [(2, "#000000", 0, 0)]
            if deesc_last < 0:
                text "[deesc_last]" size 28 color "#8fd19e" outlines [(2, "#000000", 0, 0)]
            elif deesc_last > 0:
                text "+[deesc_last]" size 28 color "#ff7b6b" outlines [(2, "#000000", 0, 0)]


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
