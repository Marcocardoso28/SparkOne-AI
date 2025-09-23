"""Script para criar tabelas SQLite manualmente."""

import sqlite3
from pathlib import Path

def create_sqlite_tables():
    """Cria tabelas SQLite manualmente."""
    
    db_path = Path("sparkone.db")
    
    # Remove banco existente se estiver vazio
    if db_path.exists() and db_path.stat().st_size == 0:
        db_path.unlink()
        print("🗑️ Removido banco vazio")
    
    conn = sqlite3.connect("sparkone.db")
    cursor = conn.cursor()
    
    print("🚀 Criando tabelas SQLite...")
    
    # Tabela alembic_version
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        )
    """)
    
    # Inserir versão atual
    cursor.execute("INSERT OR REPLACE INTO alembic_version (version_num) VALUES ('0002')")
    
    # Tabela channel_messages (usando TEXT em vez de ENUM)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channel_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT NOT NULL,
            sender VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT NOT NULL,
            occurred_at DATETIME NOT NULL,
            extra_data TEXT NOT NULL DEFAULT '{}',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela message_embeddings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL UNIQUE,
            embedding TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (message_id) REFERENCES channel_messages (id) ON DELETE CASCADE
        )
    """)
    
    # Tabela knowledge_documents
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela knowledge_chunks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding TEXT NOT NULL,
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES knowledge_documents (id) ON DELETE CASCADE
        )
    """)
    
    # Tabela sheets_sync_state
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sheets_sync_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sheet_id TEXT NOT NULL UNIQUE,
            last_sync_at DATETIME,
            sync_status TEXT NOT NULL DEFAULT 'pending',
            error_message TEXT,
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela conversation_messages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela tasks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            due_at DATETIME,
            status TEXT NOT NULL DEFAULT 'todo',
            external_id TEXT,
            channel TEXT NOT NULL,
            sender TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            data TEXT NOT NULL DEFAULT '{}',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    
    # Verificar tabelas criadas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"✅ Tabelas criadas: {[t[0] for t in tables]}")
    
    # Verificar versão do Alembic
    cursor.execute("SELECT version_num FROM alembic_version;")
    version = cursor.fetchone()
    print(f"🏷️ Versão do Alembic: {version[0] if version else 'Nenhuma'}")
    
    # Verificar tamanho do banco
    conn.close()
    print(f"📊 Tamanho do banco: {db_path.stat().st_size} bytes")

if __name__ == "__main__":
    create_sqlite_tables()