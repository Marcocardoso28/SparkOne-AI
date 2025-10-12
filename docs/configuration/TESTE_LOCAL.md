# 🚀 Guia para Testar SparkOne Localmente

## ⚠️ Situação Atual
O Docker Desktop não está rodando no seu sistema. Vamos configurar o SparkOne para rodar localmente sem Docker.

## 📋 Pré-requisitos

### 1. Python 3.11+
```powershell
python --version
```

### 2. PostgreSQL Local
**Opção A: Instalar PostgreSQL**
- Baixe em: https://www.postgresql.org/download/windows/
- Configure usuário: `sparkone`, senha: `sparkone`, database: `sparkone`

**Opção B: Docker apenas para banco (se Docker funcionar)**
```powershell
docker run -d --name sparkone-postgres -p 5432:5432 -e POSTGRES_DB=sparkone -e POSTGRES_USER=sparkone -e POSTGRES_PASSWORD=sparkone postgres:15
```

### 3. Redis Local
**Opção A: Instalar Redis**
- Baixe em: https://github.com/microsoftarchive/redis/releases
- Ou use chocolatey: `choco install redis-64`

**Opção B: Docker apenas para Redis**
```powershell
docker run -d --name sparkone-redis -p 6379:6379 redis:7-alpine
```

## 🔧 Configuração Rápida

### 1. Criar Ambiente Virtual
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Instalar Dependências
```powershell
pip install --upgrade pip
pip install -e .[dev]
```

### 3. Configurar .env para Local
Edite o arquivo `.env` e ajuste as URLs:
```env
DATABASE_URL=postgresql+asyncpg://sparkone:sparkone@localhost:5432/sparkone
VECTOR_STORE_URL=postgresql://sparkone:sparkone@localhost:5432/sparkone
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=development
DEBUG=true
```

### 4. Executar Migrações
```powershell
alembic upgrade head
```

### 5. Iniciar Servidor
```powershell
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🌐 URLs de Teste

Após iniciar o servidor:

- **API Principal**: http://localhost:8000
- **Documentação**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Profiler Stats**: http://localhost:8000/profiler/stats
- **Profiler Reports**: http://localhost:8000/profiler/reports
- **Interface Web**: http://localhost:8000/web

## 🧪 Testes Básicos

### 1. Health Check
```powershell
curl http://localhost:8000/health
```

### 2. Documentação OpenAPI
Acesse: http://localhost:8000/docs

### 3. Profiler de Performance
```powershell
curl http://localhost:8000/profiler/stats
```

### 4. Criar Canal de Teste
```powershell
curl -X POST http://localhost:8000/channels/ -H "Content-Type: application/json" -d '{"name": "teste", "description": "Canal de teste"}'
```

## 🐛 Resolução de Problemas

### Erro de Conexão com Banco
- Verifique se PostgreSQL está rodando: `Get-Service postgresql*`
- Teste conexão: `psql -h localhost -U sparkone -d sparkone`

### Erro de Conexão com Redis
- Verifique se Redis está rodando: `Get-Process redis-server`
- Teste conexão: `redis-cli ping`

### Erro de Dependências
```powershell
pip install --upgrade pip setuptools wheel
pip install -e .[dev] --force-reinstall
```

### Erro de Migrações
```powershell
# Reset do banco (CUIDADO: apaga dados)
alembic downgrade base
alembic upgrade head
```

## 📊 Monitoramento

### Logs da Aplicação
Os logs aparecerão no terminal onde você executou o uvicorn.

### Métricas de Performance
- Acesse: http://localhost:8000/profiler/stats
- Relatórios: http://localhost:8000/profiler/reports

### Queries Lentas
- Endpoint: http://localhost:8000/profiler/slow-queries

## 🚀 Próximos Passos

1. **Teste Funcionalidades**:
   - Criar canais
   - Enviar mensagens
   - Testar embeddings
   - Verificar profiler

2. **Configurar Chaves de API**:
   - OpenAI API Key no `.env`
   - Outras integrações necessárias

3. **Executar Testes**:
   ```powershell
   pytest
   ```

4. **Verificar Qualidade**:
   ```powershell
   black src --check
   ruff check src
   mypy src
   ```

## 📝 Notas Importantes

- ✅ Sistema de profiling implementado
- ✅ Observabilidade avançada
- ✅ Testes E2E configurados
- ✅ Documentação OpenAPI completa
- ⚠️ Docker Desktop precisa ser configurado para uso completo
- 🔧 Ambiente local funcional para desenvolvimento

---

**Dica**: Se Docker Desktop estiver funcionando, use `docker compose up --build` para ambiente completo.