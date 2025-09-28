# Configuração Local para Desenvolvimento

## Resumo da Configuração

Este documento descreve como configurar o ambiente local de desenvolvimento para o projeto SparkOne.

## Pré-requisitos

- Python 3.12+
- Git
- PowerShell (Windows)

## Configuração do Ambiente

### 1. Clonar o Repositório

```bash
git clone <repository-url>
cd SparkOne
```

### 2. Criar Ambiente Virtual

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instalar Dependências

```powershell
pip install .
# ou se usando pyproject.toml:
pip install -e .
```

### 4. Configurar Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env` e configure as variáveis necessárias:

```powershell
Copy-Item .env.example .env
```

Edite o arquivo `.env` com suas configurações locais.

## Configuração do Banco de Dados

### SQLite (Desenvolvimento Local)

O projeto está configurado para usar SQLite em desenvolvimento local:

1. **Configuração do Alembic**: O arquivo `alembic.ini` está configurado com:
   ```ini
   sqlalchemy.url = sqlite:///sparkone.db
   ```

2. **Executar Migrações**: 
   ```powershell
   alembic upgrade head
   ```

3. **Verificar Tabelas**:
   ```powershell
   python -c "import sqlite3; conn = sqlite3.connect('sparkone.db'); print([t[0] for t in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()]); conn.close()"
   ```

### Problemas Conhecidos e Soluções

#### Problema: Migrações não criam tabelas
**Causa**: As migrações originais usam `sa.Enum` que não é compatível com SQLite.

**Solução**: Foi criado um script `create_sqlite_tables.py` que cria as tabelas manualmente:
```powershell
python create_sqlite_tables.py
```

#### Problema: Banco SQLite com 0 bytes
**Causa**: Falha na execução das migrações devido a incompatibilidades.

**Solução**: 
1. Remover banco vazio: `Remove-Item sparkone.db -ErrorAction SilentlyContinue`
2. Executar script de criação manual: `python create_sqlite_tables.py`

## Executar a Aplicação

### Servidor de Desenvolvimento

```powershell
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Verificar Funcionamento

1. **Health Check**: 
   ```powershell
   (Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET).Content
   ```
   
   Resposta esperada:
   ```json
   {"status":"ok","timestamp":"2025-09-23T00:53:45.635173Z"}
   ```

2. **Documentação da API**: Acesse `http://localhost:8000/docs`

## Estrutura do Projeto

```
SparkOne/
├── src/app/                 # Código principal da aplicação
├── migrations/              # Migrações do banco de dados
├── scripts/                 # Scripts utilitários
├── docs/                    # Documentação
├── alembic.ini             # Configuração do Alembic
├── pyproject.toml          # Configuração do projeto Python
└── sparkone.db             # Banco SQLite (criado automaticamente)
```

## Scripts Úteis

### Verificar Estado do Banco
```powershell
python debug_sqlite.py
```

### Criar Tabelas Manualmente
```powershell
python create_sqlite_tables.py
```

### Verificar Migrações
```powershell
alembic current
alembic history
```

## Troubleshooting

### Erro: "no such table: alembic_version"
Execute o script de criação manual das tabelas:
```powershell
python create_sqlite_tables.py
```

### Erro: Migrações não executam
1. Verifique se o `alembic.ini` tem a URL correta
2. Execute as migrações manualmente:
   ```powershell
   python test_migration.py
   ```

### Servidor não inicia
1. Verifique se todas as dependências estão instaladas
2. Verifique se o ambiente virtual está ativo
3. Verifique se a porta 8000 não está em uso

## Próximos Passos

1. Configurar testes automatizados
2. Implementar CI/CD local
3. Documentar endpoints da API
4. Configurar logging estruturado

---

**Última atualização**: 23/09/2025
**Versão do banco**: 0002 (rename metadata to extra_data)