#!/usr/bin/env bash
set -euo pipefail

# Script de verificação de backup para SparkOne
# Verifica integridade de backups de banco e arquivos

BACKUP_DIR=${BACKUP_DIR:-/opt/sparkone/backups}
LOG_FILE="/var/log/sparkone-backup.log"

# Função de log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Função para verificar backup do banco
verify_database_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        log "ERRO: Arquivo de backup não encontrado: $backup_file"
        return 1
    fi
    
    log "Verificando backup do banco: $backup_file"
    
    # Verificar se é um arquivo custom do pg_dump
    if [[ "$backup_file" == *.sql ]]; then
        # Verificar se o arquivo não está vazio
        if [ ! -s "$backup_file" ]; then
            log "ERRO: Arquivo de backup está vazio"
            return 1
        fi
        
        # Verificar se contém dados SQL válidos
        if ! head -n 10 "$backup_file" | grep -q "PostgreSQL database dump"; then
            log "ERRO: Arquivo não parece ser um dump válido do PostgreSQL"
            return 1
        fi
        
        log "Backup do banco verificado com sucesso"
        return 0
    else
        log "AVISO: Formato de backup não suportado: $backup_file"
        return 1
    fi
}

# Função para verificar backup de arquivos
verify_files_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        log "ERRO: Arquivo de backup não encontrado: $backup_file"
        return 1
    fi
    
    log "Verificando backup de arquivos: $backup_file"
    
    # Verificar se é um arquivo tar.gz
    if [[ "$backup_file" == *.tar.gz ]]; then
        # Verificar integridade do arquivo
        if ! tar -tzf "$backup_file" >/dev/null 2>&1; then
            log "ERRO: Arquivo tar.gz corrompido"
            return 1
        fi
        
        # Verificar se não está vazio
        if [ ! -s "$backup_file" ]; then
            log "ERRO: Arquivo de backup está vazio"
            return 1
        fi
        
        log "Backup de arquivos verificado com sucesso"
        return 0
    else
        log "AVISO: Formato de backup não suportado: $backup_file"
        return 1
    fi
}

# Função para verificar backups mais recentes
verify_latest_backups() {
    log "Verificando backups mais recentes..."
    
    local db_backup=$(find "$BACKUP_DIR" -name "sparkone_db_*.sql" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    local files_backup=$(find "$BACKUP_DIR" -name "sparkone_files_*.tar.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    local success=true
    
    if [ -n "$db_backup" ]; then
        if ! verify_database_backup "$db_backup"; then
            success=false
        fi
    else
        log "AVISO: Nenhum backup de banco encontrado"
    fi
    
    if [ -n "$files_backup" ]; then
        if ! verify_files_backup "$files_backup"; then
            success=false
        fi
    else
        log "AVISO: Nenhum backup de arquivos encontrado"
    fi
    
    if [ "$success" = true ]; then
        log "Todos os backups verificados com sucesso"
        return 0
    else
        log "ERRO: Alguns backups falharam na verificação"
        return 1
    fi
}

# Função principal
main() {
    if [ $# -eq 0 ]; then
        # Verificar backups mais recentes
        verify_latest_backups
    else
        # Verificar arquivo específico
        local backup_file="$1"
        if [[ "$backup_file" == *.sql ]]; then
            verify_database_backup "$backup_file"
        elif [[ "$backup_file" == *.tar.gz ]]; then
            verify_files_backup "$backup_file"
        else
            log "ERRO: Formato de arquivo não suportado: $backup_file"
            exit 1
        fi
    fi
}

# Executar função principal
main "$@"
