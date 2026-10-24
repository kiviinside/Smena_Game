-- Выполните ОДИН раз в pgAdmin (Query Tool), подключившись к серверу
-- под суперпользователем (обычно postgres) к базе "postgres".
-- Таблицы создавать вручную НЕ нужно: их создаст Flyway при первом запуске
-- бэкенда (src/main/resources/db/migration/V1__init.sql).

CREATE ROLE smena LOGIN PASSWORD 'change_me';   -- смените пароль!

CREATE DATABASE smena
    OWNER smena
    ENCODING 'UTF8';
