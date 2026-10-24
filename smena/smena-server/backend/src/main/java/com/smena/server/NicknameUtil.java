package com.smena.server;

import java.text.Normalizer;
import java.util.Locale;
import java.util.regex.Pattern;

/** Проверка и нормализация никнейма. Без зависимостей от Spring. */
public final class NicknameUtil {

    public static final int MIN_LENGTH = 2;
    public static final int MAX_LENGTH = 20; // совпадает с renpy.input(length=20)

    // буквы любых алфавитов, цифры, пробел, _ - .
    private static final Pattern ALLOWED = Pattern.compile("^[\\p{L}\\p{N}_.\\- ]+$");

    private NicknameUtil() {}

    /** Ник для отображения: NFKC, обрезаны края, схлопнуты повторные пробелы. */
    public static String clean(String raw) {
        if (raw == null) {
            return "";
        }
        String s = Normalizer.normalize(raw, Normalizer.Form.NFKC).strip();
        return s.replaceAll(" {2,}", " ");
    }

    /** Ключ для поиска/уникальности: регистр не важен. */
    public static String key(String cleaned) {
        return cleaned.toLowerCase(Locale.ROOT);
    }

    /** @return текст ошибки на русском или null, если ник допустим. */
    public static String validate(String cleaned) {
        if (cleaned.length() < MIN_LENGTH || cleaned.length() > MAX_LENGTH) {
            return "Никнейм должен быть от " + MIN_LENGTH + " до " + MAX_LENGTH + " символов.";
        }
        if (!ALLOWED.matcher(cleaned).matches()) {
            return "Допустимы буквы, цифры, пробел и символы _ - .";
        }
        return null;
    }
}
