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
    forename VARCHAR(32) NOT NULL,
    emoji TEXT DEFAULT NULL,
    tid_owner BIGINT NOT NULL,
    tid_chats BIGINT[] DEFAULT '{}',
    date_reg TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usernames (
    tid BIGINT PRIMARY KEY,
    username VARCHAR(32) DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS chats (
    id_chat SERIAL PRIMARY KEY,
    tid_chat BIGINT REFERENCES usernames(tid) ON DELETE CASCADE,
    id_web INTEGER REFERENCES webs(id_web) ON DELETE CASCADE,
    tid_owner BIGINT REFERENCES usernames(tid) ON DELETE CASCADE,
    date_reg TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admins (
    id_admin SERIAL PRIMARY KEY,
    tid_admin BIGINT REFERENCES usernames(tid) ON DELETE CASCADE,
    id_web INTEGER REFERENCES webs(id_web) ON DELETE CASCADE,
    post admin_type NOT NULL,
    date_reg TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ress (
    id_res SERIAL PRIMARY KEY,
    tid_user BIGINT,
    id_web INTEGER REFERENCES webs(id_web) ON DELETE CASCADE,
    res restriction_type NOT NULL,
    reason TEXT DEFAULT NULL,
    tid_admin BIGINT,
    date_reg TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_until TIMESTAMP DEFAULT NULL
);

COMMIT;
