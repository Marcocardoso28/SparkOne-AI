# Script para iniciar o servidor SparkOne
Write-Host "Iniciando SparkOne..." -ForegroundColor Green
Write-Host "Servidor estara disponivel em: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar o servidor`n" -ForegroundColor Yellow

python -m uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

