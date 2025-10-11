#!/usr/bin/env python3
"""Script de limpeza e manutenção do projeto."""

import os
import shutil
import sys
from pathlib import Path
from typing import List, Set


def find_files(pattern: str, exclude_dirs: Set[str] = None) -> List[Path]:
    """Encontra arquivos que correspondem ao padrão."""
    if exclude_dirs is None:
        exclude_dirs = {'.git', 'venv', '__pycache__',
                        '.pytest_cache', 'node_modules'}

    files = []
    for root, dirs, filenames in os.walk('.'):
        # Remover diretórios excluídos
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for filename in filenames:
            if filename.endswith(pattern):
                files.append(Path(root) / filename)

    return files


def clean_python_cache():
    """Limpa cache do Python."""
    print("🧹 Limpando cache do Python...")

    cache_files = find_files('.pyc')
    cache_dirs = []

    for root, dirs, filenames in os.walk('.'):
        if '__pycache__' in dirs:
            cache_dirs.append(Path(root) / '__pycache__')

    removed_files = 0
    for file_path in cache_files:
        try:
            file_path.unlink()
            removed_files += 1
        except OSError:
            pass

    removed_dirs = 0
    for dir_path in cache_dirs:
        try:
            shutil.rmtree(dir_path)
            removed_dirs += 1
        except OSError:
            pass

    print(
        f"✅ Removidos {removed_files} arquivos .pyc e {removed_dirs} diretórios __pycache__")


def clean_pytest_cache():
    """Limpa cache do pytest."""
    print("🧹 Limpando cache do pytest...")

    pytest_dirs = [
        Path('.pytest_cache'),
        Path('htmlcov'),
        Path('.coverage'),
    ]

    removed = 0
    for dir_path in pytest_dirs:
        if dir_path.exists():
            try:
                if dir_path.is_file():
                    dir_path.unlink()
                else:
                    shutil.rmtree(dir_path)
                removed += 1
            except OSError:
                pass

    print(f"✅ Removidos {removed} arquivos/diretórios de cache do pytest")


def clean_temp_files():
    """Limpa arquivos temporários."""
    print("🧹 Limpando arquivos temporários...")

    temp_patterns = ['.tmp', '.temp', '.log', '.pid', '.bak', '.backup']
    removed = 0

    for pattern in temp_patterns:
        temp_files = find_files(pattern)
        for file_path in temp_files:
            try:
                file_path.unlink()
                removed += 1
            except OSError:
                pass

    print(f"✅ Removidos {removed} arquivos temporários")


def clean_database_files():
    """Limpa arquivos de banco de dados locais."""
    print("🧹 Limpando arquivos de banco de dados...")

    db_patterns = ['.db', '.db-shm', '.db-wal', '.db-journal']
    removed = 0

    for pattern in db_patterns:
        db_files = find_files(pattern)
        for file_path in db_files:
            # Não remover arquivos na pasta data/databases (podem ser importantes)
            if 'data/databases' not in str(file_path):
                try:
                    file_path.unlink()
                    removed += 1
                except OSError:
                    pass

    print(f"✅ Removidos {removed} arquivos de banco de dados")


def clean_uploads():
    """Limpa uploads temporários."""
    print("🧹 Limpando uploads temporários...")

    uploads_dir = Path('data/uploads')
    if uploads_dir.exists():
        removed = 0
        for file_path in uploads_dir.iterdir():
            if file_path.is_file() and file_path.name != '.gitkeep':
                try:
                    file_path.unlink()
                    removed += 1
                except OSError:
                    pass

        print(f"✅ Removidos {removed} arquivos de upload")
    else:
        print("✅ Diretório de uploads não existe")


def clean_backups():
    """Limpa backups antigos."""
    print("🧹 Limpando backups antigos...")

    backups_dir = Path('data/backups')
    if backups_dir.exists():
        removed = 0
        for file_path in backups_dir.iterdir():
            if file_path.is_file() and file_path.suffix == '.sql':
                # Manter apenas os últimos 7 backups
                try:
                    file_path.unlink()
                    removed += 1
                except OSError:
                    pass

        print(f"✅ Removidos {removed} backups antigos")
    else:
        print("✅ Diretório de backups não existe")


def clean_reports():
    """Limpa relatórios antigos."""
    print("🧹 Limpando relatórios antigos...")

    reports_dir = Path('reports')
    if reports_dir.exists():
        removed = 0
        for file_path in reports_dir.iterdir():
            if file_path.is_file() and file_path.suffix in ['.json', '.html', '.md']:
                # Manter apenas os últimos 30 relatórios
                try:
                    file_path.unlink()
                    removed += 1
                except OSError:
                    pass

        print(f"✅ Removidos {removed} relatórios antigos")
    else:
        print("✅ Diretório de relatórios não existe")


def clean_empty_dirs():
    """Remove diretórios vazios."""
    print("🧹 Removendo diretórios vazios...")

    removed = 0
    for root, dirs, files in os.walk('.', topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                if not any(dir_path.iterdir()):  # Diretório vazio
                    dir_path.rmdir()
                    removed += 1
            except OSError:
                pass

    print(f"✅ Removidos {removed} diretórios vazios")


def show_disk_usage():
    """Mostra uso de disco."""
    print("📊 Uso de disco:")

    total_size = 0
    for root, dirs, files in os.walk('.'):
        for filename in files:
            file_path = Path(root) / filename
            try:
                total_size += file_path.stat().st_size
            except OSError:
                pass

    # Converter para MB
    size_mb = total_size / (1024 * 1024)
    print(f"✅ Tamanho total do projeto: {size_mb:.2f} MB")


def main():
    """Função principal."""
    print("🧹 Iniciando limpeza do projeto SparkOne...")
    print()

    # Verificar se estamos no diretório correto
    if not Path("pyproject.toml").exists():
        print("❌ Execute este script no diretório raiz do projeto")
        sys.exit(1)

    cleanup_functions = [
        clean_python_cache,
        clean_pytest_cache,
        clean_temp_files,
        clean_database_files,
        clean_uploads,
        clean_backups,
        clean_reports,
        clean_empty_dirs,
    ]

    for cleanup_func in cleanup_functions:
        try:
            cleanup_func()
        except Exception as e:
            print(f"⚠️ Erro em {cleanup_func.__name__}: {e}")

    print()
    show_disk_usage()
    print("\n🎉 Limpeza concluída!")


if __name__ == "__main__":
    main()
