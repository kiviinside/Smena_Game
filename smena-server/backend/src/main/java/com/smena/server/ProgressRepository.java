package com.smena.server;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Map;
import java.util.Optional;
import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public class ProgressRepository {

    private static final TypeReference<Map<String, Integer>> STATE_TYPE = new TypeReference<>() {};

    private final JdbcTemplate jdbc;
    private final ObjectMapper mapper;

    public ProgressRepository(JdbcTemplate jdbc, ObjectMapper mapper) {
        this.jdbc = jdbc;
        this.mapper = mapper;
    }

    /** Результат входа: отображаемый ник из БД, признак нового игрока и прогресс. */
    public record LoginResult(String nickname, boolean isNew, Dto.Progress progress) {}

    /** Находит игрока по нику или создаёт нового (вместе с пустым прогрессом). */
    @Transactional
    public LoginResult login(String nickname, String key) {
        int inserted = jdbc.update(
                "INSERT INTO players (nickname, nickname_key) VALUES (?, ?) ON CONFLICT (nickname_key) DO NOTHING",
                nickname, key);

        Map<String, Object> player = jdbc.queryForMap(
                "SELECT id, nickname FROM players WHERE nickname_key = ?", key);
        long id = ((Number) player.get("id")).longValue();

        jdbc.update("UPDATE players SET last_seen_at = now() WHERE id = ?", id);
        jdbc.update("INSERT INTO progress (player_id) VALUES (?) ON CONFLICT (player_id) DO NOTHING", id);

        return new LoginResult((String) player.get("nickname"), inserted == 1, loadProgress(id));
    }

    private Dto.Progress loadProgress(long playerId) {
        return jdbc.queryForObject(
                "SELECT game_started, unlocked_chapters, ending, state::text AS state FROM progress WHERE player_id = ?",
                (rs, i) -> new Dto.Progress(
                        rs.getBoolean("game_started"),
                        rs.getInt("unlocked_chapters"),
                        rs.getString("ending"),
                        parseState(rs.getString("state"))),
                playerId);
    }

    /**
     * Сохраняет прогресс. Число открытых глав и флаг "игра начата" никогда не уменьшаются
     * (как max() в самой игре). Остальное перезаписывается.
     *
     * @return false, если такого игрока нет (нужно сначала войти)
     */
    @Transactional
    public boolean save(String key, Dto.Progress p) {
        Optional<Long> id = findId(key);
        if (id.isEmpty()) {
            return false;
        }
        jdbc.update(
                "UPDATE progress SET "
                        + "game_started = (game_started OR ?), "
                        + "unlocked_chapters = GREATEST(unlocked_chapters, ?), "
                        + "ending = ?, "
                        + "state = ?::jsonb, "
                        + "updated_at = now() "
                        + "WHERE player_id = ?",
                p.gameStarted(), p.unlockedChapters(), p.ending(), toJson(p.state()), id.get());
        jdbc.update("UPDATE players SET last_seen_at = now() WHERE id = ?", id.get());
        return true;
    }

    private Optional<Long> findId(String key) {
        try {
            return Optional.ofNullable(
                    jdbc.queryForObject("SELECT id FROM players WHERE nickname_key = ?", Long.class, key));
        } catch (EmptyResultDataAccessException e) {
            return Optional.empty();
        }
    }

    private String toJson(Map<String, Integer> state) {
        try {
            return mapper.writeValueAsString(state);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException(e);
        }
    }

    private Map<String, Integer> parseState(String json) {
        try {
            return mapper.readValue(json, STATE_TYPE);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("Повреждён JSON состояния в БД", e);
        }
    }
}
