-- infra/db_schema.sql
-- Drivers
CREATE TABLE drivers (
    id SERIAL PRIMARY KEY,
    driver_code TEXT UNIQUE,
    name TEXT,
    team TEXT
);

-- Teams (optional)
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name TEXT
);

-- Races
CREATE TABLE races (
    id SERIAL PRIMARY KEY,
    season INT,
    round INT,
    name TEXT,
    circuit TEXT,
    date_utc TIMESTAMPTZ
);

-- Laps
CREATE TABLE laps (
    id SERIAL PRIMARY KEY,
    race_id INT REFERENCES races(id),
    driver_id INT REFERENCES drivers(id),
    lap INT,
    lap_time_ms INT,
    tyre_compound TEXT,
    tyre_age INT,
    pit_stop BOOLEAN
);

-- Stints
CREATE TABLE stints (
    id SERIAL PRIMARY KEY,
    race_id INT REFERENCES races(id),
    driver_id INT REFERENCES drivers(id),
    compound TEXT,
    lap_start INT,
    lap_end INT
);

-- Overtakes
CREATE TABLE overtakes (
    id SERIAL PRIMARY KEY,
    race_id INT REFERENCES races(id),
    lap INT,
    attacker_id INT REFERENCES drivers(id),
    defender_id INT REFERENCES drivers(id),
    corner_id TEXT
);
