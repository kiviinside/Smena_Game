-- Игроки: аккаунт = только никнейм (без пароля).
-- nickname_key - нормализованный ник (NFKC + нижний регистр), по нему ищем и он уникален,
-- чтобы "Анна" и "анна" были одним игроком. nickname - как ввёл игрок.
CREATE TABLE players (
    id           BIGSERIAL PRIMARY KEY,
    nickname     VARCHAR(20)  NOT NULL,
    nickname_key VARCHAR(20)  NOT NULL UNIQUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Прогресс: одна строка на игрока.
-- state - баллы и "отношение" по главам (priem_score, therapy_attitude, ...),
-- чтобы добавлять переменные в игру без миграций БД.
CREATE TABLE progress (
    player_id         BIGINT      PRIMARY KEY REFERENCES players(id) ON DELETE CASCADE,
    game_started      BOOLEAN     NOT NULL DEFAULT FALSE,
    unlocked_chapters INTEGER     NOT NULL DEFAULT 1 CHECK (unlocked_chapters BETWEEN 1 AND 5),
    ending            VARCHAR(32) NOT NULL DEFAULT '',
    state             JSONB       NOT NULL DEFAULT '{}'::jsonb,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
