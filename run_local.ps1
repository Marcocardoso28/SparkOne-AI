# ============================================================================
# SCRIPT PARA EXECUTAR SPARKONE LOCALMENTE (SEM DOCKER)
# ============================================================================

Write-Host "🚀 Iniciando SparkOne em ambiente local..." -ForegroundColor Green

# Verificar se Python está instalado
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python não encontrado. Instale Python 3.11+ primeiro." -ForegroundColor Red
    exit 1
}

# Verificar se PostgreSQL está rodando (assumindo instalação local)
Write-Host "📊 Verificando PostgreSQL local..." -ForegroundColor Yellow
$pgStatus = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
if ($pgStatus) {
    Write-Host "✅ PostgreSQL encontrado" -ForegroundColor Green
} else {
    Write-Host "⚠️  PostgreSQL não encontrado. Você precisará de um banco PostgreSQL rodando." -ForegroundColor Yellow
    Write-Host "   Opções:" -ForegroundColor Yellow
    Write-Host "   1. Instalar PostgreSQL localmente" -ForegroundColor Yellow
    Write-Host "   2. Usar Docker apenas para o banco: docker run -d -p 5432:5432 -e POSTGRES_DB=sparkone -e POSTGRES_USER=sparkone -e POSTGRES_PASSWORD=sparkone postgres:15" -ForegroundColor Yellow
}

# Verificar se Redis está rodando
Write-Host "🔄 Verificando Redis local..." -ForegroundColor Yellow
$redisProcess = Get-Process -Name "redis-server" -ErrorAction SilentlyContinue
if ($redisProcess) {
    Write-Host "✅ Redis encontrado" -ForegroundColor Green
} else {
    Write-Host "⚠️  Redis não encontrado. Você precisará de Redis rodando." -ForegroundColor Yellow
    Write-Host "   Opção: docker run -d -p 6379:6379 redis:7-alpine" -ForegroundColor Yellow
}

# Criar ambiente virtual se não existir
if (!(Test-Path "venv")) {
    Write-Host "📦 Criando ambiente virtual..." -ForegroundColor Yellow
    python -m venv venv
}

# Ativar ambiente virtual
Write-Host "🔧 Ativando ambiente virtual..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Instalar dependências
Write-Host "📚 Instalando dependências..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -e .[dev]

# Configurar variáveis de ambiente para execução local
Write-Host "⚙️  Configurando variáveis de ambiente..." -ForegroundColor Yellow
$env:DATABASE_URL = "postgresql+asyncpg://sparkone:sparkone@localhost:5432/sparkone"
$env:VECTOR_STORE_URL = "postgresql://sparkone:sparkone@localhost:5432/sparkone"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:ENVIRONMENT = "development"
$env:DEBUG = "true"

# Executar migrações
Write-Host "🗄️  Executando migrações..." -ForegroundColor Yellow
alembic upgrade head

# Iniciar servidor
Write-Host "🌟 Iniciando servidor SparkOne..." -ForegroundColor Green
Write-Host "   API estará disponível em: http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Documentação em: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   Profiler em: http://localhost:8000/profiler/stats" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow

uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload