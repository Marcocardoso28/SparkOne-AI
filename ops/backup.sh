#!/usr/bin/env bash
set -euo pipefail

# Script de backup para SparkOne em produção
# Suporta backup de banco PostgreSQL gerenciado e arquivos locais

# Configurações
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.prod.yml}
BACKUP_DIR=${BACKUP_DIR:-/opt/sparkone/backups}
RETENTION_DAYS=${RETENTION_DAYS:-30}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="/var/log/sparkone-backup.log"

# Função de log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Função para backup do banco PostgreSQL gerenciado
backup_database() {
    local db_url="$1"
    local backup_file="$2"
    
    log "Iniciando backup do banco de dados..."
    
    # Extrair informações da URL do banco
    # postgresql+asyncpg://user:password@host:port/database
    if [[ $db_url =~ postgresql\+asyncpg://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
        local db_user="${BASH_REMATCH[1]}"
        local db_password="${BASH_REMATCH[2]}"
        local db_host="${BASH_REMATCH[3]}"
        local db_port="${BASH_REMATCH[4]}"
        local db_name="${BASH_REMATCH[5]}"
        
        # Backup usando pg_dump
        PGPASSWORD="$db_password" pg_dump \
            -h "$db_host" \
            -p "$db_port" \
            -U "$db_user" \
            -d "$db_name" \
            --no-password \
            --verbose \
            --format=custom \
            --compress=9 \
            --file="$backup_file"
        
        log "Backup do banco salvo em $backup_file"
    else
        log "ERRO: URL do banco inválida: $db_url"
        return 1
    fi
}

# Função para backup de arquivos
backup_files() {
    local source_dir="$1"
    local backup_file="$2"
    
    log "Iniciando backup de arquivos..."
    
    if [ -d "$source_dir" ]; then
        tar -czf "$backup_file" -C "$(dirname "$source_dir")" "$(basename "$source_dir")"
        log "Backup de arquivos salvo em $backup_file"
    else
        log "AVISO: Diretório $source_dir não encontrado"
    fi
}

# Função para limpeza de backups antigos
cleanup_old_backups() {
    log "Removendo backups antigos (mais de $RETENTION_DAYS dias)..."
    
    find "$BACKUP_DIR" -name "*.sql" -type f -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
    
    log "Limpeza de backups antigos concluída"
}

# Função principal
main() {
    log "=== Iniciando backup do SparkOne ==="
    
    # Criar diretório de backup se não existir
    mkdir -p "$BACKUP_DIR"
    
    # Carregar variáveis de ambiente
    if [ -f "/opt/sparkone/.env.prod" ]; then
        source /opt/sparkone/.env.prod
    else
        log "ERRO: Arquivo .env.prod não encontrado"
        exit 1
    fi
    
    # Backup do banco de dados
    if [ -n "${DATABASE_URL:-}" ]; then
        local db_backup_file="$BACKUP_DIR/sparkone_db_$TIMESTAMP.sql"
        backup_database "$DATABASE_URL" "$db_backup_file"
    else
        log "AVISO: DATABASE_URL não configurada, pulando backup do banco"
    fi
    
    # Backup de arquivos
    local files_backup_file="$BACKUP_DIR/sparkone_files_$TIMESTAMP.tar.gz"
    backup_files "/opt/sparkone/uploads" "$files_backup_file"
    
    # Limpeza de backups antigos
    cleanup_old_backups
    
    log "=== Backup concluído com sucesso ==="
}

# Executar função principal
main "$@"
