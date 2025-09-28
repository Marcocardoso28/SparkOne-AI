#!/usr/bin/env python3
"""Script para corrigir imports relativos para absolutos no projeto SparkOne."""

import re
from pathlib import Path
from typing import Dict, List, Tuple


def find_python_files(root_dir: Path) -> List[Path]:
    """Encontra todos os arquivos Python no diretório src."""
    return list(root_dir.rglob("*.py"))


def analyze_import_structure(file_path: Path, src_root: Path) -> Dict[str, str]:
    """Analisa a estrutura de imports de um arquivo."""
    relative_path = file_path.relative_to(src_root)
    parts = relative_path.parts[:-1]  # Remove o nome do arquivo
    
    # Constrói o caminho do módulo atual
    if parts:
        current_module = ".".join(parts)
    else:
        current_module = ""
    
    return {
        "current_module": current_module,
        "file_path": str(file_path),
        "relative_path": str(relative_path)
    }


def convert_relative_import(import_line: str, current_module: str) -> str:
    """Converte um import relativo para absoluto."""
    # Padrão para imports relativos: from ..module import something
    pattern = r'^(\s*)from\s+(\.+)([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import\s+(.+)$'
    match = re.match(pattern, import_line.strip())
    
    if not match:
        return import_line
    
    indent, dots, module_path, imports = match.groups()
    
    # Calcula quantos níveis subir
    levels_up = len(dots) - 1
    
    # Divide o módulo atual em partes
    current_parts = current_module.split('.') if current_module else []
    
    # Remove os níveis necessários
    if levels_up >= len(current_parts):
        # Se subir mais níveis do que existem, vai para a raiz
        base_module = "src"
    else:
        base_parts = current_parts[:-levels_up] if levels_up > 0 else current_parts
        base_module = "src." + ".".join(base_parts) if base_parts else "src"
    
    # Constrói o import absoluto
    if module_path:
        absolute_module = f"{base_module}.{module_path}"
    else:
        absolute_module = base_module
    
    return f"{indent}from {absolute_module} import {imports}"


def fix_file_imports(file_path: Path, src_root: Path) -> Tuple[bool, List[str]]:
    """Corrige os imports relativos em um arquivo."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        analysis = analyze_import_structure(file_path, src_root)
        current_module = analysis["current_module"]
        
        modified = False
        changes = []
        new_lines = []
        
        for i, line in enumerate(lines, 1):
            # Verifica se é um import relativo
            if re.match(r'^\s*from\s+\.\.', line.strip()):
                original_line = line.rstrip()
                new_line = convert_relative_import(line, current_module)
                
                if new_line != line:
                    modified = True
                    changes.append(f"Linha {i}: '{original_line.strip()}' -> '{new_line.strip()}'")
                    new_lines.append(new_line + '\n')
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Escreve o arquivo modificado
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
        
        return modified, changes
    
    except Exception as e:
        return False, [f"Erro ao processar arquivo: {e}"]


def main():
    """Função principal."""
    project_root = Path(__file__).parent
    src_root = project_root / "src"
    
    if not src_root.exists():
        print(f"❌ Diretório src não encontrado: {src_root}")
        return
    
    print("🔍 Procurando arquivos Python com imports relativos...")
    
    python_files = find_python_files(src_root)
    total_files = len(python_files)
    modified_files = 0
    total_changes = 0
    
    print(f"📁 Encontrados {total_files} arquivos Python")
    print()
    
    for file_path in python_files:
        try:
            modified, changes = fix_file_imports(file_path, src_root)
            
            if modified:
                modified_files += 1
                total_changes += len(changes)
                relative_path = file_path.relative_to(project_root)
                
                print(f"✅ {relative_path}")
                for change in changes:
                    print(f"   {change}")
                print()
        
        except Exception as e:
            relative_path = file_path.relative_to(project_root)
            print(f"❌ Erro em {relative_path}: {e}")
    
    print("=" * 60)
    print(f"📊 Resumo:")
    print(f"   • Arquivos processados: {total_files}")
    print(f"   • Arquivos modificados: {modified_files}")
    print(f"   • Total de mudanças: {total_changes}")
    
    if modified_files > 0:
        print(f"\n✅ Correção de imports relativos concluída!")
        print(f"💡 Execute 'ruff check .' para verificar se há outros problemas")
    else:
        print(f"\n✨ Nenhum import relativo encontrado para corrigir")


if __name__ == "__main__":
    main()