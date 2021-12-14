JOURNAL_MODE = "PRAGMA journal_mode = wal"

CREATE_TABLES = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS Users(
    id INTEGER PRIMARY KEY,
    name TEXT
);
CREATE TABLE IF NOT EXISTS Levels(
    id INTEGER PRIMARY KEY,
    name TEXT
);
CREATE TABLE IF NOT EXISTS Replays(
    level_id INTEGER REFERENCES Levels(id),
    user_id INTEGER REFERENCES Users(id),
    timestamp INTEGER,
    frame_count INTEGER,
    replay TEXT,
    PRIMARY KEY(level_id, user_id, timestamp)
);
CREATE TABLE IF NOT EXISTS PersonalBests(
    level_id INTEGER REFERENCES Levels(id),
    user_id INTEGER REFERENCES Users(id),
    timestamp INTEGER,
    frame_count INTEGER,
    replay TEXT,
    PRIMARY KEY(level_id, user_id)
);
CREATE TRIGGER IF NOT EXISTS update_personal_bests
AFTER INSERT ON Replays
BEGIN
    INSERT INTO PersonalBests
    VALUES (
        NEW.level_id,
        NEW.user_id,
        NEW.timestamp,
        NEW.frame_count,
        NEW.replay
    )
    ON CONFLICT(level_id, user_id) DO UPDATE SET
        timestamp = excluded.timestamp,
        frame_count = excluded.frame_count,
        replay = excluded.replay
    WHERE excluded.timestamp > timestamp;
END;
CREATE INDEX IF NOT EXISTS pb_idx ON PersonalBests(level_id, frame_count, timestamp, user_id);
"""

INSERT_LEVEL = "INSERT OR IGNORE INTO Levels VALUES(?, ?);"
INSERT_USER = "INSERT OR REPLACE INTO Users VALUES(?, ?);"
INSERT_REPLAY = "INSERT OR IGNORE INTO Replays VALUES(?, ?, ?, ?, ?);"

UPDATE_PERSONAL_BESTS = """
INSERT OR REPLACE INTO PersonalBests
SELECT r.*
FROM Replays r
JOIN (
    SELECT r.level_id, r.user_id, max(r.timestamp) AS timestamp
    FROM Replays AS r
    GROUP BY r.level_id, r.user_id
) AS r2 ON r2.level_id = r.level_id AND r2.user_id = r.user_id AND r2.timestamp = r.timestamp;
"""

RECENT_TOP_10 = """
SELECT * FROM (
    SELECT
        rank() OVER (
            PARTITION BY r.level_id
            ORDER BY r.frame_count) AS rank,
        u.id,
        u.name,
        r.level_id,
        r.frame_count,
        r.timestamp
    FROM Users AS u
    JOIN PersonalBests AS r ON r.user_id = u.id
    ORDER BY r.timestamp DESC
)
WHERE timestamp > strftime('%s', 'now') - 60 * 60 * 24 * 7
AND rank <= 10
"""

LEVEL_TOP_100 = """
SELECT
    rank() OVER (ORDER BY r.frame_count) AS rank,
    u.id,
    u.name,
    r.frame_count,
    r.timestamp
FROM Users u
JOIN PersonalBests r ON u.id = r.user_id
WHERE r.level_id = ?
ORDER BY r.frame_count
LIMIT 100
"""

USER_PROFILE = """
SELECT rank, level_id, frame_count, timestamp
FROM (
    SELECT
        rank() OVER (
            PARTITION BY r.level_id
            ORDER BY r.frame_count) AS rank,
        r.user_id,
        r.level_id,
        r.frame_count,
        r.timestamp
    FROM PersonalBests AS r
)
WHERE user_id = ?
ORDER BY level_id
"""

USER_NAME = "SELECT u.name FROM Users u WHERE u.id = ?"
LEVEL_NAME = "SELECT l.name FROM Levels l WHERE l.id = ?"

BEST_TIME_RANKINGS = """
SELECT
    rank() OVER (ORDER BY sum(rank) + 101 * (63 - count(level_id)) - 63),
    user_id,
    user_name,
    sum(rank) + 101 * (63 - count(level_id)) - 63 AS score
FROM (
    SELECT
        rank() OVER (
            PARTITION BY r.level_id
            ORDER BY r.frame_count) AS rank,
        r.user_id,
        u.name AS user_name,
        r.level_id,
        r.frame_count,
        r.timestamp
    FROM Users AS u
    JOIN PersonalBests AS r ON r.user_id = u.id
    WHERE r.level_id % 2 = 0
)
WHERE rank <= 100
GROUP BY user_id
ORDER BY score
LIMIT 100
"""

ALL_BIRDS_RANKINGS = """
SELECT
    rank() OVER (ORDER BY sum(rank) + 101 * (63 - count(level_id)) - 63),
    user_id,
    user_name,
    sum(rank) + 101 * (63 - count(level_id)) - 63 AS score
FROM (
    SELECT
        rank() OVER (
            PARTITION BY r.level_id
            ORDER BY r.frame_count) AS rank,
        r.user_id,
        u.name AS user_name,
        r.level_id,
        r.frame_count,
        r.timestamp
    FROM Users AS u
    JOIN PersonalBests AS r ON r.user_id = u.id
    WHERE r.level_id % 2 = 1
)
WHERE rank <= 100
GROUP BY user_id
ORDER BY score
LIMIT 100
"""

COMBINED_RANKINGS = """
SELECT
    rank() OVER (ORDER BY sum(rank) + 101 * (126 - count(level_id)) - 126),
    user_id,
    user_name,
    sum(rank) + 101 * (126 - count(level_id)) - 126 AS score
FROM (
    SELECT
        rank() OVER (
            PARTITION BY r.level_id
            ORDER BY r.frame_count) AS rank,
        r.user_id,
        u.name AS user_name,
        r.level_id,
        r.frame_count,
        r.timestamp
    FROM Users AS u
    JOIN PersonalBests AS r ON r.user_id = u.id
)
WHERE rank <= 100
GROUP BY user_id
ORDER BY score
LIMIT 100
"""
