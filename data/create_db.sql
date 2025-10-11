-- Script SQL para criar o banco de dados SQLite
-- Tabela events
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_at DATETIME NOT NULL,
    end_at DATETIME,
    status VARCHAR(20) DEFAULT 'confirmed' NOT NULL,
    location VARCHAR(255),
    external_id VARCHAR(255),
    channel VARCHAR(50) NOT NULL,
    sender VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela tasks
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    priority VARCHAR(10) DEFAULT 'medium' NOT NULL,
    due_date DATETIME,
    channel VARCHAR(50) NOT NULL,
    sender VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela alembic_version
CREATE TABLE alembic_version (
    version_num VARCHAR(32) PRIMARY KEY
);

INSERT INTO alembic_version (version_num) VALUES ('9876c53d37d2');