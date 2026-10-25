# ============================================
# mechanics.rpy — скрытые параметры, таймер выбора, дневник смены, атмосфера
# ============================================
# Что здесь:
#   1. Скрытые параметры: trust (доверие пациентов), confidence (уверенность),
#      fatigue (усталость), tension (напряжение, главным образом глава 5).
#   2. Таймер на критичных выборах:   $ timed(7)   прямо перед menu:
#      Если время вышло, выбирается ПОСЛЕДНИЙ пункт меню.
#   3. Дневник смены: note(...) записывает итог выбора, экран shift_diary показывает разбор.
#   4. Атмосфера: tension затемняет и «дёргает» картинку (apply_look).
#   5. Флаги story_flags — на них ссылаются наставники в следующих главах.
#
# Параметры живут только в игре (на сервер не отправляются, API не менялся).
# Если глава открыта из меню выбора глав, параметры ставятся в «типичное» значение.

default trust = 50          # доверие пациентов (0..100)
default confidence = 50     # уверенность (0..100)
default fatigue = 0         # усталость (0..100)
default tension = 0         # напряжение (0..100)
default last_done = 0       # номер последней законченной главы в этой сессии
default look_level = 0      # текущий уровень визуального «напряжения»
default story_flags = set() # флаги выборов вида "ch1_triage_queue"
default diary = {}          # {номер главы: [(уровень, что сделали, разбор), ...]}

# Таймер выбора (используется экраном choice в screens.rpy)
default timed_seconds = 0


# --------------------------------------------
# Визуальные эффекты напряжения (слой master: фон и спрайты, диалог не трогаем)
# --------------------------------------------
define tn_low = SaturationMatrix(0.8) * TintMatrix("#dde2ee")
define tn_mid = SaturationMatrix(0.6) * TintMatrix("#c8cfe2")
define tn_high = SaturationMatrix(0.45) * TintMatrix("#b4bcd4")
define tn_high_dark = SaturationMatrix(0.45) * TintMatrix("#b4bcd4") * BrightnessMatrix(-0.45)

transform tension_low:
    matrixcolor tn_low

transform tension_mid:
    matrixcolor tn_mid

transform tension_high:
    matrixcolor tn_high
    block:
        pause 3.2
        matrixcolor tn_high_dark
        pause 0.06
        matrixcolor tn_high
        pause 0.12
        matrixcolor tn_high_dark
        pause 0.05
        matrixcolor tn_high
        pause 4.5
        repeat


# Размытие фона, пока на экране варианты ответа (включается экраном choice).
transform choice_blur_in:
    blur 0.0
    easein 0.25 blur 9.0


init python:

    def clamp100(v):
        return max(0, min(100, v))

    def stats(trust=0, confidence=0, fatigue=0, tension=0):
        # Изменить скрытые параметры на указанные величины.
        st = renpy.store
        st.trust = clamp100(st.trust + trust)
        st.confidence = clamp100(st.confidence + confidence)
        st.fatigue = clamp100(st.fatigue + fatigue)
        st.tension = clamp100(st.tension + tension)

    def timed(sec, floor=4):
        # Включить таймер на ближайшее menu. Чем выше усталость, тем меньше времени.
        renpy.store.timed_seconds = max(floor, sec - renpy.store.fatigue // 20)

    def apply_look():
        # Подобрать картинку под текущее напряжение.
        st = renpy.store
        t = st.tension
        if t >= 60:
            level = 3
        elif t >= 40:
            level = 2
        elif t >= 20:
            level = 1
        else:
            level = 0
        if level == st.look_level:
            return
        st.look_level = level
        if level == 3:
            renpy.show_layer_at(st.tension_high, layer="master")
        elif level == 2:
            renpy.show_layer_at(st.tension_mid, layer="master")
        elif level == 1:
            renpy.show_layer_at(st.tension_low, layer="master")
        else:
            renpy.show_layer_at([], layer="master")

    def reset_look():
        renpy.store.look_level = 0
        renpy.show_layer_at([], layer="master")

    def _look_list():
        # Эффекты напряжения, подходящие текущему уровню (без размытия).
        st = renpy.store
        if st.look_level == 3:
            return [st.tension_high]
        if st.look_level == 2:
            return [st.tension_mid]
        if st.look_level == 1:
            return [st.tension_low]
        return []

    def choice_blur_on():
        # Размываем фон и спрайты (слой master); окно диалога и варианты остаются чёткими.
        renpy.show_layer_at(_look_list() + [renpy.store.choice_blur_in], layer="master")

    def choice_blur_off():
        # Возвращаем картинку как была (с учётом напряжения).
        renpy.show_layer_at(_look_list(), layer="master")

    def note(ch, level, what, why="", trust=0, confidence=0, fatigue=0, tension=0, flag=None):
        # Запись в дневник смены + изменение параметров + флаг.
        # level: "good" (верно), "ok" (можно лучше), "bad" (ошибка).
        st = renpy.store
        st.diary.setdefault(ch, []).append((level, what, why))
        stats(trust, confidence, fatigue, tension)
        if flag:
            st.story_flags.add(flag)
        apply_look()

    def hidden_begin(n):
        # Начало главы n. Если предыдущая глава не пройдена в этой сессии
        # (вход из меню выбора глав), параметры ставятся в типичные значения.
        st = renpy.store
        if st.last_done != n - 1:
            st.trust = 50
            st.confidence = 50
            st.fatigue = 8 * (n - 1)
            st.tension = 0
        prefix = "ch%d_" % n
        for f in list(st.story_flags):
            if f.startswith(prefix):
                st.story_flags.discard(f)
        st.diary[n] = []
        st.timed_seconds = 0
        st.look_level = 0
        renpy.show_layer_at([], layer="master")
        if n == 5:
            st.tension = clamp100(st.fatigue // 4)
            apply_look()

    def shift_grade(ch):
        # Итоговая оценка смены по характеристикам: доверие, уверенность,
        # «обратная» усталость и (в главе 5) «обратное» напряжение.
        st = renpy.store
        parts = [st.trust, st.confidence, 100 - st.fatigue]
        if ch == 5:
            parts.append(100 - st.tension)
        score = int(round(sum(parts) / float(len(parts))))
        if score >= 65:
            return (score, "ЗАЧТЕНО", "#2e7d4f")
        elif score >= 45:
            return (score, "ЗАЧТЕНО С ЗАМЕЧАНИЯМИ", "#b26a00")
        return (score, "ТРЕБУЕТ ПЕРЕСДАЧИ", "#b3261e")

    def bad_count(n):
        return len([e for e in renpy.store.diary.get(n, []) if e[0] == "bad"])

    def phantom_ready():
        # Игрок настолько вымотан, что видит то, чего нет.
        st = renpy.store
        return st.fatigue + st.tension >= 55 or "ch5_ignored" in st.story_flags


# --------------------------------------------
# Конец главы: усталость растёт, показываем дневник смены
# --------------------------------------------
label chapter_end(n, title):
    $ stats(fatigue=8 + 3 * bad_count(n))
    call screen shift_diary(n, title)
    $ last_done = n
    if n == 5:
        $ reset_look()
    return


# --------------------------------------------
# Экран: дневник смены (бумажный бланк)
# --------------------------------------------
define diary_mentors = {
    1: "Марина Андреевна",
    2: "Ирина Валерьевна",
    3: "Надежда Сергеевна",
    4: "Ольга Николаевна",
    5: "Елена Викторовна",
}

# Шкала из 10 делений, как в бланке (ширина 356)
screen paper_scale(label, value, col):
    vbox:
        spacing 6
        fixed:
            xsize 356
            ysize 34
            text "[label]" size 28 color "#3b3b3b" xalign 0.0
            text "[value]" size 28 color "#3b3b3b" xalign 1.0
        hbox:
            spacing 4
            for i in range(10):
                add Solid(col if i < value // 10 else "#d9d3c3", xsize=32, ysize=20)

# Одна строка таблицы замечаний
screen diary_row(level, what, why):
    if level == "good":
        $ chip = "ВЕРНО"
        $ chip_col = "#2e7d4f"
    elif level == "ok":
        $ chip = "МОЖНО ЛУЧШЕ"
        $ chip_col = "#b88400"
    else:
        $ chip = "ОШИБКА"
        $ chip_col = "#b3261e"

    vbox:
        spacing 10
        xsize 960
        hbox:
            spacing 26
            frame:
                xsize 230
                yminimum 0
                padding (6, 6)
                background Solid(chip_col)
                text "[chip]" xalign 0.5 size 22 bold True color "#ffffff"
            vbox:
                spacing 6
                xsize 700
                text "[what!t]" size 30 color "#1f2933"
                if why:
                    text "Разбор: [why!t]" size 26 color "#2b3f8c" italic True
        add Solid("#cfc8b4", xsize=960, ysize=2)

screen shift_diary(ch, title):
    modal True
    zorder 100
    add Solid("#262b33")

    $ entries = diary.get(ch, [])
    $ nick = api_nickname if api_nickname else "—"
    $ mentor = diary_mentors.get(ch, "—")
    $ score, verdict, vcol = shift_grade(ch)

    fixed:
        xalign 0.5
        yalign 0.5
        xysize (1560, 980)

        # тень листа
        add Solid("#00000066", xsize=1560, ysize=980) pos (14, 14)
        # сам лист
        add Solid("#f3efe4", xsize=1546, ysize=966)

        # шапка бланка
        text "ГОРОДСКАЯ БОЛЬНИЦА":
            xpos 50
            ypos 28
            size 24
            color "#6b6b6b"
        text "Форма № 3-П":
            xpos 1496
            xanchor 1.0
            ypos 28
            size 24
            color "#6b6b6b"
        add Solid("#8a8573", xsize=1446, ysize=2) pos (50, 66)

        text "ЛИСТ ОЦЕНКИ ПРАКТИКАНТА":
            xpos 50
            ypos 80
            size 52
            bold True
            color "#1f2933"

        # поля бланка
        hbox:
            xpos 50
            ypos 156
            spacing 60
            text "Отделение: [title]" size 30 color "#1f2933"
            text "День ротации: [ch] из 5" size 30 color "#1f2933"
        hbox:
            xpos 50
            ypos 200
            spacing 60
            text "Практикант: [nick]" size 30 color "#1f2933"
            text "Наставник: [mentor]" size 30 color "#1f2933"
        add Solid("#8a8573", xsize=1446, ysize=2) pos (50, 252)

        # левая часть: замечания (колесо мыши прокручивает, если записей много)
        text "ЗАМЕЧАНИЯ ПО СМЕНЕ" xpos 50 ypos 268 size 24 color "#6b6b6b"
        viewport:
            xpos 50
            ypos 308
            xsize 980
            ysize 520
            mousewheel True
            draggable True

            vbox:
                spacing 16
                xsize 960

                if not entries:
                    text "Записей за эту смену нет." size 30 color "#6b6b6b"

                for level, what, why in entries:
                    use diary_row(level, what, why)

        # тонкая чёрная разделительная линия, 2 px
        add Solid("#000000", xsize=2, ysize=560) pos (1050, 270)

        # правая часть: показатели
        text "ПОКАЗАТЕЛИ" xpos 1090 ypos 268 size 24 color "#6b6b6b"
        vbox:
            xpos 1090
            ypos 312
            spacing 22
            use paper_scale("Доверие пациентов", trust, "#2e7d4f")
            use paper_scale("Уверенность", confidence, "#2b5fb3")
            use paper_scale("Усталость", fatigue, "#d98a1c")
            if ch == 5:
                use paper_scale("Напряжение", tension, "#b3261e")

        # подпись и кнопка
        add Solid("#8a8573", xsize=1446, ysize=2) pos (50, 856)
        text "Подпись наставника:" xpos 50 ypos 884 size 26 color "#6b6b6b"
        text "[mentor]" xpos 400 ypos 878 size 34 italic True color "#2b3f8c"

        textbutton "Далее":
            xpos 1496
            xanchor 1.0
            ypos 874
            text_size 40
            text_color "#555555"
            text_hover_color "#000000"
            action Return()

        # штамп по итоговой оценке характеристик; положение задаётся самим
        # трансформом (центр штампа), чтобы поворот не сдвигал его
        fixed:
            at Transform(rotate=-6, alpha=0.9, xcenter=1293, ycenter=745)
            xysize (400, 150)
            add Solid(vcol, xsize=400, ysize=5)
            add Solid(vcol, xsize=400, ysize=5) ypos 145
            add Solid(vcol, xsize=5, ysize=150)
            add Solid(vcol, xsize=5, ysize=150) xpos 395
            vbox:
                align (0.5, 0.5)
                spacing 6
                text "[verdict]":
                    xalign 0.5
                    xsize 350
                    text_align 0.5
                    size 32
                    bold True
                    color vcol
                text "Итог: [score] из 100":
                    xalign 0.5
                    size 26
                    color vcol


# --------------------------------------------
# Итоги мини-игр -> запись в дневник смены
# --------------------------------------------
# MG_NOTES[(глава, "вид")][уровень итога] =
#   (оценка, что сделали, разбор, доверие, уверенность, усталость, напряжение, флаг)
# Вызов из script.rpy:  $ mg_note(1, "triage", triage_tier())

init python:
    MG_NOTES = {
        (1, "triage"): {
            "good": ("good", "Расставили четверых пациентов по зонам без ошибок", "Красный: боль в груди. Жёлтый: боль в животе. Зелёный: остальные.", 4, 6, 0, 0, "ch1_triage_ok"),
            "ok":   ("ok", "Самого тяжёлого определили верно, один пациент оказался не в той зоне", "Сверяйте жалобы и пульс вместе: цифры дополняют картину.", 2, 2, 1, 0, "ch1_triage_ok"),
            "weak": ("ok", "Самого тяжёлого заметили, но остальных расставили неверно", "Приоритет по тяжести нужен для каждого пациента, а не только для красной зоны.", 0, -2, 2, 0, None),
            "bad":  ("bad", "Пациент с болью в груди не попал в красную зону", "Боль в груди, бледность и холодный пот: признаки неотложного состояния.", -6, -6, 3, 0, "ch1_triage_missed"),
        },
        (1, "relative"): {
            "good":  ("good", "Успокоили родственника, не повышая голоса", "Сочувствие и конкретика снижают напряжение лучше, чем ссылки на правила.", 5, 4, 0, 0, "ch1_calm_ok"),
            "mid":   ("ok", "Родственник стал тише, но остался недоволен", "Говорите увереннее и называйте конкретные сроки.", 1, 0, 1, 0, None),
            "bad":   ("bad", "Конфликт с родственником погасить не удалось", "Отвечать агрессией на агрессию нельзя.", -4, -3, 2, 0, None),
            "broke": ("bad", "Родственник сорвался на крик, пришлось звать охрану", "Охрана нужна в крайнем случае. Сначала разговор.", -6, -5, 3, 0, None),
        },
        (4, "ppe_don"): {
            "good": ("good", "Надели СИЗ в правильном порядке", "Костюм, респиратор, очки, перчатки.", 2, 6, 0, 0, None),
            "ok":   ("ok", "Один раз нарушили порядок при надевании СИЗ", "Порядок нужен, чтобы не нарушить герметичность комплекта.", 0, -1, 1, 0, None),
            "bad":  ("bad", "Несколько ошибок при надевании СИЗ", "В боксе такая ошибка означает контакт с инфекцией.", -3, -6, 2, 0, "ch4_ppe_fail"),
        },
        (4, "mother"): {
            "good":  ("good", "Убедили мать пациента не входить в бокс, не повышая голоса", "Объяснение и связь с сыном снимают тревогу.", 6, 4, 0, 0, None),
            "mid":   ("ok", "Мать пациента успокоилась лишь отчасти", "Предложите связь с ребёнком: переговорное устройство, разговор с врачом.", 1, 0, 1, 0, None),
            "bad":   ("bad", "Мать пациента продолжала стучать по стеклу", "Отказ без объяснений усиливает тревогу.", -4, -3, 2, 0, None),
            "broke": ("bad", "Мать пациента сорвалась на крик", "Ситуацию пришлось передавать старшей медсестре.", -6, -5, 3, 0, None),
        },
        (4, "ppe_doff"): {
            "good": ("good", "Сняли СИЗ без единой ошибки", "Снимать нужно в обратном порядке: заражённая сторона остаётся внутри.", 2, 5, 0, 0, None),
            "ok":   ("ok", "При снятии СИЗ допустили одну ошибку", "Вовремя остановиться правильно, но порядок нужно знать наизусть.", 0, -1, 1, 0, None),
            "bad":  ("bad", "Коснулись заражённой стороны при снятии СИЗ", "Снятие самый опасный этап: в реальном отделении вас бы изолировали.", -4, -6, 2, 0, "ch4_ppe_fail"),
        },
        (5, "psych"): {
            "good":  ("good", "Успокоили пациента, не споря с бредом", "Сочувствие и присутствие работают лучше возражений.", 6, 5, 0, -5, None),
            "mid":   ("ok", "Пациент стал тише, но остался напряжённым", "Не соглашайтесь с бредом, но и не спорьте с ним.", 1, 0, 2, 3, None),
            "bad":   ("bad", "Пациент остался настороженным", "Возражения и отстранённость усиливают тревогу.", -4, -3, 2, 8, None),
            "broke": ("bad", "Пациент сорвался, пришлось звать Елену Викторовну", "С бредом не спорят, а сопровождают человека в страхе.", -6, -5, 3, 18, None),
        },
        (5, "breathing"): {
            "good": ("good", "Дыхание в общем ритме помогло пациентке успокоиться", "Ровный ритм дыхания снижает тревогу у обоих.", 6, 5, 0, -5, "ch5_breath_ok"),
            "ok":   ("ok", "Дыхание пациентки выровнялось лишь отчасти", "Держите ритм ровнее и не торопитесь.", 3, 1, 1, 2, None),
            "bad":  ("bad", "Общий ритм дыхания не получился", "Пациентке нужно больше времени и спокойствия.", -2, -3, 2, 8, None),
        },
    }

    def mg_note(ch, kind, tier):
        e = MG_NOTES.get((ch, kind), {}).get(tier)
        if e:
            note(ch, e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7])
