#!/usr/bin/env python3
"""
SparkOne Project Health Check
============================

Script automatizado para verificar a saúde geral do projeto SparkOne.
Executa verificações de documentação, código, testes e infraestrutura.

Uso:
    python scripts/project_health_check.py [--verbose] [--fix]

Autor: AI Assistant
Data: Janeiro 2025
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
from datetime import datetime


class ProjectHealthChecker:
    """Verificador de saúde do projeto SparkOne."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": 0,
            "checks": {}
        }

    def log(self, message: str, level: str = "INFO"):
        """Log com níveis de verbosidade."""
        if self.verbose or level in ["ERROR", "WARNING"]:
            # Remove emojis for Windows compatibility
            message = message.replace("✅", "[OK]").replace(
                "❌", "[FAIL]").replace("⚠️", "[WARN]").replace("📋", "[INFO]")
            print(f"[{level}] {message}")

    def check_documentation_structure(self) -> Tuple[int, List[str]]:
        """Verifica estrutura da documentação."""
        score = 0
        issues = []

        required_docs = [
            "docs/README.md",
            "docs/INDEX.md",
            "docs/ARCHITECTURE.md",
            "docs/api.md",
            "docs/operations/deployment-guide.md",
            "docs/operations/operations-runbook.md",
            "docs/development/development-guide.md",
            "docs/development/testing-strategy.md",
            "docs/prd/sparkone/PRD.pt-BR.md",
            "docs/prd/sparkone/PRD.en-US.md",
            "docs/prd/sparkone/FREEZE_REPORT.md"
        ]

        for doc in required_docs:
            doc_path = self.project_root / doc
            if doc_path.exists():
                score += 10
                self.log(f"✅ {doc} encontrado")
            else:
                issues.append(f"❌ {doc} não encontrado")

        return score, issues

    def check_prd_quality(self) -> Tuple[int, List[str]]:
        """Verifica qualidade dos PRDs."""
        score = 0
        issues = []

        # Verificar se FREEZE_REPORT indica score 100/100
        freeze_report = self.project_root / "docs/prd/sparkone/FREEZE_REPORT.md"
        if freeze_report.exists():
            content = freeze_report.read_text()
            if "Score: 100/100" in content:
                score += 50
                self.log("✅ PRD com score 100/100")
            else:
                issues.append("❌ PRD não atingiu score 100/100")

        # Verificar consistência bilíngue
        pt_prd = self.project_root / "docs/prd/sparkone/PRD.pt-BR.md"
        en_prd = self.project_root / "docs/prd/sparkone/PRD.en-US.md"

        if pt_prd.exists() and en_prd.exists():
            score += 30
            self.log("✅ PRDs bilíngues presentes")
        else:
            issues.append("❌ PRDs bilíngues incompletos")

        # Verificar backlog
        backlog = self.project_root / "docs/prd/sparkone/backlog.csv"
        if backlog.exists():
            score += 20
            self.log("✅ Backlog presente")
        else:
            issues.append("❌ Backlog não encontrado")

        return score, issues

    def check_code_structure(self) -> Tuple[int, List[str]]:
        """Verifica estrutura do código."""
        score = 0
        issues = []

        required_dirs = [
            "src/app",
            "src/app/routers",
            "src/app/services",
            "src/app/models",
            "src/app/core",
            "tests"
        ]

        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                score += 15
                self.log(f"✅ {dir_path} presente")
            else:
                issues.append(f"❌ {dir_path} não encontrado")

        # Verificar arquivos principais
        main_files = [
            "src/app/main.py",
            "pyproject.toml",
            "docker-compose.yml",
            "Dockerfile"
        ]

        for file_path in main_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                score += 10
                self.log(f"✅ {file_path} presente")
            else:
                issues.append(f"❌ {file_path} não encontrado")

        return score, issues

    def check_tests(self) -> Tuple[int, List[str]]:
        """Verifica estrutura de testes."""
        score = 0
        issues = []

        # Verificar TestSprite tests
        testsprite_dir = self.project_root / "testsprite_tests"
        if testsprite_dir.exists():
            test_files = list(testsprite_dir.glob("TC*.py"))
            if len(test_files) >= 10:
                score += 40
                self.log(f"✅ {len(test_files)} testes TestSprite encontrados")
            else:
                issues.append(
                    f"❌ Apenas {len(test_files)} testes TestSprite (esperado: 10+)")

        # Verificar testes unitários
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            test_files = list(tests_dir.glob("test_*.py"))
            if len(test_files) > 0:
                score += 30
                self.log(f"✅ {len(test_files)} testes unitários encontrados")
            else:
                issues.append("❌ Nenhum teste unitário encontrado")

        # Verificar configuração de testes
        pytest_configs = ["pytest.ini", "pyproject.toml", "setup.cfg"]
        has_pytest_config = any(
            (self.project_root / config).exists() for config in pytest_configs
        )

        if has_pytest_config:
            score += 30
            self.log("✅ Configuração pytest encontrada")
        else:
            issues.append("❌ Configuração pytest não encontrada")

        return score, issues

    def check_infrastructure(self) -> Tuple[int, List[str]]:
        """Verifica configuração de infraestrutura."""
        score = 0
        issues = []

        # Verificar Docker
        docker_files = [
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.prod.yml"
        ]

        for docker_file in docker_files:
            if (self.project_root / docker_file).exists():
                score += 20
                self.log(f"✅ {docker_file} presente")
            else:
                issues.append(f"❌ {docker_file} não encontrado")

        # Verificar configurações
        config_files = [
            "config/production.env",
            "pyproject.toml",
            "alembic.ini"
        ]

        for config_file in config_files:
            if (self.project_root / config_file).exists():
                score += 15
                self.log(f"✅ {config_file} presente")
            else:
                issues.append(f"❌ {config_file} não encontrado")

        # Verificar ops
        ops_dir = self.project_root / "ops"
        if ops_dir.exists():
            score += 25
            self.log("✅ Diretório ops presente")
        else:
            issues.append("❌ Diretório ops não encontrado")

        return score, issues

    def check_security(self) -> Tuple[int, List[str]]:
        """Verifica configurações de segurança."""
        score = 0
        issues = []

        # Verificar SECURITY.md
        security_doc = self.project_root / "SECURITY.md"
        if security_doc.exists():
            score += 30
            self.log("✅ SECURITY.md presente")
        else:
            issues.append("❌ SECURITY.md não encontrado")

        # Verificar .gitignore
        gitignore = self.project_root / ".gitignore"
        if gitignore.exists():
            score += 20
            self.log("✅ .gitignore presente")
        else:
            issues.append("❌ .gitignore não encontrado")

        # Verificar se não há secrets expostos
        sensitive_patterns = [
            "password",
            "secret",
            "token",
            "key",
            "credential"
        ]

        # Verificar arquivos de configuração
        config_files = list(self.project_root.glob("**/*.env")) + \
            list(self.project_root.glob("**/*.yaml")) + \
            list(self.project_root.glob("**/*.yml"))

        secrets_found = []
        for config_file in config_files:
            try:
                content = config_file.read_text().lower()
                for pattern in sensitive_patterns:
                    if pattern in content and "example" not in content:
                        secrets_found.append(f"{config_file}: {pattern}")
            except:
                continue

        if not secrets_found:
            score += 50
            self.log("✅ Nenhum secret exposto encontrado")
        else:
            issues.extend(
                [f"⚠️ Possível secret exposto: {secret}" for secret in secrets_found[:5]])

        return score, issues

    def run_all_checks(self) -> Dict:
        """Executa todas as verificações."""
        self.log("🔍 Iniciando verificação de saúde do projeto SparkOne...")

        checks = [
            ("Documentation Structure", self.check_documentation_structure),
            ("PRD Quality", self.check_prd_quality),
            ("Code Structure", self.check_code_structure),
            ("Tests", self.check_tests),
            ("Infrastructure", self.check_infrastructure),
            ("Security", self.check_security)
        ]

        total_score = 0
        max_score = 0

        for check_name, check_func in checks:
            self.log(f"\n📋 Verificando {check_name}...")
            score, issues = check_func()

            self.results["checks"][check_name] = {
                "score": score,
                "issues": issues,
                "max_possible": 100 if check_name == "PRD Quality" else
                150 if check_name == "Code Structure" else
                100 if check_name == "Tests" else
                100 if check_name == "Infrastructure" else
                100 if check_name == "Security" else 110
            }

            total_score += score
            max_score += self.results["checks"][check_name]["max_possible"]

            if issues:
                for issue in issues:
                    self.log(f"  {issue}", "WARNING")
            else:
                self.log(f"  ✅ {check_name}: {score} pontos")

        self.results["overall_score"] = int(
            (total_score / max_score) * 100) if max_score > 0 else 0

        return self.results

    def generate_report(self) -> str:
        """Gera relatório de saúde."""
        report = f"""
# 🏥 SparkOne Project Health Report

**Data:** {self.results['timestamp']}  
**Score Geral:** {self.results['overall_score']}/100  

## 📊 Resumo por Categoria

"""

        for check_name, data in self.results["checks"].items():
            status = "✅" if not data["issues"] else "⚠️" if data["score"] > 50 else "❌"
            report += f"| {status} **{check_name}** | {data['score']}/{data['max_possible']} | {len(data['issues'])} issues |\n"

        report += "\n## 🚨 Issues Encontradas\n\n"

        for check_name, data in self.results["checks"].items():
            if data["issues"]:
                report += f"### {check_name}\n"
                for issue in data["issues"]:
                    report += f"- {issue}\n"
                report += "\n"

        if self.results["overall_score"] >= 90:
            report += "## 🎉 Status: Excelente!\n"
            report += "O projeto está em excelente estado de saúde.\n"
        elif self.results["overall_score"] >= 70:
            report += "## ✅ Status: Bom\n"
            report += "O projeto está em bom estado, com algumas melhorias necessárias.\n"
        else:
            report += "## ⚠️ Status: Precisa Atenção\n"
            report += "O projeto precisa de melhorias significativas.\n"

        return report

    def save_results(self, output_file: str = None):
        """Salva resultados em arquivo."""
        if not output_file:
            output_file = self.project_root / "reports" / \
                f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        self.log(f"📄 Resultados salvos em: {output_path}")
        return output_path


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="SparkOne Project Health Check")
    parser.add_argument("--verbose", "-v",
                        action="store_true", help="Modo verboso")
    parser.add_argument(
        "--output", "-o", help="Arquivo de saída para resultados JSON")
    parser.add_argument(
        "--report", "-r", help="Arquivo de saída para relatório markdown")

    args = parser.parse_args()

    checker = ProjectHealthChecker(verbose=args.verbose)
    results = checker.run_all_checks()

    print(f"\n[SCORE] Score Geral: {results['overall_score']}/100")

    if args.output:
        checker.save_results(args.output)

    if args.report:
        report = checker.generate_report()
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 Relatório salvo em: {args.report}")

    # Exit code baseado no score
    if results['overall_score'] >= 90:
        sys.exit(0)  # Sucesso
    elif results['overall_score'] >= 70:
        sys.exit(1)  # Aviso
    else:
        sys.exit(2)  # Erro


if __name__ == "__main__":
    main()
