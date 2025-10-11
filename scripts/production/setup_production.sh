#!/usr/bin/env bash
set -euo pipefail

# Script de setup para produção do SparkOne
# Este script automatiza a configuração inicial da VPS

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função de log
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Função para verificar se está rodando como root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "Este script não deve ser executado como root"
        exit 1
    fi
}

# Função para verificar se o usuário tem sudo
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        error "Este script requer privilégios sudo"
        exit 1
    fi
}

# Função para instalar dependências do sistema
install_system_dependencies() {
    log "Instalando dependências do sistema..."
    
    # Atualizar sistema
    sudo apt update && sudo apt upgrade -y
    
    # Instalar dependências básicas
    sudo apt install -y \
        curl \
        wget \
        git \
        unzip \
        postgresql-client \
        htop \
        vim \
        ufw \
        cron \
        logrotate
    
    success "Dependências do sistema instaladas"
}

# Função para instalar Docker
install_docker() {
    log "Instalando Docker..."
    
    if command -v docker &> /dev/null; then
        warning "Docker já está instalado"
        return 0
    fi
    
    # Instalar Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    
    # Adicionar usuário ao grupo docker
    sudo usermod -aG docker $USER
    
    # Instalar Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    success "Docker instalado com sucesso"
    warning "Você precisa fazer logout/login para usar Docker sem sudo"
}

# Função para configurar firewall
configure_firewall() {
    log "Configurando firewall..."
    
    # Configurar UFW
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow 22/tcp    # SSH
    sudo ufw allow 80/tcp    # HTTP
    sudo ufw allow 443/tcp   # HTTPS
    sudo ufw --force enable
    
    success "Firewall configurado"
}

# Função para criar estrutura de diretórios
create_directories() {
    log "Criando estrutura de diretórios..."
    
    # Criar diretório da aplicação
    sudo mkdir -p /opt/sparkone
    sudo chown $USER:$USER /opt/sparkone
    
    # Criar subdiretórios
    mkdir -p /opt/sparkone/{backups,secrets,uploads,logs}
    mkdir -p /opt/sparkone/ops/traefik/letsencrypt
    
    # Configurar permissões
    chmod 755 /opt/sparkone
    chmod 700 /opt/sparkone/secrets
    chmod 755 /opt/sparkone/{backups,uploads,logs}
    
    success "Estrutura de diretórios criada"
}

# Função para configurar logrotate
configure_logrotate() {
    log "Configurando logrotate..."
    
    sudo tee /etc/logrotate.d/sparkone > /dev/null <<EOF
/var/log/sparkone-*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        # Reiniciar serviços se necessário
    endscript
}
EOF
    
    success "Logrotate configurado"
}

# Função para configurar cron
configure_cron() {
    log "Configurando cron jobs..."
    
    # Adicionar jobs de backup
    (crontab -l 2>/dev/null || true; cat <<EOF

# SparkOne - Backup diário às 2h
0 2 * * * /opt/sparkone/ops/backup.sh >> /var/log/sparkone-backup.log 2>&1

# SparkOne - Verificação de backup às 3h
0 3 * * * /opt/sparkone/ops/verify_backup.sh >> /var/log/sparkone-backup.log 2>&1

# SparkOne - Limpeza de logs antigos às 4h
0 4 * * * find /var/log -name "sparkone-*.log.*" -mtime +30 -delete

EOF
    ) | crontab -
    
    success "Cron jobs configurados"
}

# Função para configurar sistema de monitoramento
configure_monitoring() {
    log "Configurando monitoramento básico..."
    
    # Instalar htop se não estiver instalado
    sudo apt install -y htop
    
    # Criar script de monitoramento
    sudo tee /usr/local/bin/sparkone-monitor > /dev/null <<'EOF'
#!/bin/bash
# Script de monitoramento básico do SparkOne

LOG_FILE="/var/log/sparkone-monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Verificar se Docker está rodando
if ! systemctl is-active --quiet docker; then
    echo "[$DATE] ERRO: Docker não está rodando" >> "$LOG_FILE"
    systemctl start docker
fi

# Verificar uso de disco
DISK_USAGE=$(df /opt/sparkone | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "[$DATE] AVISO: Uso de disco alto: ${DISK_USAGE}%" >> "$LOG_FILE"
fi

# Verificar uso de memória
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ "$MEM_USAGE" -gt 90 ]; then
    echo "[$DATE] AVISO: Uso de memória alto: ${MEM_USAGE}%" >> "$LOG_FILE"
fi

# Verificar se os containers estão rodando
if [ -d "/opt/sparkone" ]; then
    cd /opt/sparkone
    if [ -f "docker-compose.prod.yml" ]; then
        CONTAINERS_DOWN=$(docker-compose -f docker-compose.prod.yml ps -q | xargs docker inspect -f '{{.State.Status}}' | grep -v running | wc -l)
        if [ "$CONTAINERS_DOWN" -gt 0 ]; then
            echo "[$DATE] AVISO: $CONTAINERS_DOWN containers não estão rodando" >> "$LOG_FILE"
        fi
    fi
fi
EOF
    
    sudo chmod +x /usr/local/bin/sparkone-monitor
    
    # Adicionar ao cron
    (crontab -l 2>/dev/null || true; echo "*/5 * * * * /usr/local/bin/sparkone-monitor") | crontab -
    
    success "Monitoramento configurado"
}

# Função para configurar backup automático
configure_backup() {
    log "Configurando sistema de backup..."
    
    # Tornar scripts executáveis
    chmod +x /opt/sparkone/ops/backup.sh
    chmod +x /opt/sparkone/ops/verify_backup.sh
    chmod +x /opt/sparkone/ops/restore.sh
    
    # Criar diretório de backup se não existir
    mkdir -p /opt/sparkone/backups
    
    success "Sistema de backup configurado"
}

# Função para exibir informações pós-instalação
show_post_install_info() {
    log "Configuração concluída!"
    
    echo ""
    echo -e "${GREEN}=== PRÓXIMOS PASSOS ===${NC}"
    echo ""
    echo "1. Clone o repositório SparkOne:"
    echo "   cd /opt/sparkone"
    echo "   git clone https://github.com/seu-usuario/sparkone.git ."
    echo ""
    echo "2. Configure as variáveis de ambiente:"
    echo "   cp config/production.env .env.prod"
    echo "   nano .env.prod"
    echo ""
    echo "3. Configure o domínio nos arquivos:"
    echo "   - ops/traefik/traefik.yml"
    echo "   - ops/traefik/dynamic/sparkone.yml"
    echo "   - docker-compose.prod.yml"
    echo ""
    echo "4. Execute o deploy:"
    echo "   docker-compose -f docker-compose.prod.yml up -d"
    echo ""
    echo "5. Configure o DNS do seu domínio para apontar para este servidor"
    echo ""
    echo -e "${YELLOW}IMPORTANTE:${NC}"
    echo "- Faça logout/login para usar Docker sem sudo"
    echo "- Configure as variáveis de ambiente antes do deploy"
    echo "- Teste os backups após o deploy"
    echo ""
    echo -e "${BLUE}Documentação completa:${NC} docs/DEPLOY_PRODUCTION.md"
}

# Função principal
main() {
    echo -e "${BLUE}"
    echo "=========================================="
    echo "    SparkOne - Setup de Produção"
    echo "=========================================="
    echo -e "${NC}"
    
    # Verificações iniciais
    check_root
    check_sudo
    
    # Confirmar instalação
    echo -e "${YELLOW}Este script irá configurar o servidor para o SparkOne.${NC}"
    echo -e "${YELLOW}Continuar? (y/N):${NC} "
    read -r response
    case "$response" in
        [yY][eE][sS]|[yY]) ;;
        *) echo "Instalação cancelada"; exit 0 ;;
    esac
    
    # Executar configurações
    install_system_dependencies
    install_docker
    configure_firewall
    create_directories
    configure_logrotate
    configure_cron
    configure_monitoring
    configure_backup
    
    # Informações finais
    show_post_install_info
}

# Executar função principal
main "$@"
