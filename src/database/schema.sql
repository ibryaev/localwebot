BEGIN TRANSACTION;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'admin_type') THEN
        CREATE TYPE admin_type AS ENUM ('owner', 'helper', 'admin', 'moder');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'restriction_type') THEN
        CREATE TYPE restriction_type AS ENUM ('ban', 'mute');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS users (
    tid BIGINT PRIMARY KEY,
    username VARCHAR(32) DEFAULT NULL
);  

CREATE TABLE IF NOT EXISTS webs (
    web_id VARCHAR(4) PRIMARY KEY,
    forename VARCHAR(32) NOT NULL,
    emoji TEXT DEFAULT NULL,
    owner_tid BIGINT REFERENCES users(tid) ON DELETE CASCADE,
    chats_tid BIGINT[] NOT NULL DEFAULT '{}',
    date_reg TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chats (
    chat_tid BIGINT PRIMARY KEY REFERENCES users(tid) ON DELETE CASCADE,
    web_id VARCHAR(4) REFERENCES webs(web_id) ON DELETE CASCADE,
    owner_tid BIGINT REFERENCES users(tid) ON DELETE CASCADE,
    date_reg TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admins (
    admin_id VARCHAR(4) PRIMARY KEY,
    admin_tid BIGINT REFERENCES users(tid) ON DELETE CASCADE,
    web_id VARCHAR(4) REFERENCES webs(web_id) ON DELETE CASCADE,
    post admin_type NOT NULL,
    date_reg TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS restrs (
    restr_id VARCHAR(4) PRIMARY KEY,
    web_id VARCHAR(4) REFERENCES webs(web_id) ON DELETE CASCADE,
    user_tid BIGINT NOT NULL,
    restr restriction_type NOT NULL,
    admin_tid BIGINT NOT NULL,
    reason TEXT DEFAULT NULL,
    date_reg TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_until TIMESTAMP DEFAULT NULL
);

COMMIT;