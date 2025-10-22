# Script para iniciar o servidor FastAPI para testes
Write-Host "Iniciando servidor FastAPI na porta 8000..." -ForegroundColor Green

# Ativar ambiente virtual se existir
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
}

# Iniciar servidor
python -m uvicorn src.app.main:app --host 0.0.0.0 --port 8000

