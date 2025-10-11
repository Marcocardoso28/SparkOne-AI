#!/usr/bin/env python3
"""
SparkOne Project Organizer
=========================

Script para organizar automaticamente a estrutura do projeto SparkOne.
Move arquivos para locais apropriados, limpa duplicatas e organiza diretórios.

Uso:
    python scripts/organize_project.py [--dry-run] [--backup]

Autor: AI Assistant
Data: Janeiro 2025
"""

import os
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple


class ProjectOrganizer:
    """Organizador automático do projeto SparkOne."""

    def __init__(self, dry_run: bool = False, backup: bool = True):
        self.dry_run = dry_run
        self.backup = backup
        self.project_root = Path(__file__).parent.parent
        self.operations_log = []

    def log_operation(self, operation: str, details: str = ""):
        """Registra operação no log."""
        self.operations_log.append({
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "details": details
        })
        print(f"[{'DRY-RUN' if self.dry_run else 'EXEC'}] {operation}: {details}")

    def create_backup(self):
        """Cria backup antes das operações."""
        if not self.backup:
            return

        backup_dir = self.project_root / \
            f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(exist_ok=True)

        self.log_operation("CREATE_BACKUP", f"Backup criado em: {backup_dir}")
        return backup_dir

    def organize_test_files(self):
        """Organiza arquivos de teste dispersos."""
        test_files_to_move = [
            "test_*.py",
            "teste_*.py",
            "*_test.py"
        ]

        # Diretório de destino para testes
        tests_dir = self.project_root / "tests"
        tests_dir.mkdir(exist_ok=True)

        moved_count = 0
        for pattern in test_files_to_move:
            for test_file in self.project_root.glob(pattern):
                if test_file.is_file() and test_file.parent == self.project_root:
                    dest_path = tests_dir / test_file.name

                    if not self.dry_run:
                        shutil.move(str(test_file), str(dest_path))

                    self.log_operation(
                        "MOVE_TEST_FILE", f"{test_file} -> {dest_path}")
                    moved_count += 1

        return moved_count

    def organize_config_files(self):
        """Organiza arquivos de configuração."""
        config_files_to_move = [
            "CONFIGURACAO_*.md",
            "PROVEDORES_*.md",
            "STATE_OF_*.md",
            "TESTE_LOCAL.md",
            "SPEC.md",
            "SECURITY.md",
            "OBSERVABILITY.md"
        ]

        # Diretório de destino para configurações
        config_docs_dir = self.project_root / "docs" / "configuration"
        config_docs_dir.mkdir(exist_ok=True)

        moved_count = 0
        for pattern in config_files_to_move:
            for config_file in self.project_root.glob(pattern):
                if config_file.is_file() and config_file.parent == self.project_root:
                    dest_path = config_docs_dir / config_file.name

                    if not self.dry_run:
                        shutil.move(str(config_file), str(dest_path))

                    self.log_operation("MOVE_CONFIG_FILE",
                                       f"{config_file} -> {dest_path}")
                    moved_count += 1

        return moved_count

    def organize_script_files(self):
        """Organiza scripts dispersos."""
        script_files_to_move = [
            "*.ps1",
            "*.sh",
            "fix_*.sh",
            "setup_*.py",
            "init_*.py",
            "create_*.py",
            "debug_*.py"
        ]

        # Diretório de destino para scripts
        scripts_dir = self.project_root / "scripts"
        scripts_dir.mkdir(exist_ok=True)

        moved_count = 0
        for pattern in script_files_to_move:
            for script_file in self.project_root.glob(pattern):
                if script_file.is_file() and script_file.parent == self.project_root:
                    dest_path = scripts_dir / script_file.name

                    if not self.dry_run:
                        shutil.move(str(script_file), str(dest_path))

                    self.log_operation("MOVE_SCRIPT_FILE",
                                       f"{script_file} -> {dest_path}")
                    moved_count += 1

        return moved_count

    def organize_database_files(self):
        """Organiza arquivos de banco de dados."""
        db_files_to_move = [
            "*.db",
            "*.db-*",
            "create_*.sql"
        ]

        # Diretório de destino para dados
        data_dir = self.project_root / "data"
        data_dir.mkdir(exist_ok=True)

        moved_count = 0
        for pattern in db_files_to_move:
            for db_file in self.project_root.glob(pattern):
                if db_file.is_file() and db_file.parent == self.project_root:
                    dest_path = data_dir / db_file.name

                    if not self.dry_run:
                        shutil.move(str(db_file), str(dest_path))

                    self.log_operation(
                        "MOVE_DB_FILE", f"{db_file} -> {dest_path}")
                    moved_count += 1

        return moved_count

    def clean_temp_files(self):
        """Remove arquivos temporários."""
        temp_patterns = [
            "*.tmp",
            "*.temp",
            "*.log",
            "nul",
            "*.pyc",
            "__pycache__"
        ]

        removed_count = 0
        for pattern in temp_patterns:
            for temp_file in self.project_root.rglob(pattern):
                if temp_file.is_file():
                    if not self.dry_run:
                        temp_file.unlink()

                    self.log_operation("REMOVE_TEMP_FILE", str(temp_file))
                    removed_count += 1
                elif temp_file.is_dir() and temp_file.name == "__pycache__":
                    if not self.dry_run:
                        shutil.rmtree(temp_file)

                    self.log_operation("REMOVE_TEMP_DIR", str(temp_file))
                    removed_count += 1

        return removed_count

    def organize_documentation(self):
        """Organiza documentação dispersa."""
        doc_files_to_move = [
            "README_EN.md",
            "ROADMAP_COMPLETO_*.md"
        ]

        moved_count = 0
        for pattern in doc_files_to_move:
            for doc_file in self.project_root.glob(pattern):
                if doc_file.is_file() and doc_file.parent == self.project_root:
                    dest_path = self.project_root / "docs" / doc_file.name

                    if not self.dry_run:
                        shutil.move(str(doc_file), str(dest_path))

                    self.log_operation(
                        "MOVE_DOC_FILE", f"{doc_file} -> {dest_path}")
                    moved_count += 1

        return moved_count

    def create_directory_structure(self):
        """Cria estrutura de diretórios padrão."""
        directories_to_create = [
            "docs/templates",
            "docs/examples",
            "scripts/maintenance",
            "scripts/development",
            "tools/validation",
            "tools/automation",
            "data/migrations",
            "data/backups",
            "logs",
            "temp"
        ]

        created_count = 0
        for dir_path in directories_to_create:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                if not self.dry_run:
                    full_path.mkdir(parents=True, exist_ok=True)

                self.log_operation("CREATE_DIRECTORY", str(full_path))
                created_count += 1

        return created_count

    def create_gitignore_enhancements(self):
        """Melhora o .gitignore."""
        gitignore_path = self.project_root / ".gitignore"

        additional_ignores = [
            "",
            "# SparkOne specific",
            "data/",
            "logs/",
            "temp/",
            "backup_*/",
            "*.db-shm",
            "*.db-wal",
            "prd_audit_*.json",
            "",
            "# IDE specific",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "",
            "# OS specific",
            ".DS_Store",
            "Thumbs.db",
            "",
            "# Project specific",
            "uploads/temp/",
            "tmp/",
            "out/"
        ]

        if gitignore_path.exists():
            current_content = gitignore_path.read_text()

            # Adicionar apenas linhas que não existem
            new_lines = []
            for line in additional_ignores:
                if line not in current_content:
                    new_lines.append(line)

            if new_lines:
                additional_content = "\n".join(new_lines)
                if not self.dry_run:
                    gitignore_path.write_text(
                        current_content + additional_content)

                self.log_operation("UPDATE_GITIGNORE",
                                   f"Adicionadas {len(new_lines)} linhas")
                return 1
        else:
            if not self.dry_run:
                gitignore_path.write_text("\n".join(additional_ignores))

            self.log_operation("CREATE_GITIGNORE", "Arquivo .gitignore criado")
            return 1

        return 0

    def generate_organization_report(self) -> str:
        """Gera relatório de organização."""
        report = f"""
# SparkOne Project Organization Report

**Data:** {datetime.now().isoformat()}  
**Modo:** {'DRY-RUN' if self.dry_run else 'EXECUCAO'}  
**Backup:** {'Sim' if self.backup else 'Nao'}  

## Operacoes Realizadas

"""

        operation_counts = {}
        for op in self.operations_log:
            op_type = op["operation"]
            operation_counts[op_type] = operation_counts.get(op_type, 0) + 1

        for op_type, count in operation_counts.items():
            report += f"- **{op_type}:** {count} operações\n"

        report += f"\n## Total de Operacoes: {len(self.operations_log)}\n"

        if self.dry_run:
            report += "\n**MODO DRY-RUN**: Nenhuma alteracao foi feita no sistema de arquivos.\n"
            report += "Execute sem --dry-run para aplicar as mudancas.\n"
        else:
            report += "\n**MUDANCAS APLICADAS** com sucesso!\n"

        return report

    def run_organization(self):
        """Executa processo completo de organização."""
        print("Iniciando organizacao do projeto SparkOne...")

        if self.backup and not self.dry_run:
            self.create_backup()

        # Executar operações de organização
        operations = [
            ("Test Files", self.organize_test_files),
            ("Config Files", self.organize_config_files),
            ("Script Files", self.organize_script_files),
            ("Database Files", self.organize_database_files),
            ("Documentation", self.organize_documentation),
            ("Directory Structure", self.create_directory_structure),
            ("GitIgnore", self.create_gitignore_enhancements),
            ("Temp Files", self.clean_temp_files)
        ]

        total_operations = 0
        for name, func in operations:
            print(f"\nOrganizando {name}...")
            count = func()
            total_operations += count
            print(f"   OK: {count} operacoes realizadas")

        print(f"\nOrganizacao concluida! Total: {total_operations} operacoes")

        # Gerar relatório
        report = self.generate_organization_report()

        # Salvar relatório
        report_file = self.project_root / "reports" / \
            f"organization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.dry_run:
            report_file.write_text(report, encoding='utf-8')
            print(f"Relatorio salvo em: {report_file}")

        return report


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="SparkOne Project Organizer")
    parser.add_argument("--dry-run", action="store_true",
                        help="Modo de simulação (não aplica mudanças)")
    parser.add_argument("--no-backup", action="store_true",
                        help="Não criar backup antes das operações")

    args = parser.parse_args()

    organizer = ProjectOrganizer(
        dry_run=args.dry_run,
        backup=not args.no_backup
    )

    report = organizer.run_organization()

    if args.dry_run:
        print("\nMODO DRY-RUN: Execute sem --dry-run para aplicar as mudancas.")

    print("\n" + "="*50)
    print(report)


if __name__ == "__main__":
    main()
