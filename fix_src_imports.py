#!/usr/bin/env python3
"""
Script para corrigir imports que usam src.app quando executados de dentro do diretório src.
Converte imports como 'from src.app.config import Settings' para 'from app.config import Settings'
quando o arquivo está dentro do diretório src.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


def find_python_files(directory: Path) -> List[Path]:
    """Encontra todos os arquivos Python no diretório."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Ignora diretórios específicos
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache', 'venv', '.venv'}]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files


def fix_src_imports_in_file(file_path: Path) -> Tuple[bool, int]:
    """
    Corrige imports que usam src.app em arquivos dentro do diretório src.
    
    Returns:
        Tuple[bool, int]: (arquivo_foi_modificado, numero_de_mudancas)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            print(f"Erro ao ler {file_path}: {e}")
            return False, 0
    
    original_content = content
    changes = 0
    
    # Padrões para encontrar imports que usam src.app
    patterns = [
        # from src.app.module import something
        (r'from src\.app\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)', r'from app.\1'),
        # import src.app.module
        (r'import src\.app\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)', r'import app.\1'),
    ]
    
    for pattern, replacement in patterns:
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            content = new_content
            changes += count
            print(f"  - Substituído {count} ocorrências de '{pattern}' por '{replacement}'")
    
    if changes > 0:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        except Exception as e:
            print(f"Erro ao escrever {file_path}: {e}")
            return False, 0
    
    return False, 0


def main():
    """Função principal."""
    src_dir = Path("src")
    
    if not src_dir.exists():
        print("Diretório 'src' não encontrado!")
        return
    
    print("🔍 Procurando arquivos Python no diretório src...")
    python_files = find_python_files(src_dir)
    print(f"Encontrados {len(python_files)} arquivos Python")
    
    total_files_modified = 0
    total_changes = 0
    
    print("\n🔧 Corrigindo imports src.app...")
    for file_path in python_files:
        print(f"\nProcessando: {file_path}")
        
        modified, changes = fix_src_imports_in_file(file_path)
        
        if modified:
            total_files_modified += 1
            total_changes += changes
            print(f"  ✅ Arquivo modificado com {changes} mudanças")
        else:
            print(f"  ⏭️  Nenhuma mudança necessária")
    
    print(f"\n✨ Concluído!")
    print(f"📊 Resumo:")
    print(f"  - Arquivos modificados: {total_files_modified}")
    print(f"  - Total de mudanças: {total_changes}")
    
    if total_changes > 0:
        print(f"\n💡 Sugestão: Execute 'ruff check .' para verificar outros problemas")


if __name__ == "__main__":
    main()