# SparkOne PRD — Comprehensive Validation Request

You are a PRD validation expert. Analyze the SparkOne project documentation and deliver a structured validation report scoring each criterion.

## VALIDATION CRITERIA (100 points total)

### 1. Requirement ID Consistency (20 points)
- All requirements use RF-xxx (functional) or RNF-xxx (non-functional)
- IDs unique, sequential, match exactly between PT-BR and EN-US
- All IDs referenced in backlog/decisions/system-map/traceability exist in PRDs

**Deductions:**
- -5 per duplicate ID
- -3 per missing ID
- -2 per PT/EN mismatch
- -1 per broken cross-reference

### 2. Traceability (20 points)
- Every PRD requirement maps to backlog item(s)
- Every backlog item references PRD ID(s)
- ADRs reference specific requirements
- System-map components link to requirements
- inventory.json aligns with system-map and PRDs

**Deductions:**
- -4 per orphaned requirement
- -3 per orphaned backlog item
- -2 per ADR without requirement link
- -1 per unmapped component

### 3. Bilingual Parity (15 points)
- PRD.pt-BR and PRD.en-US identical structure
- All sections/requirements/criteria match
- Technical terms consistent with glossario.md

**Deductions:**
- -5 structural mismatch
- -3 per missing/extra requirement
- -2 per inconsistent criteria
- -1 per glossary mismatch

### 4. Completeness (15 points)
- All requirements have acceptance criteria
- All ADRs complete (Context/Decision/Consequences/Status)
- No TODO/TBD/FIXME placeholders

**Deductions:**
- -3 per requirement without criteria
- -2 per incomplete ADR
- -1 per TODO/placeholder

### 5. Architecture Coherence (15 points)
- System-map reflects actual implementation
- No ghost services (documented but not implemented without clear status)
- ProactivityEngine, JWT Auth, Vector Search status clear

**Deductions:**
- -5 per ghost service
- -4 per undocumented service
- -2 per ambiguous status

### 6. Backlog Quality (10 points)
- All items reference PRD IDs in TraceIDs column
- All items reference ADRs where applicable
- Priorities assigned, estimates present

**Deductions:**
- -2 per missing PRD reference
- -1 per missing priority
- -0.5 per missing estimate

### 7. Glossary Consistency (5 points)
- All technical terms in PRDs exist in glossario.md
- Definitions consistent across documents

**Deductions:**
- -1 per undefined term
- -0.5 per inconsistent definition

## OUTPUT FORMAT

```markdown
# SparkOne PRD Validation Report — Iteration 1

## Overall Score: X/100

**Status:**
- [ ] READY TO FREEZE (100/100)
- [X] NEEDS CORRECTIONS (Score < 100)

## CRITICAL Issues (Blockers)
1. **[Title]** - Impact: [...] - Location: [file:line] - Fix: [...]

## HIGH Priority Issues
[Same format]

## MEDIUM Priority Issues
[Same format]

## LOW Priority Issues
[Same format]

## Detailed Analysis by Criterion

### 1. Requirement ID Consistency (X/20)
**Findings:** [specific evidence]
**Score Breakdown:** Base 20, Deductions: [...], **Final: X/20**

[Repeat for all 7 criteria]

## Specific Corrections Required

### Priority 1 (CRITICAL)
1. **[Action]** - File: [...] - Current: [...] - Required: [...]

### Priority 2 (HIGH)
[Same format]

### Priority 3 (MEDIUM)
[Same format]

## Summary
**Strengths:** [3-5 points]
**Weaknesses:** [3-5 points]
**Recommendations:** [prioritized actions]

## Next Steps
1. [Action in priority order]
```

## ANALYZE THESE FILES

@PRD.pt-BR.md @PRD.en-US.md @backlog.csv @decisions.md @system-map.md @inventory.json @glossario.md @coerencia.md @traceability.md

## INSTRUCTIONS

1. Check EVERY requirement ID, cross-reference, ADR link
2. Use specific line numbers when citing issues
3. Provide actionable corrections with exact paths
4. Score honestly - only 100/100 if truly production-ready
5. Verify PT-BR and EN-US are perfect mirrors
6. Validate traceability completely
7. Ensure status clarity everywhere

BEGIN VALIDATION NOW.
