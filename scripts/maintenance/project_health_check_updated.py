#!/usr/bin/env python3
"""
SparkOne Project Health Check - Atualizado para Nova Estrutura
Verifica a saúde do projeto após reorganização.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any

class ProjectHealthCheck:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.score = 0
        self.max_score = 100
        self.issues = []
        self.warnings = []
        
    def log(self, message: str):
        """Log de mensagem."""
        print(f"[OK]       {message}")
        
    def warn(self, message: str):
        """Log de warning."""
        print(f"[WARNING]  {message}")
        self.warnings.append(message)
        
    def error(self, message: str):
        """Log de erro."""
        print(f"[ERROR]    {message}")
        self.issues.append(message)
        
    def check_essential_files(self) -> Tuple[int, List[str]]:
        """Verifica arquivos essenciais."""
        print("\n[INFO] Verificando arquivos essenciais...")
        score = 0
        issues = []
        
        essential_files = {
            "README.md": 10,
            "pyproject.toml": 10,
            ".gitignore": 5,
            "Makefile": 5,
        }
        
        for file_name, points in essential_files.items():
            file_path = self.project_root / file_name
            if file_path.exists():
                score += points
                self.log(f"[OK] {file_name}")
            else:
                issues.append(f"[FAIL] {file_name} nao encontrado")
                self.error(f"{file_name} nao encontrado")
        
        return score, issues
    
    def check_directory_structure(self) -> Tuple[int, List[str]]:
        """Verifica estrutura de diretórios."""
        print("\n[INFO] Verificando estrutura de diretórios...")
        score = 0
        issues = []
        
        required_dirs = {
            "src/app": 15,
            "docs": 10,
            "tests": 10,
            "scripts": 5,
            "config": 5,
            "ops": 5,
            "data": 5,
            "tools": 5,
        }
        
        for dir_name, points in required_dirs.items():
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                score += points
                self.log(f"[OK] {dir_name}/")
            else:
                issues.append(f"[FAIL] {dir_name}/ nao encontrado")
                self.error(f"{dir_name}/ nao encontrado")
        
        return score, issues
    
    def check_application_files(self) -> Tuple[int, List[str]]:
        """Verifica arquivos da aplicação."""
        print("\n[INFO] Verificando arquivos da aplicação...")
        score = 0
        issues = []
        
        app_files = {
            "src/app/main.py": 10,
            "src/app/config.py": 5,
        }
        
        for file_name, points in app_files.items():
            file_path = self.project_root / file_name
            if file_path.exists():
                score += points
                self.log(f"[OK] {file_name}")
            else:
                issues.append(f"[FAIL] {file_name} nao encontrado")
                self.error(f"{file_name} nao encontrado")
        
        return score, issues
    
    def check_configuration_files(self) -> Tuple[int, List[str]]:
        """Verifica arquivos de configuração."""
        print("\n[INFO] Verificando arquivos de configuração...")
        score = 0
        issues = []
        
        config_files = {
            "config/docker/Dockerfile": 5,
            "config/docker/docker-compose.yml": 5,
            "config/docker/docker-compose.prod.yml": 5,
            "config/production.env": 5,
            "config/env.example": 5,
        }
        
        for file_name, points in config_files.items():
            file_path = self.project_root / file_name
            if file_path.exists():
                score += points
                self.log(f"[OK] {file_name}")
            else:
                issues.append(f"[FAIL] {file_name} nao encontrado")
                self.error(f"{file_name} nao encontrado")
        
        return score, issues
    
    def check_documentation_structure(self) -> Tuple[int, List[str]]:
        """Verifica estrutura de documentação."""
        print("\n[INFO] Verificando estrutura de documentação...")
        score = 0
        issues = []
        
        doc_files = {
            "docs/README.md": 5,
            "docs/INDEX.md": 5,
            "docs/architecture/overview.md": 5,
            "docs/architecture/infrastructure.md": 5,
            "docs/api.md": 5,
            "docs/operations/deployment-guide.md": 5,
            "docs/development/development-guide.md": 5,
        }
        
        for file_name, points in doc_files.items():
            file_path = self.project_root / file_name
            if file_path.exists():
                score += points
                self.log(f"[OK] {file_name}")
            else:
                issues.append(f"[FAIL] {file_name} nao encontrado")
                self.error(f"{file_name} nao encontrado")
        
        return score, issues
    
    def check_prd_documentation(self) -> Tuple[int, List[str]]:
        """Verifica documentação PRD."""
        print("\n[INFO] Verificando documentação PRD...")
        score = 0
        issues = []
        
        prd_files = {
            "docs/prd/sparkone/PRD.pt-BR.md": 10,
            "docs/prd/sparkone/PRD.en-US.md": 10,
            "docs/prd/sparkone/FREEZE_REPORT.md": 5,
            "docs/prd/sparkone/backlog.csv": 5,
        }
        
        for file_name, points in prd_files.items():
            file_path = self.project_root / file_name
            if file_path.exists():
                score += points
                self.log(f"[OK] {file_name}")
            else:
                issues.append(f"[FAIL] {file_name} nao encontrado")
                self.error(f"{file_name} nao encontrado")
        
        return score, issues
    
    def check_scripts_organization(self) -> Tuple[int, List[str]]:
        """Verifica organização de scripts."""
        print("\n[INFO] Verificando organização de scripts...")
        score = 0
        issues = []
        
        script_dirs = {
            "scripts/development": 5,
            "scripts/maintenance": 5,
            "scripts/production": 5,
            "scripts/tools": 5,
        }
        
        for dir_name, points in script_dirs.items():
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                score += points
                self.log(f"[OK] {dir_name}/")
            else:
                issues.append(f"[FAIL] {dir_name}/ nao encontrado")
                self.error(f"{dir_name}/ nao encontrado")
        
        return score, issues
    
    def check_tests_organization(self) -> Tuple[int, List[str]]:
        """Verifica organização de testes."""
        print("\n[INFO] Verificando organização de testes...")
        score = 0
        issues = []
        
        test_dirs = {
            "tests/unit": 5,
            "tests/integration": 5,
            "tests/e2e": 5,
            "tests/smoke": 5,
            "tests/testsprite": 5,
        }
        
        for dir_name, points in test_dirs.items():
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                score += points
                self.log(f"[OK] {dir_name}/")
            else:
                issues.append(f"[FAIL] {dir_name}/ nao encontrado")
                self.error(f"{dir_name}/ nao encontrado")
        
        return score, issues
    
    def check_data_organization(self) -> Tuple[int, List[str]]:
        """Verifica organização de dados."""
        print("\n[INFO] Verificando organização de dados...")
        score = 0
        issues = []
        
        data_dirs = {
            "data/databases": 5,
            "data/backups": 5,
            "data/uploads": 5,
            "logs": 5,
        }
        
        for dir_name, points in data_dirs.items():
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                score += points
                self.log(f"[OK] {dir_name}/")
            else:
                issues.append(f"[FAIL] {dir_name}/ nao encontrado")
                self.error(f"{dir_name}/ nao encontrado")
        
        return score, issues
    
    def run_health_check(self) -> Dict[str, Any]:
        """Executa verificação completa de saúde."""
        print("SparkOne Project Health Check - Nova Estrutura")
        print("=" * 60)
        
        total_score = 0
        all_issues = []
        
        # Executar todas as verificações
        checks = [
            ("Arquivos Essenciais", self.check_essential_files),
            ("Estrutura de Diretórios", self.check_directory_structure),
            ("Arquivos da Aplicação", self.check_application_files),
            ("Arquivos de Configuração", self.check_configuration_files),
            ("Estrutura de Documentação", self.check_documentation_structure),
            ("Documentação PRD", self.check_prd_documentation),
            ("Organização de Scripts", self.check_scripts_organization),
            ("Organização de Testes", self.check_tests_organization),
            ("Organização de Dados", self.check_data_organization),
        ]
        
        for check_name, check_func in checks:
            print(f"\n[CHECK] {check_name}")
            print("-" * 40)
            score, issues = check_func()
            total_score += score
            all_issues.extend(issues)
        
        # Calcular score final
        final_score = min(total_score, self.max_score)
        grade = self._calculate_grade(final_score)
        
        # Relatório final
        print("\n" + "=" * 60)
        print("RELATORIO FINAL")
        print("=" * 60)
        
        print(f"[SCORE] Score Geral: {final_score}/{self.max_score}")
        print(f"[GRADE] Nota: {grade}")
        
        if all_issues:
            print(f"\n[ISSUES] {len(all_issues)} problemas encontrados:")
            for issue in all_issues:
                print(f"  {issue}")
        
        if self.warnings:
            print(f"\n[WARNINGS] {len(self.warnings)} avisos:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        # Status geral
        if final_score >= 90:
            print("\n[EXCELLENT] PROJETO EM EXCELENTE ESTADO!")
        elif final_score >= 80:
            print("\n[GOOD] PROJETO EM BOM ESTADO!")
        elif final_score >= 70:
            print("\n[WARNING] PROJETO PRECISA DE ATENCAO!")
        else:
            print("\n[ERROR] PROJETO PRECISA DE CORRECOES URGENTES!")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "score": final_score,
            "max_score": self.max_score,
            "grade": grade,
            "issues": all_issues,
            "warnings": self.warnings,
            "status": "EXCELLENT" if final_score >= 90 else "GOOD" if final_score >= 80 else "NEEDS_ATTENTION" if final_score >= 70 else "NEEDS_FIXES"
        }
    
    def _calculate_grade(self, score: int) -> str:
        """Calcula nota baseada no score."""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 75:
            return "C+"
        elif score >= 70:
            return "C"
        elif score >= 65:
            return "D+"
        elif score >= 60:
            return "D"
        else:
            return "F"

def main():
    """Função principal."""
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    else:
        project_root = Path(__file__).resolve().parents[2]
    
    if not project_root.exists():
        print(f"[ERROR] Diretorio do projeto nao encontrado: {project_root}")
        sys.exit(1)
    
    health_check = ProjectHealthCheck(project_root)
    report = health_check.run_health_check()
    
    # Salvar relatório
    report_file = project_root / "reports" / f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SAVE] Relatorio salvo em: {report_file}")
    
    # Exit code baseado no score
    if report["score"] >= 80:
        sys.exit(0)  # Sucesso
    else:
        sys.exit(1)  # Falha

if __name__ == "__main__":
    main()
