# SparkOne - Guia de Desenvolvimento

**Versão:** v1.1.0  
**Data:** Janeiro 2025  

---

## 🎯 Visão Geral

Este guia fornece informações para desenvolvedores que trabalham no projeto SparkOne, incluindo setup do ambiente, padrões de código e processos de desenvolvimento.

---

## 🚀 Setup do Ambiente

### 1. Pré-requisitos

```bash
# Python 3.11+
python --version

# Node.js 18+ (para ferramentas de desenvolvimento)
node --version

# Docker e Docker Compose
docker --version
docker-compose --version

# Git
git --version
```

### 2. Clone e Setup

```bash
# Clone do repositório
git clone https://github.com/seu-usuario/sparkone.git
cd sparkone

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -e .

# Instalar dependências de desenvolvimento
pip install -r requirements-dev.txt

# Configurar pre-commit hooks
pre-commit install
```

### 3. Configuração do Ambiente

```bash
# Copiar arquivo de configuração
cp config/development.env .env

# Configurar variáveis de ambiente
nano .env
```

**Variáveis importantes para desenvolvimento:**

```env
# Ambiente
ENVIRONMENT=development
DEBUG=true

# Banco de dados (SQLite para desenvolvimento)
DATABASE_URL=sqlite+aiosqlite:///./sparkone.db

# Redis (opcional para desenvolvimento)
REDIS_URL=redis://localhost:6379

# APIs externas (opcional)
EVOLUTION_API_URL=http://localhost:8080
NOTION_API_KEY=your_notion_key
```

### 4. Inicializar Banco de Dados

```bash
# Executar migrações
alembic upgrade head

# Criar dados de teste (opcional)
python scripts/seed_test_data.py
```

---

## 🧪 Executando Testes

### 1. Testes Unitários

```bash
# Executar todos os testes
pytest

# Executar com coverage
pytest --cov=src/app --cov-report=html

# Executar testes específicos
pytest tests/test_auth.py

# Executar em modo verbose
pytest -v
```

### 2. Testes de Integração

```bash
# Executar testes de integração
pytest tests/integration/

# Executar com banco de dados de teste
pytest --db-url=sqlite+aiosqlite:///./test.db
```

### 3. Testes End-to-End

```bash
# Executar testes E2E com TestSprite
node C:\Users\marco\AppData\Local\npm-cache\_npx\8ddf6bea01b2519d\node_modules\@testsprite\testsprite-mcp\dist\index.js generateCodeAndExecute

# Executar testes Playwright
pytest tests/e2e/
```

### 4. Linting e Formatação

```bash
# Executar linting
ruff check src/

# Executar formatação
black src/

# Executar type checking
mypy src/

# Executar tudo
make lint
make format
make type-check
```

---

## 🏗️ Estrutura do Projeto

### Arquitetura

```
src/app/
├── agents/          # Agentes de IA e orquestração
├── channels/        # Adaptadores de entrada (WhatsApp, Web)
├── core/           # Infraestrutura base (config, db, cache)
├── models/         # Schemas Pydantic e modelos SQLAlchemy
├── routers/        # Endpoints da API REST
├── services/       # Lógica de negócio
├── middleware/     # Middleware customizado
└── tests/          # Testes automatizados
```

### Padrões de Código

#### 1. Nomenclatura

```python
# Classes: PascalCase
class TaskService:
    pass

# Funções e variáveis: snake_case
def create_task(task_data: dict) -> Task:
    pass

# Constantes: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3

# Arquivos: snake_case
task_service.py
auth_middleware.py
```

#### 2. Imports

```python
# Ordem de imports
import os
import sys
from typing import List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from pydantic import BaseModel

from src.app.core.config import get_settings
from src.app.models.db.tasks import TaskRecord
```

#### 3. Type Hints

```python
# Sempre usar type hints
def process_message(
    message: str,
    channel: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    pass

# Para classes
class TaskResponse(BaseModel):
    id: int
    title: str
    status: TaskStatus
    created_at: datetime
```

---

## 🔧 Desenvolvimento de Features

### 1. Criando um Novo Endpoint

```python
# 1. Criar schema Pydantic
class TaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None

# 2. Criar endpoint no router
@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    request: TaskCreateRequest,
    session: AsyncSession = Depends(get_db_session)
) -> TaskResponse:
    # Implementação
    pass

# 3. Criar testes
def test_create_task():
    # Teste unitário
    pass
```

### 2. Adicionando Novo Serviço

```python
# 1. Criar serviço
class NotificationService:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    async def send_notification(
        self, 
        user_id: str, 
        message: str
    ) -> bool:
        # Implementação
        pass

# 2. Registrar no container de DI
def get_notification_service() -> NotificationService:
    return NotificationService(get_settings())

# 3. Usar em endpoints
@router.post("/notify")
async def send_notification(
    notification_service: NotificationService = Depends(get_notification_service)
):
    pass
```

### 3. Trabalhando com Banco de Dados

```python
# 1. Criar modelo SQLAlchemy
class NotificationRecord(Base):
    __tablename__ = "notifications"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

# 2. Criar migração
alembic revision --autogenerate -m "Add notifications table"

# 3. Implementar repositório
async def create_notification(
    session: AsyncSession,
    user_id: str,
    message: str
) -> NotificationRecord:
    notification = NotificationRecord(
        user_id=user_id,
        message=message,
        sent_at=datetime.now(UTC)
    )
    session.add(notification)
    await session.commit()
    return notification
```

---

## 🧪 Estratégias de Teste

### 1. Testes Unitários

```python
# Teste de serviço
@pytest.mark.asyncio
async def test_task_service_create_task():
    # Arrange
    service = TaskService(mock_session)
    task_data = {"title": "Test Task", "description": "Test Description"}
    
    # Act
    result = await service.create_task(task_data)
    
    # Assert
    assert result.title == "Test Task"
    assert result.status == TaskStatus.PENDING
```

### 2. Testes de Integração

```python
# Teste de endpoint
@pytest.mark.asyncio
async def test_create_task_endpoint(client: AsyncClient):
    # Arrange
    task_data = {
        "title": "Integration Test Task",
        "description": "Test Description"
    }
    
    # Act
    response = await client.post("/tasks", json=task_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["title"] == task_data["title"]
```

### 3. Mocks e Fixtures

```python
# Fixture para cliente de teste
@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# Mock de serviço externo
@pytest.fixture
def mock_notification_service():
    with patch('src.app.services.notification.NotificationService') as mock:
        mock.return_value.send_notification = AsyncMock(return_value=True)
        yield mock
```

---

## 🔄 Processo de Desenvolvimento

### 1. Fluxo de Trabalho

```bash
# 1. Criar branch para feature
git checkout -b feature/nova-funcionalidade

# 2. Desenvolver feature
# ... código ...

# 3. Executar testes
pytest
make lint
make type-check

# 4. Commit com mensagem descritiva
git add .
git commit -m "feat: adicionar endpoint para notificações

- Implementar POST /notifications
- Adicionar validação de dados
- Criar testes unitários e de integração"

# 5. Push e criar PR
git push origin feature/nova-funcionalidade
```

### 2. Convenções de Commit

```bash
# Formato: tipo(escopo): descrição

# Tipos:
feat: nova funcionalidade
fix: correção de bug
docs: documentação
style: formatação
refactor: refatoração
test: testes
chore: tarefas de manutenção

# Exemplos:
feat(auth): implementar 2FA
fix(api): corrigir validação de email
docs(readme): atualizar instruções de instalação
test(tasks): adicionar testes para CRUD
```

### 3. Code Review

- **Revisar** lógica e implementação
- **Verificar** testes e coverage
- **Validar** padrões de código
- **Testar** funcionalidade localmente
- **Aprovar** se atender critérios

---

## 📊 Ferramentas de Desenvolvimento

### 1. Debugging

```python
# Debug com breakpoints
import pdb; pdb.set_trace()

# Logging estruturado
import structlog
logger = structlog.get_logger()
logger.info("Debug info", user_id=user_id, action="create_task")

# Profiling de queries
from src.app.core.profiler import profile_query

@profile_query
async def slow_function():
    # Função que será profileada
    pass
```

### 2. Monitoramento Local

```bash
# Ver logs em tempo real
docker-compose logs -f api

# Verificar métricas
curl http://localhost:8000/metrics

# Health checks
curl http://localhost:8000/health
```

### 3. Ferramentas de Qualidade

```bash
# Análise de segurança
bandit -r src/

# Análise de dependências
safety check

# Análise de complexidade
radon cc src/ --min B

# Análise de duplicação
pylint --disable=all --enable=duplicate-code src/
```

---

## 🚀 Deploy e CI/CD

### 1. GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          pytest --cov=src/app
          make lint
          make type-check
```

### 2. Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.270
    hooks:
      - id: ruff
        args: [--fix]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
```

---

## 📚 Recursos e Referências

### Documentação

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

### Ferramentas

- [pytest](https://docs.pytest.org/) - Framework de testes
- [ruff](https://docs.astral.sh/ruff/) - Linter rápido
- [black](https://black.readthedocs.io/) - Formatador de código
- [mypy](https://mypy.readthedocs.io/) - Type checker

### Padrões

- [PEP 8](https://peps.python.org/pep-0008/) - Style guide
- [PEP 484](https://peps.python.org/pep-0484/) - Type hints
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit messages

---

**Última atualização:** Janeiro 2025  
**Versão:** 1.1.0
