#!/usr/bin/env python3
"""Script consolidado de setup para desenvolvimento."""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> bool:
    """Executa um comando e retorna True se bem-sucedido."""
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True,
                                capture_output=True, text=True)
        print(f"✅ {cmd[0]} executado com sucesso")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar {cmd[0]}: {e.stderr}")
        return False


def check_python_version():
    """Verifica se a versão do Python é compatível."""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ é necessário")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detectado")


def setup_venv():
    """Configura ambiente virtual."""
    venv_path = Path("venv")
    if not venv_path.exists():
        print("📦 Criando ambiente virtual...")
        if not run_command([sys.executable, "-m", "venv", "venv"]):
            return False
    else:
        print("✅ Ambiente virtual já existe")
    return True


def install_dependencies():
    """Instala dependências do projeto."""
    print("📦 Instalando dependências...")

    # Determinar o executável do pip no venv
    if os.name == 'nt':  # Windows
        pip_path = Path("venv/Scripts/pip.exe")
    else:  # Unix-like
        pip_path = Path("venv/bin/pip")

    if not pip_path.exists():
        print("❌ pip não encontrado no ambiente virtual")
        return False

    # Instalar dependências
    commands = [
        [str(pip_path), "install", "--upgrade", "pip"],
        [str(pip_path), "install", "-e", "."],
        [str(pip_path), "install", "-e", ".[dev]"],
    ]

    for cmd in commands:
        if not run_command(cmd):
            return False

    return True


def setup_database():
    """Configura banco de dados."""
    print("🗄️ Configurando banco de dados...")

    # Criar diretório de dados se não existir
    data_dir = Path("data/databases")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Executar migrações
    if os.name == 'nt':  # Windows
        python_path = Path("venv/Scripts/python.exe")
    else:  # Unix-like
        python_path = Path("venv/bin/python")

    if not python_path.exists():
        print("❌ Python não encontrado no ambiente virtual")
        return False

    # Executar script de criação de tabelas
    create_tables_script = Path("scripts/tools/create_tables.py")
    if create_tables_script.exists():
        if not run_command([str(python_path), str(create_tables_script)]):
            return False
    else:
        print("⚠️ Script de criação de tabelas não encontrado")

    return True


def setup_environment():
    """Configura variáveis de ambiente."""
    print("🔧 Configurando ambiente...")

    env_file = Path(".env.development")
    if not env_file.exists():
        example_file = Path("config/env.example")
        if example_file.exists():
            print("📝 Copiando arquivo de exemplo...")
            import shutil
            shutil.copy(example_file, env_file)
            print(f"✅ Arquivo {env_file} criado")
            print("⚠️ Edite o arquivo .env.development com suas configurações")
        else:
            print("⚠️ Arquivo de exemplo não encontrado")
    else:
        print("✅ Arquivo .env.development já existe")

    return True


def run_tests():
    """Executa testes básicos."""
    print("🧪 Executando testes...")

    if os.name == 'nt':  # Windows
        python_path = Path("venv/Scripts/python.exe")
    else:  # Unix-like
        python_path = Path("venv/bin/python")

    # Executar testes básicos
    test_commands = [
        [str(python_path), "-m", "pytest", "tests/unit/", "-v", "--tb=short"],
    ]

    for cmd in test_commands:
        if not run_command(cmd):
            print("⚠️ Alguns testes falharam, mas o setup continuará")

    return True


def main():
    """Função principal."""
    print("🚀 Configurando ambiente de desenvolvimento do SparkOne...")
    print()

    # Verificar se estamos no diretório correto
    if not Path("pyproject.toml").exists():
        print("❌ Execute este script no diretório raiz do projeto")
        sys.exit(1)

    steps = [
        ("Verificando versão do Python", check_python_version),
        ("Configurando ambiente virtual", setup_venv),
        ("Instalando dependências", install_dependencies),
        ("Configurando banco de dados", setup_database),
        ("Configurando ambiente", setup_environment),
        ("Executando testes", run_tests),
    ]

    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            print(f"❌ Falha em: {step_name}")
            sys.exit(1)

    print("\n🎉 Setup concluído com sucesso!")
    print("\n📝 Próximos passos:")
    print("1. Edite o arquivo .env.development com suas configurações")
    print("2. Execute: python -m uvicorn src.app.main:app --reload")
    print("3. Acesse: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
