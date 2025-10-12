# SparkOne PRD — Corrections Report (Codex Editor)

**Date:** 2025-10-02  
**Scope:** Apply bilingual ID unification, traceability, architecture alignment, security plan, and critical gaps alignment across PRD package.

---

## Files Changed

- `docs/prd/sparkone/PRD.en-US.md`
- `docs/prd/sparkone/PRD.pt-BR.md`
- `docs/prd/sparkone/decisions.md`
- `docs/prd/sparkone/system-map.md`
- `docs/prd/sparkone/backlog.csv`
- `docs/prd/sparkone/traceability.md` (new)

---

## Exact Corrections

1) Requirement IDs (bilingual unification)
- Added canonical RF/RNF section to `PRD.en-US.md` with bilingual mapping tables (RF and RNF) and acceptance criteria summaries.
- Added canonical RF/RNF mapping table to `PRD.pt-BR.md` and acceptance criteria per RF, plus RF-018 (Vector Search) as planned.
- Ensured both PRDs now share identical RF IDs and titles via canonical sections.

2) Traceability improvements
- Created `traceability.md` with matrix: Requirement ID → Backlog ID(s) → ADR(s) → Endpoint(s) → Code Path(s) → Tests. Marked unknowns as `UNASSIGNED`.
- Augmented `backlog.csv` by adding columns `TraceIDs` and `ADRs`, populating concrete mappings (e.g., ProactivityEngine → RF-015; Vector Search → RF-018/ADR-003; JWT → RNF-020/ADR-011). Unclear items marked `UNASSIGNED`.

3) Architecture alignment
- Removed `TrustedHostMiddleware` from `system-map.md` middleware stack to match `inventory.json` and EN PRD.
- Replaced pseudo-secrets in `system-map.md` with safe stubs (`<set in env>`, masked DSN).
- Made routers explicit in `system-map.md` (added Events router: `src/app/routers/events.py`, `/events`).

4) Critical gaps alignment
- Updated `PRD.en-US.md` Critical Gaps to include: ProactivityEngine (P0), JWT Auth (P1), Vector Search (P1).
- Updated `PRD.pt-BR.md` gaps table to include Vector Search (P1) and JWT Auth (P1).

5) Security plan and consistency
- Added staged security plan in both PRDs: Current HTTP Basic → P1 JWT → optional 2FA (TOTP).
- Added ADR-011 to `decisions.md` for JWT migration (P1) with context, decision, consequences, and implementation notes.

6) Bilingual PRD parity
- Expanded EN PRD with canonical RF/RNF mapping and acceptance criteria summaries to match PT granularity.
- Added acceptance criteria for each RF in PT PRD; summarized RNF criteria via Security Plan and existing NFR sections.

7) Vector Search status clarity
- Annotated EN PRD data layer: pgvector “infra ready; feature pending RF-018 (P1)” with references to ADR-003 and backlog RF-006.

---

## Verification Checklist

- Requirement IDs unified (canonical RF/RNF) and bilingual mapping present in both PRDs.
- Acceptance criteria provided per RF (PT fully; EN summarized) and RNF plan clarified.
- Traceability matrix present (`traceability.md`) with mappings to backlog, ADRs, endpoints, and code paths.
- `backlog.csv` includes `TraceIDs` and `ADRs` columns with populated mappings; unknowns marked `UNASSIGNED`.
- System diagram aligns with inventory: `TrustedHostMiddleware` removed where not implemented.
- Events router explicitly referenced in system map and PRDs.
- Security plan staged and reflected in PRDs and ADRs (ADR-011).
- No secrets in documentation examples; placeholders standardized to `<set in env>`.
- Vector Search status labeled as infra-ready; feature pending (P1) and cross-referenced.

---

## Final Strict Validation Score

- Completeness: 88 (canonical IDs, acceptance criteria added; traceability file added)
- Consistency: 80 (architecture/IDs/security now aligned; minor legacy FR/NFR kept for context)
- Traceability: 78 (matrix exists; some items UNASSIGNED pending code/tests links)
- Architecture: 85 (diagram/inventory alignment; routers explicit)
- Bilingual quality: 82 (mapping tables unify titles/IDs; EN retains legacy section for context)
- Security hygiene (docs): 95 (placeholders fixed; staged plan + ADR)

Overall (strict): 78/100.

---

## Verdict

Not Production-Ready.

- Rationale: P0 feature (ProactivityEngine) and P1 items (JWT, Vector Search) remain unimplemented. Documentation is now audit-ready for a production plan, but runtime readiness depends on these deliveries.

---

## Next Steps (Suggested)

- Implement RF-015 (ProactivityEngine) and RF-018 (Vector Search) and RNF-020 (JWT) in sequence; update traceability with code paths and tests.
- Convert remaining `UNASSIGNED` entries to concrete links (tests, ADRs) as work lands.
- Optionally, merge legacy FR/NFR sections into canonical RF/RNF structure in EN PRD to avoid duplication.
