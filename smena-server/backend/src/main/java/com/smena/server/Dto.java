package com.smena.server;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.Map;

/** Все DTO API в одном месте. */
public final class Dto {

    private Dto() {}

    public record LoginRequest(@NotNull @Size(max = 100) String nickname) {}

    /** Прогресс игрока. state: переменные вида priem_score -> число. */
    public record Progress(
            boolean gameStarted,
            @Min(1) @Max(5) int unlockedChapters,
            @NotNull @Size(max = 32) String ending,
            @NotNull @Size(max = 50) Map<String, Integer> state) {}

    public record SaveRequest(
            @NotNull @Size(max = 100) String nickname,
            @NotNull @Valid Progress progress) {}

    public record LoginResponse(String nickname, boolean isNew, Progress progress) {}

    public record ErrorResponse(String error) {}

    public record Ok(boolean ok) {}
}
