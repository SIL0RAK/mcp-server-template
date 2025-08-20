INSERT INTO data (name, value)
SELECT
    substr(md5(random()::text), 1, 5) AS name,   -- random 5-character string
    substr(md5(random()::text), 1, 8) AS value  -- random 8-character string
FROM generate_series(1, 10);