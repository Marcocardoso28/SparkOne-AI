#!/usr/bin/env bash
set -euo pipefail

# Script de restore para SparkOne em produção
# Suporta restore de banco PostgreSQL gerenciado e arquivos locais

BACKUP_DIR=${BACKUP_DIR:-/opt/sparkone/backups}
LOG_FILE="/var/log/sparkone-restore.log"

# Função de log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Função para confirmar ação
confirm() {
    local message="$1"
    echo -n "$message (y/N): "
    read -r response
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

# Função para restore do banco
restore_database() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        log "ERRO: Arquivo de backup não encontrado: $backup_file"
        return 1
    fi
    
    log "Iniciando restore do banco de dados..."
    
    # Carregar variáveis de ambiente
    if [ -f "/opt/sparkone/.env.prod" ]; then
        source /opt/sparkone/.env.prod
    else
        log "ERRO: Arquivo .env.prod não encontrado"
        return 1
    fi
    
    if [ -z "${DATABASE_URL:-}" ]; then
        log "ERRO: DATABASE_URL não configurada"
        return 1
    fi
    
    # Extrair informações da URL do banco
    if [[ $DATABASE_URL =~ postgresql\+asyncpg://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
        local db_user="${BASH_REMATCH[1]}"
        local db_password="${BASH_REMATCH[2]}"
        local db_host="${BASH_REMATCH[3]}"
        local db_port="${BASH_REMATCH[4]}"
        local db_name="${BASH_REMATCH[5]}"
        
        # Confirmar restore
        if ! confirm "ATENÇÃO: Isso irá sobrescrever o banco de dados atual. Continuar?"; then
            log "Restore cancelado pelo usuário"
            return 1
        fi
        
        # Parar aplicação temporariamente
        log "Parando aplicação..."
        cd /opt/sparkone
        docker-compose -f docker-compose.prod.yml stop api worker
        
        # Restore usando pg_restore ou psql
        if [[ "$backup_file" == *.sql ]]; then
            log "Executando restore com psql..."
            PGPASSWORD="$db_password" psql \
                -h "$db_host" \
                -p "$db_port" \
                -U "$db_user" \
                -d "$db_name" \
                --no-password \
                -f "$backup_file"
        else
            log "ERRO: Formato de backup não suportado para restore: $backup_file"
            return 1
        fi
        
        # Reiniciar aplicação
        log "Reiniciando aplicação..."
        docker-compose -f docker-compose.prod.yml start api worker
        
        log "Restore do banco concluído com sucesso"
        return 0
    else
        log "ERRO: URL do banco inválida: $DATABASE_URL"
        return 1
    fi
}

# Função para restore de arquivos
restore_files() {
    local backup_file="$1"
    local target_dir="${2:-/opt/sparkone/uploads}"
    
    if [ ! -f "$backup_file" ]; then
        log "ERRO: Arquivo de backup não encontrado: $backup_file"
        return 1
    fi
    
    log "Iniciando restore de arquivos..."
    
    # Confirmar restore
    if ! confirm "ATENÇÃO: Isso irá sobrescrever os arquivos em $target_dir. Continuar?"; then
        log "Restore cancelado pelo usuário"
        return 1
    fi
    
    # Fazer backup dos arquivos atuais
    local current_backup="/tmp/uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    if [ -d "$target_dir" ]; then
        log "Fazendo backup dos arquivos atuais..."
        tar -czf "$current_backup" -C "$(dirname "$target_dir")" "$(basename "$target_dir")"
    fi
    
    # Restore dos arquivos
    if [[ "$backup_file" == *.tar.gz ]]; then
        log "Extraindo arquivos de $backup_file para $target_dir..."
        
        # Criar diretório se não existir
        mkdir -p "$target_dir"
        
        # Extrair arquivos
        tar -xzf "$backup_file" -C "$(dirname "$target_dir")"
        
        log "Restore de arquivos concluído com sucesso"
        return 0
    else
        log "ERRO: Formato de backup não suportado: $backup_file"
        return 1
    fi
}

# Função para listar backups disponíveis
list_backups() {
    log "Backups disponíveis:"
    echo "=== Backups de Banco ==="
    find "$BACKUP_DIR" -name "sparkone_db_*.sql" -type f -printf '%T@ %Tc %p\n' | sort -n | tail -10
    echo ""
    echo "=== Backups de Arquivos ==="
    find "$BACKUP_DIR" -name "sparkone_files_*.tar.gz" -type f -printf '%T@ %Tc %p\n' | sort -n | tail -10
}

# Função principal
main() {
    log "=== Script de Restore do SparkOne ==="
    
    if [ $# -eq 0 ]; then
        echo "Uso: $0 [--list] [--db <arquivo.sql>] [--files <arquivo.tar.gz>]"
        echo ""
        echo "Opções:"
        echo "  --list                    Listar backups disponíveis"
        echo "  --db <arquivo.sql>        Restore do banco de dados"
        echo "  --files <arquivo.tar.gz>  Restore de arquivos"
        exit 1
    fi
    
    case "$1" in
        --list)
            list_backups
            ;;
        --db)
            if [ $# -lt 2 ]; then
                log "ERRO: Arquivo de backup do banco não especificado"
                exit 1
            fi
            restore_database "$2"
            ;;
        --files)
            if [ $# -lt 2 ]; then
                log "ERRO: Arquivo de backup de arquivos não especificado"
                exit 1
            fi
            restore_files "$2"
            ;;
        *)
            log "ERRO: Opção inválida: $1"
            exit 1
            ;;
    esac
}

# Executar função principal
main "$@"
