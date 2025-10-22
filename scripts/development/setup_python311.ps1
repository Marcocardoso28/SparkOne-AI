# Script para configurar Python 3.11 após instalação manual
# Execute DEPOIS de instalar Python 3.11 do site oficial

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  SparkOne - Setup Python 3.11" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar se Python 3.11 está instalado
Write-Host "[1/7] Verificando Python 3.11..." -ForegroundColor Yellow
try {
    $pythonVersion = & python3.11 --version 2>&1
    Write-Host "✅ $pythonVersion encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Python 3.11 não encontrado!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Por favor, instale Python 3.11.9 primeiro:" -ForegroundColor Yellow
    Write-Host "https://www.python.org/downloads/release/python-3119/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Baixe: Windows installer (64-bit)" -ForegroundColor Yellow
    Write-Host "✅ Marque: 'Add Python 3.11 to PATH'" -ForegroundColor Yellow
    exit 1
}

# 2. Voltar para raiz do projeto
Write-Host ""
Write-Host "[2/7] Navegando para raiz do projeto..." -ForegroundColor Yellow
Set-Location $PSScriptRoot\..\..\
Write-Host "✅ Diretório: $(Get-Location)" -ForegroundColor Green

# 3. Fazer backup do venv antigo (se existir)
Write-Host ""
Write-Host "[3/7] Fazendo backup do ambiente virtual antigo..." -ForegroundColor Yellow
if (Test-Path "venv") {
    $backupName = "venv_backup_python314_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Rename-Item -Path "venv" -NewName $backupName
    Write-Host "✅ Backup criado: $backupName" -ForegroundColor Green
} else {
    Write-Host "✅ Nenhum venv anterior encontrado" -ForegroundColor Green
}

# 4. Criar novo ambiente virtual com Python 3.11
Write-Host ""
Write-Host "[4/7] Criando novo ambiente virtual com Python 3.11..." -ForegroundColor Yellow
& python3.11 -m venv venv
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Ambiente virtual criado com sucesso" -ForegroundColor Green
} else {
    Write-Host "❌ Erro ao criar ambiente virtual" -ForegroundColor Red
    exit 1
}

# 5. Ativar ambiente virtual
Write-Host ""
Write-Host "[5/7] Ativando ambiente virtual..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Ambiente virtual ativado" -ForegroundColor Green
} else {
    Write-Host "⚠️ Execute manualmente: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
}

# 6. Atualizar pip
Write-Host ""
Write-Host "[6/7] Atualizando pip..." -ForegroundColor Yellow
& python -m pip install --upgrade pip --quiet
Write-Host "✅ pip atualizado" -ForegroundColor Green

# 7. Instalar dependências do projeto
Write-Host ""
Write-Host "[7/7] Instalando dependências do projeto..." -ForegroundColor Yellow
Write-Host "Isso pode levar alguns minutos..." -ForegroundColor Gray
& pip install -e . --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependências instaladas com sucesso!" -ForegroundColor Green
} else {
    Write-Host "❌ Erro ao instalar dependências" -ForegroundColor Red
    Write-Host "Tente manualmente: pip install -e ." -ForegroundColor Yellow
    exit 1
}

# Verificações finais
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  VALIDAÇÕES FINAIS" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Verificando instalações críticas..." -ForegroundColor Yellow

# Verificar asyncpg
Write-Host ""
Write-Host "→ asyncpg: " -NoNewline -ForegroundColor Gray
try {
    & python -c "import asyncpg; print('✅ OK')" 2>&1 | Out-Null
    Write-Host "✅ Instalado e funcionando" -ForegroundColor Green
} catch {
    Write-Host "❌ Erro ao importar" -ForegroundColor Red
}

# Verificar fastapi
Write-Host "→ fastapi: " -NoNewline -ForegroundColor Gray
try {
    & python -c "import fastapi; print('✅ OK')" 2>&1 | Out-Null
    Write-Host "✅ Instalado e funcionando" -ForegroundColor Green
} catch {
    Write-Host "❌ Erro ao importar" -ForegroundColor Red
}

# Verificar sqlalchemy
Write-Host "→ sqlalchemy: " -NoNewline -ForegroundColor Gray
try {
    & python -c "import sqlalchemy; print('✅ OK')" 2>&1 | Out-Null
    Write-Host "✅ Instalado e funcionando" -ForegroundColor Green
} catch {
    Write-Host "❌ Erro ao importar" -ForegroundColor Red
}

# Sucesso!
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  SETUP COMPLETO! ✅" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Iniciar servidor:" -ForegroundColor White
Write-Host "   python -m uvicorn src.app.main:app --host 0.0.0.0 --port 8000" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Testar health check (em outro terminal):" -ForegroundColor White
Write-Host "   Invoke-WebRequest -Uri 'http://localhost:8000/health'" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Executar testes:" -ForegroundColor White
Write-Host "   cd tests\testsprite" -ForegroundColor Gray
Write-Host "   python TC001_test_get_system_health_status.py" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Consultar próximos passos:" -ForegroundColor White
Write-Host "   notepad PROXIMOS_PASSOS.md" -ForegroundColor Gray
Write-Host ""

