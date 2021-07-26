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
CREATE VIEW IF NOT EXISTS PersonalBests AS
SELECT r.*
FROM Replays r
JOIN (
    SELECT r.level_id, r.user_id, max(r.timestamp) AS timestamp
    FROM Replays as r
    GROUP BY r.level_id, r.user_id
) AS r2 ON r2.level_id = r.level_id AND r2.user_id = r.user_id AND r2.timestamp = r.timestamp
"""

INSERT_LEVEL = "INSERT INTO Levels VALUES(?, ?) ON CONFLICT(id) DO NOTHING;"
INSERT_USER = "INSERT INTO Users VALUES(?, ?) ON CONFLICT(id) DO UPDATE SET name = excluded.name;"
INSERT_REPLAY = "INSERT INTO Replays VALUES(?, ?, ?, ?, ?) ON CONFLICT(level_id, user_id, timestamp) DO NOTHING;"

RECENT_TOP_10 = """
SELECT * FROM (
    SELECT
        rank() OVER (
            PARTITION BY r.level_id
            ORDER BY r.frame_count) as rank,
        u.name as user_name,
        l.name as level_name,
        r.frame_count,
        r.timestamp
    FROM Users as u
    JOIN PersonalBests as r ON r.user_id = u.id
    JOIN Levels as l ON l.id = r.level_id
    ORDER BY r.timestamp DESC
)
WHERE timestamp > strftime('%s', 'now') - 60 * 60 * 24 * 7
AND rank <= 10"""

LEVEL_TOP_50 = """
SELECT
    rank() OVER (ORDER BY r.frame_count) as rank,
    u.name,
    r.frame_count,
    r.timestamp
FROM Users u
JOIN PersonalBests r ON u.id = r.user_id
WHERE r.level_id = ?
ORDER BY r.frame_count
LIMIT 50"""

LEVEL_NAME = "SELECT l.name FROM Levels l WHERE l.id = ?"
