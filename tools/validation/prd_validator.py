#!/usr/bin/env python3
"""
SparkOne PRD Validator
=====================

Ferramenta para validar automaticamente a qualidade e consistência dos PRDs.
Verifica sincronização bilíngue, rastreabilidade e estrutura.

Uso:
    python tools/validation/prd_validator.py [--fix] [--verbose]

Autor: AI Assistant  
Data: Janeiro 2025
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set
from datetime import datetime


class PRDValidator:
    """Validador de PRDs do SparkOne."""
    
    def __init__(self, fix: bool = False, verbose: bool = False):
        self.fix = fix
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent.parent
        self.prd_dir = self.project_root / "docs" / "prd" / "sparkone"
        self.issues = []
        self.fixes_applied = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log com níveis de verbosidade."""
        if self.verbose or level in ["ERROR", "WARNING"]:
            print(f"[{level}] {message}")
    
    def extract_requirements(self, content: str) -> Dict[str, List[str]]:
        """Extrai IDs de requisitos do conteúdo."""
        patterns = {
            'RF': r'RF-\d{3}',
            'RNF': r'RNF-\d{3}', 
            'BUG': r'BUG-\d{3}',
            'TECH': r'TECH-\d{3}',
            'ADR': r'ADR-\d{3}'
        }
        
        requirements = {}
        for req_type, pattern in patterns.items():
            matches = re.findall(pattern, content)
            requirements[req_type] = sorted(set(matches))
        
        return requirements
    
    def validate_bilingual_consistency(self) -> Tuple[int, List[str]]:
        """Valida consistência entre PRDs em português e inglês."""
        score = 0
        issues = []
        
        pt_file = self.prd_dir / "PRD.pt-BR.md"
        en_file = self.prd_dir / "PRD.en-US.md"
        
        if not pt_file.exists() or not en_file.exists():
            issues.append("❌ PRDs bilíngues não encontrados")
            return 0, issues
        
        # Ler conteúdo dos arquivos
        pt_content = pt_file.read_text(encoding='utf-8')
        en_content = en_file.read_text(encoding='utf-8')
        
        # Extrair requisitos
        pt_requirements = self.extract_requirements(pt_content)
        en_requirements = self.extract_requirements(en_content)
        
        # Verificar consistência de RFs
        pt_rfs = set(pt_requirements.get('RF', []))
        en_rfs = set(en_requirements.get('RNF', []))
        
        if pt_rfs == en_rfs:
            score += 40
            self.log("✅ RFs consistentes entre PT e EN")
        else:
            missing_in_en = pt_rfs - en_rfs
            missing_in_pt = en_rfs - pt_rfs
            
            if missing_in_en:
                issues.append(f"❌ RFs em PT não encontrados em EN: {missing_in_en}")
            if missing_in_pt:
                issues.append(f"❌ RFs em EN não encontrados em PT: {missing_in_pt}")
        
        # Verificar consistência de RNFs
        pt_rnfs = set(pt_requirements.get('RNF', []))
        en_rnfs = set(en_requirements.get('RNF', []))
        
        if pt_rnfs == en_rnfs:
            score += 30
            self.log("✅ RNFs consistentes entre PT e EN")
        else:
            missing_in_en = pt_rnfs - en_rnfs
            missing_in_pt = en_rnfs - pt_rnfs
            
            if missing_in_en:
                issues.append(f"❌ RNFs em PT não encontrados em EN: {missing_in_en}")
            if missing_in_pt:
                issues.append(f"❌ RNFs em EN não encontrados em PT: {missing_in_pt}")
        
        # Verificar seções obrigatórias
        required_sections = [
            "Timeline e Marcos", "Timeline and Milestones",
            "Análise de Riscos", "Risk Analysis",
            "Orçamento e Recursos", "Budget and Resources"
        ]
        
        pt_sections_found = sum(1 for section in required_sections[:3] if section in pt_content)
        en_sections_found = sum(1 for section in required_sections[3:] if section in en_content)
        
        if pt_sections_found == 3 and en_sections_found == 3:
            score += 30
            self.log("✅ Seções obrigatórias presentes em ambos PRDs")
        else:
            issues.append(f"❌ Seções faltando: PT={pt_sections_found}/3, EN={en_sections_found}/3")
        
        return score, issues
    
    def validate_traceability(self) -> Tuple[int, List[str]]:
        """Valida rastreabilidade entre PRD, backlog e ADRs."""
        score = 0
        issues = []
        
        # Verificar backlog
        backlog_file = self.prd_dir / "backlog.csv"
        if not backlog_file.exists():
            issues.append("❌ Backlog não encontrado")
            return 0, issues
        
        backlog_content = backlog_file.read_text(encoding='utf-8')
        backlog_requirements = self.extract_requirements(backlog_content)
        
        # Verificar PRDs
        pt_file = self.prd_dir / "PRD.pt-BR.md"
        en_file = self.prd_dir / "PRD.en-US.md"
        
        if pt_file.exists() and en_file.exists():
            pt_content = pt_file.read_text(encoding='utf-8')
            en_content = en_file.read_text(encoding='utf-8')
            
            pt_requirements = self.extract_requirements(pt_content)
            en_requirements = self.extract_requirements(en_content)
            
            # Verificar se todos os RFs do backlog estão nos PRDs
            backlog_rfs = set(backlog_requirements.get('RF', []))
            pt_rfs = set(pt_requirements.get('RF', []))
            en_rfs = set(en_requirements.get('RF', []))
            
            if backlog_rfs.issubset(pt_rfs) and backlog_rfs.issubset(en_rfs):
                score += 40
                self.log("✅ Todos os RFs do backlog estão nos PRDs")
            else:
                missing_in_pt = backlog_rfs - pt_rfs
                missing_in_en = backlog_rfs - en_rfs
                
                if missing_in_pt:
                    issues.append(f"❌ RFs do backlog faltando no PRD PT: {missing_in_pt}")
                if missing_in_en:
                    issues.append(f"❌ RFs do backlog faltando no PRD EN: {missing_in_en}")
        
        # Verificar ADRs
        decisions_file = self.prd_dir / "decisions.md"
        if decisions_file.exists():
            decisions_content = decisions_file.read_text(encoding='utf-8')
            decisions_adrs = set(self.extract_requirements(decisions_content).get('ADR', []))
            
            # Verificar se ADRs do backlog existem
            backlog_adrs = set(backlog_requirements.get('ADR', []))
            
            if backlog_adrs.issubset(decisions_adrs):
                score += 30
                self.log("✅ Todos os ADRs do backlog estão documentados")
            else:
                missing_adrs = backlog_adrs - decisions_adrs
                issues.append(f"❌ ADRs do backlog não documentados: {missing_adrs}")
        else:
            issues.append("❌ Arquivo de decisões não encontrado")
        
        # Verificar Technical Debt
        tech_debt_in_backlog = set(backlog_requirements.get('BUG', []) + backlog_requirements.get('TECH', []))
        if tech_debt_in_backlog:
            # Verificar se estão nos PRDs
            if pt_file.exists() and en_file.exists():
                pt_content = pt_file.read_text(encoding='utf-8')
                en_content = en_file.read_text(encoding='utf-8')
                
                pt_tech_debt = set(self.extract_requirements(pt_content).get('BUG', []) + 
                                 self.extract_requirements(pt_content).get('TECH', []))
                en_tech_debt = set(self.extract_requirements(en_content).get('BUG', []) + 
                                 self.extract_requirements(en_content).get('TECH', []))
                
                if tech_debt_in_backlog.issubset(pt_tech_debt) and tech_debt_in_backlog.issubset(en_tech_debt):
                    score += 30
                    self.log("✅ Technical Debt está documentado nos PRDs")
                else:
                    issues.append("❌ Technical Debt do backlog não está nos PRDs")
        
        return score, issues
    
    def validate_structure_completeness(self) -> Tuple[int, List[str]]:
        """Valida completude da estrutura dos PRDs."""
        score = 0
        issues = []
        
        required_files = [
            "PRD.pt-BR.md",
            "PRD.en-US.md", 
            "backlog.csv",
            "decisions.md",
            "coerencia.md",
            "inventory.json",
            "FREEZE_REPORT.md"
        ]
        
        files_found = 0
        for file_name in required_files:
            file_path = self.prd_dir / file_name
            if file_path.exists():
                files_found += 1
                self.log(f"✅ {file_name} encontrado")
            else:
                issues.append(f"❌ {file_name} não encontrado")
        
        score = int((files_found / len(required_files)) * 50)
        
        # Verificar FREEZE_REPORT score
        freeze_report = self.prd_dir / "FREEZE_REPORT.md"
        if freeze_report.exists():
            content = freeze_report.read_text(encoding='utf-8')
            if "Score: 100/100" in content:
                score += 50
                self.log("✅ FREEZE_REPORT indica score 100/100")
            else:
                issues.append("❌ FREEZE_REPORT não indica score 100/100")
        
        return score, issues
    
    def validate_file_organization(self) -> Tuple[int, List[str]]:
        """Valida organização de arquivos."""
        score = 100
        issues = []
        
        # Verificar se há arquivos históricos no diretório principal
        historical_patterns = [
            "prd_freeze_report_v1.0_FINAL.md",
            "prd_codex_*.md",
            "validation_prompt.*",
            "baseline_*.md",
            "execution_plan_*.md",
            "issues_*.csv",
            "notes_*.md",
            "traceability.md"
        ]
        
        files_in_main_dir = []
        for pattern in historical_patterns:
            for file_path in self.prd_dir.glob(pattern):
                if file_path.is_file():
                    files_in_main_dir.append(file_path.name)
        
        if files_in_main_dir:
            score -= len(files_in_main_dir) * 10
            issues.append(f"❌ Arquivos históricos no diretório principal: {files_in_main_dir}")
        
        # Verificar se existe diretório archive
        archive_dir = self.prd_dir / "archive"
        if archive_dir.exists():
            archive_files = list(archive_dir.glob("*"))
            if archive_files:
                score += 20
                self.log(f"✅ {len(archive_files)} arquivos históricos organizados em archive/")
        
        return max(0, score), issues
    
    def apply_fixes(self, issues: List[str]) -> List[str]:
        """Aplica correções automáticas quando possível."""
        fixes_applied = []
        
        for issue in issues:
            if "Arquivos históricos no diretório principal" in issue:
                if self.fix:
                    # Mover arquivos históricos para archive
                    archive_dir = self.prd_dir / "archive"
                    archive_dir.mkdir(exist_ok=True)
                    
                    historical_files = [
                        "prd_freeze_report_v1.0_FINAL.md",
                        "prd_codex_corrections_final.md",
                        "prd_codex_validation.md",
                        "validation_prompt.md",
                        "validation_prompt.txt",
                        "baseline_v1.md",
                        "execution_plan_proactivity.md",
                        "issues_proactivity.csv",
                        "notes_alignment.md",
                        "traceability.md"
                    ]
                    
                    moved_count = 0
                    for file_name in historical_files:
                        file_path = self.prd_dir / file_name
                        if file_path.exists():
                            dest_path = archive_dir / file_name
                            file_path.rename(dest_path)
                            moved_count += 1
                    
                    if moved_count > 0:
                        fixes_applied.append(f"✅ Movidos {moved_count} arquivos históricos para archive/")
                        self.log(f"Correção aplicada: movidos {moved_count} arquivos históricos")
        
        return fixes_applied
    
    def run_validation(self) -> Dict:
        """Executa validação completa."""
        self.log("🔍 Iniciando validação de PRDs...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": 0,
            "checks": {}
        }
        
        checks = [
            ("Bilingual Consistency", self.validate_bilingual_consistency),
            ("Traceability", self.validate_traceability),
            ("Structure Completeness", self.validate_structure_completeness),
            ("File Organization", self.validate_file_organization)
        ]
        
        total_score = 0
        all_issues = []
        
        for check_name, check_func in checks:
            self.log(f"\n📋 Validando {check_name}...")
            score, issues = check_func()
            
            results["checks"][check_name] = {
                "score": score,
                "issues": issues
            }
            
            total_score += score
            all_issues.extend(issues)
            
            if issues:
                for issue in issues:
                    self.log(f"  {issue}", "WARNING")
            else:
                self.log(f"  ✅ {check_name}: {score}/100")
        
        results["overall_score"] = int(total_score / len(checks))
        results["all_issues"] = all_issues
        
        # Aplicar correções se solicitado
        if self.fix and all_issues:
            self.log("\n🔧 Aplicando correções automáticas...")
            fixes_applied = self.apply_fixes(all_issues)
            results["fixes_applied"] = fixes_applied
            
            for fix in fixes_applied:
                self.log(f"  {fix}")
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """Gera relatório de validação."""
        report = f"""
# 🔍 SparkOne PRD Validation Report

**Data:** {results['timestamp']}  
**Score Geral:** {results['overall_score']}/100  

## 📊 Resumo por Categoria

"""
        
        for check_name, data in results["checks"].items():
            status = "✅" if data["score"] >= 90 else "⚠️" if data["score"] >= 70 else "❌"
            report += f"| {status} **{check_name}** | {data['score']}/100 | {len(data['issues'])} issues |\n"
        
        if results.get("all_issues"):
            report += "\n## 🚨 Issues Encontradas\n\n"
            for issue in results["all_issues"]:
                report += f"- {issue}\n"
        
        if results.get("fixes_applied"):
            report += "\n## 🔧 Correções Aplicadas\n\n"
            for fix in results["fixes_applied"]:
                report += f"- {fix}\n"
        
        if results["overall_score"] >= 90:
            report += "\n## 🎉 Status: Excelente!\n"
            report += "Os PRDs estão em excelente estado.\n"
        elif results["overall_score"] >= 70:
            report += "\n## ✅ Status: Bom\n"
            report += "Os PRDs estão em bom estado, com algumas melhorias necessárias.\n"
        else:
            report += "\n## ⚠️ Status: Precisa Atenção\n"
            report += "Os PRDs precisam de melhorias significativas.\n"
        
        return report


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="SparkOne PRD Validator")
    parser.add_argument("--fix", action="store_true", help="Aplicar correções automáticas")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verboso")
    parser.add_argument("--output", "-o", help="Arquivo de saída para relatório")
    
    args = parser.parse_args()
    
    validator = PRDValidator(fix=args.fix, verbose=args.verbose)
    results = validator.run_validation()
    
    print(f"\n🎯 Score Geral: {results['overall_score']}/100")
    
    if args.output:
        report = validator.generate_report(results)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 Relatório salvo em: {args.output}")


if __name__ == "__main__":
    main()
