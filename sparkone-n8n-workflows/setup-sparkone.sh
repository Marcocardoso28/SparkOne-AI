#!/bin/bash

# ⚡ SparkOne Setup Script
# Script automatizado para configurar o sistema SparkOne completo

set -e

echo "🚀 Iniciando configuração do SparkOne..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar se Docker está instalado
check_docker() {
    log "Verificando instalação do Docker..."
    if ! command -v docker &> /dev/null; then
        error "Docker não está instalado. Instale o Docker primeiro."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose não está instalado. Instale o Docker Compose primeiro."
        exit 1
    fi
    
    success "Docker e Docker Compose estão instalados"
}

# Verificar se arquivo .env existe
check_env() {
    log "Verificando arquivo de configuração..."
    if [ ! -f .env ]; then
        warning "Arquivo .env não encontrado. Criando a partir do template..."
        cp env.template .env
        warning "Configure suas chaves de API no arquivo .env antes de continuar"
        echo ""
        echo "Variáveis obrigatórias:"
        echo "- OPENAI_API_KEY"
        echo "- OPENWEATHER_API_KEY" 
        echo "- NEWS_API_KEY"
        echo ""
        read -p "Pressione Enter após configurar o arquivo .env..."
    fi
    
    # Verificar variáveis obrigatórias
    source .env
    
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
        error "OPENAI_API_KEY não configurada no arquivo .env"
        exit 1
    fi
    
    if [ -z "$OPENWEATHER_API_KEY" ] || [ "$OPENWEATHER_API_KEY" = "your_openweather_api_key_here" ]; then
        error "OPENWEATHER_API_KEY não configurada no arquivo .env"
        exit 1
    fi
    
    if [ -z "$NEWS_API_KEY" ] || [ "$NEWS_API_KEY" = "your_news_api_key_here" ]; then
        error "NEWS_API_KEY não configurada no arquivo .env"
        exit 1
    fi
    
    success "Arquivo .env configurado corretamente"
}

# Parar containers existentes
stop_containers() {
    log "Parando containers existentes..."
    docker-compose down --remove-orphans || true
    success "Containers parados"
}

# Iniciar serviços
start_services() {
    log "Iniciando serviços SparkOne..."
    docker-compose up -d
    
    log "Aguardando serviços iniciarem..."
    sleep 10
    
    success "Serviços iniciados"
}

# Verificar saúde dos serviços
check_health() {
    log "Verificando saúde dos serviços..."
    
    # Verificar Evolution API
    if curl -s http://localhost:8080/manager/fetchInstances > /dev/null; then
        success "Evolution API está funcionando"
    else
        warning "Evolution API pode não estar funcionando corretamente"
    fi
    
    # Verificar n8n
    if curl -s http://localhost:5678 > /dev/null; then
        success "n8n está funcionando"
    else
        warning "n8n pode não estar funcionando corretamente"
    fi
}

# Criar instância do WhatsApp
create_whatsapp_instance() {
    log "Criando instância do WhatsApp..."
    
    INSTANCE_RESPONSE=$(curl -s -X POST http://localhost:8080/instance/create \
        -H "Content-Type: application/json" \
        -H "apikey: sparkone_2024_secure_key" \
        -d '{
            "instanceName": "sparkone-instance",
            "token": "sparkone-whatsapp-token",
            "qrcode": true,
            "integration": "WHATSAPP-BAILEYS"
        }')
    
    if echo "$INSTANCE_RESPONSE" | grep -q "success"; then
        success "Instância WhatsApp criada"
        log "Acesse http://localhost:8080/sparkone-instance/qrcode para conectar seu WhatsApp"
    else
        warning "Erro ao criar instância WhatsApp: $INSTANCE_RESPONSE"
    fi
}

# Mostrar informações finais
show_info() {
    echo ""
    echo "🎉 SparkOne configurado com sucesso!"
    echo ""
    echo "📱 URLs importantes:"
    echo "   Evolution API: http://localhost:8080"
    echo "   n8n Interface: http://localhost:5678"
    echo "   WhatsApp QR: http://localhost:8080/sparkone-instance/qrcode"
    echo ""
    echo "🔑 Credenciais n8n:"
    echo "   Usuário: admin"
    echo "   Senha: sparkone2024"
    echo ""
    echo "📋 Próximos passos:"
    echo "   1. Acesse o n8n e importe os workflows JSON"
    echo "   2. Configure as credenciais no n8n"
    echo "   3. Conecte seu WhatsApp escaneando o QR Code"
    echo "   4. Teste enviando uma mensagem para o WhatsApp"
    echo ""
    echo "📚 Documentação: README_JARVIS_SYSTEM.md"
    echo "⚙️  Configuração: CONFIGURACAO_SPARKONE.md"
}

# Função principal
main() {
    echo "⚡ SparkOne Setup - Sistema de IA Avançado"
    echo "=========================================="
    echo ""
    
    check_docker
    check_env
    stop_containers
    start_services
    check_health
    create_whatsapp_instance
    show_info
}

# Executar se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

