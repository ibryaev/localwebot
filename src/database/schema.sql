BEGIN TRANSACTION;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'admin_type') THEN
        CREATE TYPE admin_type AS ENUM ('owner', 'helper', 'admin', 'moder');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'restriction_type') THEN
        CREATE TYPE restriction_type AS ENUM ('ban', 'mute');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS webs (
    id_web SERIAL PRIMARY KEY,
    forename VARCHAR(32),
    tid_owner BIGINT,
    tid_chats BIGINT[] DEFAULT '{}',
    date_reg TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chats (
    tid_chat BIGINT PRIMARY KEY,
    username VARCHAR(32) DEFAULT NULL,
    id_web INTEGER REFERENCES webs(id_web) ON DELETE CASCADE,
    tid_owner BIGINT,
    date_reg TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admins (
    id_admin SERIAL PRIMARY KEY,
    tid_user BIGINT,
    username VARCHAR(32) DEFAULT NULL,
    id_web INTEGER REFERENCES webs(id_web) ON DELETE CASCADE,
    post admin_type,
    date_reg TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tid_user, id_web)
);

CREATE TABLE IF NOT EXISTS restrictions (
    id_restriction SERIAL PRIMARY KEY,
    tid_user BIGINT,
    username VARCHAR(32) DEFAULT NULL,
    id_web INTEGER REFERENCES webs(id_web) ON DELETE CASCADE,
    restriction restriction_type,
    reason TEXT,
    tid_admin BIGINT,
    date_reg TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_until TIMESTAMP DEFAULT NULL
);

COMMIT;
