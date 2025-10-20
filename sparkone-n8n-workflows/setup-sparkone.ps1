# ⚡ SparkOne Setup Script - PowerShell
# Script automatizado para configurar o sistema SparkOne completo no Windows

param(
    [switch]$SkipEnvCheck
)

# Função para log
function Write-Log {
    param($Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message" -ForegroundColor Blue
}

function Write-Success {
    param($Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param($Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

# Verificar se Docker está instalado
function Test-Docker {
    Write-Log "Verificando instalação do Docker..."
    
    try {
        $dockerVersion = docker --version
        $dockerComposeVersion = docker-compose --version
        Write-Success "Docker e Docker Compose estão instalados"
        Write-Host "Docker: $dockerVersion" -ForegroundColor Gray
        Write-Host "Docker Compose: $dockerComposeVersion" -ForegroundColor Gray
    }
    catch {
        Write-Error "Docker não está instalado ou não está no PATH. Instale o Docker Desktop primeiro."
        exit 1
    }
}

# Verificar arquivo .env
function Test-EnvFile {
    Write-Log "Verificando arquivo de configuração..."
    
    if (-not (Test-Path ".env")) {
        Write-Warning "Arquivo .env não encontrado. Criando a partir do template..."
        Copy-Item "env.template" ".env"
        Write-Warning "Configure suas chaves de API no arquivo .env antes de continuar"
        Write-Host ""
        Write-Host "Variáveis obrigatórias:" -ForegroundColor Yellow
        Write-Host "- OPENAI_API_KEY" -ForegroundColor Gray
        Write-Host "- OPENWEATHER_API_KEY" -ForegroundColor Gray
        Write-Host "- NEWS_API_KEY" -ForegroundColor Gray
        Write-Host ""
        Read-Host "Pressione Enter após configurar o arquivo .env"
    }
    
    # Carregar variáveis do .env
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
    
    # Verificar variáveis obrigatórias
    $requiredVars = @("OPENAI_API_KEY", "OPENWEATHER_API_KEY", "NEWS_API_KEY")
    
    foreach ($var in $requiredVars) {
        $value = [Environment]::GetEnvironmentVariable($var, "Process")
        if ([string]::IsNullOrEmpty($value) -or $value -match "your_.*_api_key") {
            Write-Error "$var não configurada corretamente no arquivo .env"
            exit 1
        }
    }
    
    Write-Success "Arquivo .env configurado corretamente"
}

# Parar containers existentes
function Stop-Containers {
    Write-Log "Parando containers existentes..."
    try {
        docker-compose down --remove-orphans
        Write-Success "Containers parados"
    }
    catch {
        Write-Warning "Erro ao parar containers (pode ser normal se não existirem)"
    }
}

# Iniciar serviços
function Start-Services {
    Write-Log "Iniciando serviços SparkOne..."
    docker-compose up -d
    
    Write-Log "Aguardando serviços iniciarem..."
    Start-Sleep -Seconds 15
    
    Write-Success "Serviços iniciados"
}

# Verificar saúde dos serviços
function Test-ServicesHealth {
    Write-Log "Verificando saúde dos serviços..."
    
    # Verificar Evolution API
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/manager/fetchInstances" -TimeoutSec 5 -UseBasicParsing
        Write-Success "Evolution API está funcionando"
    }
    catch {
        Write-Warning "Evolution API pode não estar funcionando corretamente: $($_.Exception.Message)"
    }
    
    # Verificar n8n
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5678" -TimeoutSec 5 -UseBasicParsing
        Write-Success "n8n está funcionando"
    }
    catch {
        Write-Warning "n8n pode não estar funcionando corretamente: $($_.Exception.Message)"
    }
}

# Criar instância do WhatsApp
function New-WhatsAppInstance {
    Write-Log "Criando instância do WhatsApp..."
    
    $headers = @{
        "Content-Type" = "application/json"
        "apikey" = "sparkone_2024_secure_key"
    }
    
    $body = @{
        instanceName = "sparkone-instance"
        token = "sparkone-whatsapp-token"
        qrcode = $true
        integration = "WHATSAPP-BAILEYS"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8080/instance/create" -Method POST -Headers $headers -Body $body
        Write-Success "Instância WhatsApp criada"
        Write-Host "Acesse http://localhost:8080/sparkone-instance/qrcode para conectar seu WhatsApp" -ForegroundColor Cyan
    }
    catch {
        Write-Warning "Erro ao criar instância WhatsApp: $($_.Exception.Message)"
    }
}

# Mostrar informações finais
function Show-FinalInfo {
    Write-Host ""
    Write-Host "🎉 SparkOne configurado com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📱 URLs importantes:" -ForegroundColor Yellow
    Write-Host "   Evolution API: http://localhost:8080" -ForegroundColor Gray
    Write-Host "   n8n Interface: http://localhost:5678" -ForegroundColor Gray
    Write-Host "   WhatsApp QR: http://localhost:8080/sparkone-instance/qrcode" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔑 Credenciais n8n:" -ForegroundColor Yellow
    Write-Host "   Usuário: admin" -ForegroundColor Gray
    Write-Host "   Senha: sparkone2024" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📋 Próximos passos:" -ForegroundColor Yellow
    Write-Host "   1. Acesse o n8n e importe os workflows JSON" -ForegroundColor Gray
    Write-Host "   2. Configure as credenciais no n8n" -ForegroundColor Gray
    Write-Host "   3. Conecte seu WhatsApp escaneando o QR Code" -ForegroundColor Gray
    Write-Host "   4. Teste enviando uma mensagem para o WhatsApp" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📚 Documentação: README_JARVIS_SYSTEM.md" -ForegroundColor Cyan
    Write-Host "⚙️  Configuração: CONFIGURACAO_SPARKONE.md" -ForegroundColor Cyan
}

# Função principal
function Main {
    Write-Host "⚡ SparkOne Setup - Sistema de IA Avançado" -ForegroundColor Magenta
    Write-Host "==========================================" -ForegroundColor Magenta
    Write-Host ""
    
    Test-Docker
    
    if (-not $SkipEnvCheck) {
        Test-EnvFile
    }
    
    Stop-Containers
    Start-Services
    Test-ServicesHealth
    New-WhatsAppInstance
    Show-FinalInfo
}

# Executar função principal
Main

