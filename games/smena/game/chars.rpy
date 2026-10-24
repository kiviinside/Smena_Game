# ============================================
# chars.rpy — спрайты персонажей
# ============================================
# Картинки лежат в game/images/ (PNG/WebP с прозрачным фоном), имя файла = имя спрайта:
#   marina, irina, nadezhda, olga, elena — главные герои глав 1–5
#   child, mama, rodstvenic, pac_alec, patient_f, dmitri, sergey — остальные
# Если файла нет, show_char ничего не делает (игра не падает), поэтому спрайты
# (например, irina, elena, patient_f) можно добавлять по одному.
#
# show_char("имя")                — по центру
# show_char("имя", "left")        — слева ("left" / "center" / "right")
# show_char("имя", 0.3)           — любая позиция от 0.0 (край слева) до 1.0 (край справа)
# show_char("имя", 0.3, fade=False) — без своей анимации (чтобы несколько изменений
#                                    сошлись в одну, её даёт следующая строка with dissolve)
# hide_char("имя")                — убрать спрайт
# Для эмоций кладите "marina smile.png" и вызывайте show_char("marina smile").

init python:
    # Все спрайты приводятся к одной высоте, чтобы не вылезали за экран.
    SPRITE_HEIGHT = 940.0

    SPRITE_SPOTS = {"left": 0.15, "center": 0.5, "right": 0.85}

    # Исходная высота известных файлов (если файла в списке нет, размер читается с диска).
    SPRITE_SOURCE_HEIGHT = {
        "child": 999, "dmitri": 1035, "mama": 1022, "marina": 1054, "nadezhda": 999,
        "olga": 1158, "pac_alec": 1121, "rodstvenic": 1000, "sergey": 1063,
    }

    def _sprite_zoom(tag):
        h = SPRITE_SOURCE_HEIGHT.get(tag)
        if h is None:
            for ext in ("png", "webp"):
                try:
                    h = renpy.image_size("images/%s.%s" % (tag, ext))[1]
                    break
                except Exception:
                    h = None
        if not h:
            return 1.0
        return SPRITE_HEIGHT / float(h)

    def show_char(name, pos="center", fade=True):
        if not renpy.has_image(name):
            return
        tag = name.split()[0]
        x = SPRITE_SPOTS.get(pos, 0.5) if isinstance(pos, str) else float(pos)
        renpy.show(name, at_list=[Transform(zoom=_sprite_zoom(tag), xalign=x, yalign=1.0)])
        if fade:
            renpy.with_statement(renpy.store.dissolve)

    def hide_char(name, fade=True):
        tag = name.split()[0]
        if renpy.showing(tag):
            renpy.hide(tag)
            if fade:
                renpy.with_statement(renpy.store.dissolve)
