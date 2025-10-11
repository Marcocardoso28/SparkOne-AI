# ============================================================================
# SCRIPT PARA CONFIGURAR BANCO DE DADOS LOCAL (APENAS POSTGRES + REDIS)
# ============================================================================

Write-Host "🐘 Configurando PostgreSQL e Redis locais com Docker..." -ForegroundColor Green

# Parar containers existentes se houver
Write-Host "🛑 Parando containers existentes..." -ForegroundColor Yellow
docker stop sparkone-postgres sparkone-redis 2>$null
docker rm sparkone-postgres sparkone-redis 2>$null

# Iniciar PostgreSQL
Write-Host "🐘 Iniciando PostgreSQL..." -ForegroundColor Yellow
docker run -d `
  --name sparkone-postgres `
  -p 5432:5432 `
  -e POSTGRES_DB=sparkone `
  -e POSTGRES_USER=sparkone `
  -e POSTGRES_PASSWORD=sparkone `
  -v sparkone_pgdata:/var/lib/postgresql/data `
  postgres:15 `
  postgres -c shared_preload_libraries=pg_stat_statements -c max_connections=200 -c shared_buffers=256MB

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PostgreSQL iniciado com sucesso" -ForegroundColor Green
} else {
    Write-Host "❌ Erro ao iniciar PostgreSQL" -ForegroundColor Red
    exit 1
}

# Iniciar Redis
Write-Host "🔄 Iniciando Redis..." -ForegroundColor Yellow
docker run -d `
  --name sparkone-redis `
  -p 6379:6379 `
  redis:7-alpine

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Redis iniciado com sucesso" -ForegroundColor Green
} else {
    Write-Host "❌ Erro ao iniciar Redis" -ForegroundColor Red
    exit 1
}

# Aguardar serviços iniciarem
Write-Host "⏳ Aguardando serviços iniciarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar status
Write-Host "📊 Status dos serviços:" -ForegroundColor Cyan
docker ps --filter "name=sparkone-"

Write-Host "" -ForegroundColor White
Write-Host "✅ Banco de dados configurado!" -ForegroundColor Green
Write-Host "   PostgreSQL: localhost:5432" -ForegroundColor Cyan
Write-Host "   Redis: localhost:6379" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White
Write-Host "Agora execute: .\run_local.ps1" -ForegroundColor Yellow