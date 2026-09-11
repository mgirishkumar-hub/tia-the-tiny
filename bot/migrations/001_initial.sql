CREATE TABLE guild_settings (
    guild_id BIGINT PRIMARY KEY CHECK (guild_id > 0),
    prefix VARCHAR(5) NOT NULL CHECK (char_length(prefix) BETWEEN 1 AND 5)
);
