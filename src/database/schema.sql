-- Весь этот проект посвящается моему дяде.

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
    first_name_title VARCHAR(128) NOT NULL,
    last_name VARCHAR(128) DEFAULT NULL,
    full_name VARCHAR(256) NOT NULL,
    username VARCHAR(32) DEFAULT NULL,
    link TEXT NOT NULL,
    UNIQUE(username)
);

CREATE TABLE IF NOT EXISTS webs (
    web_id VARCHAR(4) PRIMARY KEY,
    forename VARCHAR(64) NOT NULL,
    emoji TEXT DEFAULT NULL,
    descr VARCHAR(200) DEFAULT NULL,
    owner_tid BIGINT REFERENCES users(tid) ON DELETE CASCADE,
    heir_tid BIGINT REFERENCES users(tid) ON DELETE SET NULL DEFAULT NULL,
    chats_tid BIGINT[] NOT NULL DEFAULT '{}',
    admin_chat_tid BIGINT DEFAULT NULL,
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
    restrs_count INTEGER NOT NULL DEFAULT 0,
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

CREATE TABLE IF NOT EXISTS reports (
    report_id VARCHAR(4) PRIMARY KEY,
    web_id VARCHAR(4) REFERENCES webs(web_id) ON DELETE CASCADE,
    sender_tid BIGINT REFERENCES users(tid) ON DELETE CASCADE,
    target_tid BIGINT REFERENCES users(tid) ON DELETE CASCADE,
    reason TEXT DEFAULT NULL,
    date_reg TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE webs 
ADD CONSTRAINT fk_admin_chat 
FOREIGN KEY (admin_chat_tid) REFERENCES chats(chat_tid) ON DELETE SET NULL;

COMMIT;
