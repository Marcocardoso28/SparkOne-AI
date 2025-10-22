# Script para validar ambiente após setup Python 3.11

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  SparkOne - Validação de Ambiente" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$errors = 0

# 1. Verificar Python version
Write-Host "[1/8] Verificando versão Python..." -ForegroundColor Yellow
$pythonVersion = & python --version 2>&1
if ($pythonVersion -match "3\.11\.") {
    Write-Host "✅ Python $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python version incorreta: $pythonVersion" -ForegroundColor Red
    Write-Host "   Esperado: Python 3.11.x" -ForegroundColor Yellow
    $errors++
}

# 2. Verificar venv ativo
Write-Host ""
Write-Host "[2/8] Verificando ambiente virtual..." -ForegroundColor Yellow
if ($env:VIRTUAL_ENV) {
    Write-Host "✅ venv ativo: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "⚠️  venv não está ativo" -ForegroundColor Yellow
    Write-Host "   Execute: .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
    $errors++
}

# 3. Verificar asyncpg
Write-Host ""
Write-Host "[3/8] Verificando asyncpg..." -ForegroundColor Yellow
try {
    $result = & python -c "import asyncpg; print(asyncpg.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ asyncpg $result instalado" -ForegroundColor Green
    } else {
        throw "Erro ao importar"
    }
} catch {
    Write-Host "❌ asyncpg não instalado ou com erro" -ForegroundColor Red
    $errors++
}

# 4. Verificar fastapi
Write-Host ""
Write-Host "[4/8] Verificando fastapi..." -ForegroundColor Yellow
try {
    $result = & python -c "import fastapi; print(fastapi.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ fastapi $result instalado" -ForegroundColor Green
    } else {
        throw "Erro ao importar"
    }
} catch {
    Write-Host "❌ fastapi não instalado ou com erro" -ForegroundColor Red
    $errors++
}

# 5. Verificar sqlalchemy
Write-Host ""
Write-Host "[5/8] Verificando sqlalchemy..." -ForegroundColor Yellow
try {
    $result = & python -c "import sqlalchemy; print(sqlalchemy.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ sqlalchemy $result instalado" -ForegroundColor Green
    } else {
        throw "Erro ao importar"
    }
} catch {
    Write-Host "❌ sqlalchemy não instalado ou com erro" -ForegroundColor Red
    $errors++
}

# 6. Verificar structlog
Write-Host ""
Write-Host "[6/8] Verificando structlog..." -ForegroundColor Yellow
try {
    $result = & python -c "import structlog; print(structlog.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ structlog $result instalado" -ForegroundColor Green
    } else {
        throw "Erro ao importar"
    }
} catch {
    Write-Host "❌ structlog não instalado ou com erro" -ForegroundColor Red
    $errors++
}

# 7. Verificar se app pode ser importado
Write-Host ""
Write-Host "[7/8] Verificando se aplicação pode ser importada..." -ForegroundColor Yellow
try {
    & python -c "from src.app.main import app; print('OK')" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Aplicação pode ser importada" -ForegroundColor Green
    } else {
        throw "Erro ao importar"
    }
} catch {
    Write-Host "❌ Erro ao importar aplicação" -ForegroundColor Red
    Write-Host "   Verifique erros de import em src/app/main.py" -ForegroundColor Yellow
    $errors++
}

# 8. Verificar banco de dados
Write-Host ""
Write-Host "[8/8] Verificando banco de dados..." -ForegroundColor Yellow
if (Test-Path "sparkone.db") {
    Write-Host "✅ Banco de dados SQLite encontrado" -ForegroundColor Green
} else {
    Write-Host "⚠️  Banco de dados não encontrado" -ForegroundColor Yellow
    Write-Host "   Execute: python create_tables.py" -ForegroundColor Gray
}

# Resultado final
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan

if ($errors -eq 0) {
    Write-Host "  VALIDAÇÃO COMPLETA! ✅" -ForegroundColor Green
    Write-Host "  Ambiente está pronto para uso" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Próximos comandos:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Iniciar servidor:" -ForegroundColor White
    Write-Host "  python -m uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Executar testes:" -ForegroundColor White
    Write-Host "  cd tests\testsprite" -ForegroundColor Gray
    Write-Host "  python TC001_test_get_system_health_status.py" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "  VALIDAÇÃO FALHOU ❌" -ForegroundColor Red
    Write-Host "  $errors problema(s) encontrado(s)" -ForegroundColor Red
    Write-Host "================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Corrija os problemas acima e execute novamente:" -ForegroundColor Yellow
    Write-Host "  .\scripts\development\validate_environment.ps1" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

