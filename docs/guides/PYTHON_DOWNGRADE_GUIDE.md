# Guia de Downgrade Python 3.14 → 3.11

**Status**: CRÍTICO - Necessário para continuar desenvolvimento  
**Razão**: `asyncpg` não compila em Python 3.14  
**Data**: 21 de Outubro de 2025

## 🚨 Problema Identificado

O projeto SparkOne está rodando em **Python 3.14.0**, mas:
- ❌ `asyncpg` (driver PostgreSQL async) não compila
- ❌ API C interna mudou (funções `_PyUnicodeWriter_*` deprecated)
- ❌ Não há wheels pré-compilados disponíveis
- ❌ Servidor FastAPI não pode iniciar

## ✅ Solução: Python 3.11 LTS

Python 3.11 é a versão **recomendada para produção**:
- ✅ LTS (Long Term Support)
- ✅ Suporte completo para `asyncpg`
- ✅ Todas as dependências funcionam
- ✅ Testado e estável no ecossistema Python

## 📋 Passo a Passo

### 1. Download Python 3.11

**Link oficial**: https://www.python.org/downloads/release/python-3119/

**Para Windows 64-bit**:
- Baixe: `Windows installer (64-bit)`
- Arquivo: `python-3.11.9-amd64.exe`

### 2. Instalação

```powershell
# Executar instalador
# ✅ Marcar: "Add Python 3.11 to PATH"
# ✅ Marcar: "Install for all users" (opcional)
# ✅ Escolher: "Customize installation"
# ✅ Marcar: "pip", "py launcher"
```

**Diretório sugerido**: `C:\Python311\`

### 3. Verificar Instalação

```powershell
# Verificar versão instalada
python3.11 --version
# Deve mostrar: Python 3.11.9

# Verificar pip
python3.11 -m pip --version
```

### 4. Criar Novo Ambiente Virtual

```powershell
# Navegar para o projeto
cd C:\Users\marco\Macspark\SparkOne

# Remover ambiente virtual antigo (Python 3.14)
Remove-Item -Recurse -Force venv

# Criar novo ambiente com Python 3.11
python3.11 -m venv venv

# Ativar ambiente
.\venv\Scripts\Activate.ps1
```

### 5. Verificar Ambiente Virtual

```powershell
# Deve mostrar Python 3.11.x
python --version

# Deve estar dentro do venv
# Prompt deve mostrar: (venv) PS C:\Users\marco\Macspark\SparkOne>
```

### 6. Instalar Dependências

```powershell
# Atualizar pip primeiro
python -m pip install --upgrade pip

# Instalar dependências do projeto
pip install -e .

# Verificar asyncpg instalou corretamente
pip show asyncpg
# Deve mostrar: Version: 0.30.0
```

### 7. Validar Instalação

```powershell
# Testar importação básica
python -c "import asyncpg; print('asyncpg OK')"
python -c "import fastapi; print('fastapi OK')"
python -c "import sqlalchemy; print('sqlalchemy OK')"

# Deve mostrar:
# asyncpg OK
# fastapi OK
# sqlalchemy OK
```

### 8. Iniciar Servidor

```powershell
# Iniciar servidor FastAPI
python -m uvicorn src.app.main:app --host 0.0.0.0 --port 8000

# Aguardar mensagem:
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 9. Testar Health Check

```powershell
# Em outro terminal
Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET

# Deve retornar: StatusCode: 200
```

### 10. Executar Testes

```powershell
# Executar testes TestSprite
cd tests\testsprite
python TC001_test_get_system_health_status.py
python TC008_test_user_login_with_valid_credentials.py

# Todos devem passar ✅
```

## 🔧 Solução de Problemas

### Problema: Python 3.11 não encontrado

```powershell
# Adicionar manualmente ao PATH
$env:Path += ";C:\Python311\;C:\Python311\Scripts\"

# Verificar
python3.11 --version
```

### Problema: pip não funciona

```powershell
# Reinstalar pip
python3.11 -m ensurepip --upgrade
python3.11 -m pip install --upgrade pip
```

### Problema: asyncpg ainda não compila

```powershell
# Instalar Visual C++ Build Tools (se necessário)
# Link: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Ou tentar versão específica
pip install asyncpg==0.29.0
```

### Problema: ImportError após instalação

```powershell
# Limpar cache Python
Remove-Item -Recurse -Force __pycache__
Remove-Item -Recurse -Force src\**\__pycache__

# Reinstalar em modo editable
pip install -e . --force-reinstall --no-cache-dir
```

## 📊 Checklist de Validação

Após o downgrade, verificar:

- [ ] ✅ Python 3.11.x instalado
- [ ] ✅ Ambiente virtual criado com Python 3.11
- [ ] ✅ Todas as dependências instaladas (incluindo `asyncpg`)
- [ ] ✅ Servidor FastAPI inicia sem erros
- [ ] ✅ Health check responde (200 OK)
- [ ] ✅ Testes TestSprite executam
- [ ] ✅ Banco de dados conecta (PostgreSQL ou SQLite)

## 🎯 Próximos Passos Após Downgrade

1. **Validar Servidor**
   ```powershell
   python -m uvicorn src.app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Executar TestSprite Completo**
   ```powershell
   cd tests\testsprite
   # Executar todos os 10 testes
   ```

3. **Continuar com Plano de Validação**
   - Code review com Gemini CLI
   - Completar Fase 1
   - Iniciar Fase 2 (Frontend)

## ⚠️ Notas Importantes

### Manter Python 3.11 para Produção

Python 3.11 deve ser mantido para:
- ✅ Desenvolvimento local
- ✅ Ambiente de staging
- ✅ Ambiente de produção
- ✅ CI/CD pipelines

### Não Usar Python 3.14

Python 3.14 é muito recente:
- ❌ Lançado em Outubro 2025
- ❌ Ecossistema ainda não tem suporte completo
- ❌ Muitas bibliotecas não compatíveis
- ❌ Não recomendado para produção

### Configurar `pyproject.toml`

Atualizar restrição de versão Python:

```toml
[project]
requires-python = ">=3.11,<3.14"
```

Isso garante que o projeto só funcione com Python 3.11-3.13.

## 📝 Referências

- Python 3.11 Downloads: https://www.python.org/downloads/
- asyncpg Documentation: https://magicstack.github.io/asyncpg/
- FastAPI Async SQL Databases: https://fastapi.tiangolo.com/tutorial/sql-databases/
- SQLAlchemy Async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

---

**Autor**: AI Assistant  
**Data**: 21/10/2025  
**Status**: Guia completo pronto para uso

