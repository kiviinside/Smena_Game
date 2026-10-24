package com.smena.server;

import jakarta.validation.Valid;
import java.util.Set;
import java.util.regex.Pattern;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api")
public class PlayerController {

    private static final Pattern STATE_KEY = Pattern.compile("^[a-z][a-z0-9_]{0,39}$");
    private static final Set<String> ENDINGS =
            Set.of("", "priem", "therapy", "pediatrics", "infection", "psych");
    private static final int STATE_VALUE_LIMIT = 1000;

    private final ProgressRepository repository;

    public PlayerController(ProgressRepository repository) {
        this.repository = repository;
    }

    /** Вход по нику: создаёт игрока, если его ещё нет, и возвращает сохранённый прогресс. */
    @PostMapping("/login")
    public Dto.LoginResponse login(@Valid @RequestBody Dto.LoginRequest req) {
        String nickname = checkedNickname(req.nickname());
        ProgressRepository.LoginResult r = repository.login(nickname, NicknameUtil.key(nickname));
        return new Dto.LoginResponse(r.nickname(), r.isNew(), r.progress());
    }

    /** Сохранение прогресса игрока. */
    @PutMapping("/progress")
    public Dto.Ok save(@Valid @RequestBody Dto.SaveRequest req) {
        String nickname = checkedNickname(req.nickname());
        validateProgress(req.progress());
        if (!repository.save(NicknameUtil.key(nickname), req.progress())) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Игрок не найден. Сначала выполните вход.");
        }
        return new Dto.Ok(true);
    }

    private String checkedNickname(String raw) {
        String nickname = NicknameUtil.clean(raw);
        String error = NicknameUtil.validate(nickname);
        if (error != null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, error);
        }
        return nickname;
    }

    private void validateProgress(Dto.Progress p) {
        if (!ENDINGS.contains(p.ending())) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Неизвестная концовка.");
        }
        p.state().forEach((k, v) -> {
            if (!STATE_KEY.matcher(k).matches() || v == null || Math.abs(v) > STATE_VALUE_LIMIT) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Недопустимое поле состояния: " + k);
            }
        });
    }
}
