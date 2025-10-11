# SparkOne PRD — Independent Validation Report (Codex)

**Date:** 2025-10-02  
**Scope:** Validation of the SparkOne PRD package produced by Trae Agent.  
**Files reviewed (read-only):** `PRD.pt-BR.md`, `PRD.en-US.md`, `decisions.md`, `glossario.md`, `system-map.md`, `backlog.csv`, `coerencia.md`, `inventory.json`

---

## ✅ Strengths

- Solid documentation set: All eight artifacts exist and are materially filled with technical detail and current status.  
- Clear core architecture: FastAPI + PostgreSQL (pgvector) + Redis + Docker Compose consistently presented across PRD, system-map, and inventory.  
- Coherent feature picture: Implemented services (Tasks, Calendar, Coach, Brief) and missing ones (ProactivityEngine, Recommendation) are consistently identified.  
- Backlog coverage: P0/P1 work items for ProactivityEngine, Agno migration, CI/CD, Vector Search, and JWT Auth are present with acceptance criteria.  
- Observability and security baselines documented: Health/metrics endpoints, structured logs, security headers, rate limiting called out and reflected in inventory/system map.  
- ADRs present and meaningful: Decisions on FastAPI, Redis, pgvector, security middleware, and AgnoBridge captured with context and consequences.

---

## ⚠️ Issues

- Bilingual misalignment of requirement IDs
  - EN uses `FR-xxx`/`NFR-xxx` while PT uses `RF-xxx`/`RNF-xxx`. IDs and counts do not match across languages.  
    - EN Functional: `FR-001…FR-008` (8 items) (PRD.en-US.md:66).  
    - PT Functional: `RF-001…RF-017` (17 items) (PRD.pt-BR.md:59).  
  - Result: Cross-language traceability breaks. The backlog uses PT-style IDs (`RF-xxx`/`RNF-xxx`).

- Traceability gaps (PRD ↔ ADR ↔ Backlog ↔ Code)
  - Backlog items have a generic “Referência” to files/specs, but rarely map to ADR IDs (e.g., ADR-00x) or PRD requirement IDs.  
  - PRDs do not provide a bidirectional mapping table from each requirement to backlog line(s), ADR(s), affected endpoints, and code owners.  
  - Impact: Hard to audit coverage or prove completeness/consistency across artifacts.

- Architecture inconsistencies (diagram vs inventory)
  - `TrustedHostMiddleware` appears in `system-map.md` (system-map.md:305-314) but is not listed in `inventory.json` middleware or EN PRD security stack.  
  - `events` router exists in `inventory.json` (inventory.json:199) but is not explicit in the mermaid diagram; only implied via Calendar/Brief narratives.

- Security posture mismatches across docs
  - EN PRD shows “API endpoints: No authentication (internal use)” (PRD.en-US.md:210), while backlog plans JWT as P1 (backlog.csv:7). This needs a clear phase plan and risk statement.  
  - EN PRD claims “2FA support with TOTP” (PRD.en-US.md:191), but there is no user flow/acceptance criteria or cross-reference in backlog/routers to activate it.  
  - System-map includes environment examples with placeholders (e.g., `OPENAI_API_KEY=sk-...`, `WEB_PASSWORD=secure_password`) (system-map.md:392-397). Placeholders are fine, but it’s better to avoid even pseudo-secrets in docs.

- Critical gaps not uniformly reflected across artifacts
  - ProactivityEngine is P0 and consistently flagged. Vector Search and JWT Auth are flagged in backlog and coherence matrix, but not explicitly listed in the EN PRD “Critical Gaps” section (PRD.en-US.md:243-293).  
  - Suggest aligning “Critical Gaps” sections so Vector Search and Auth appear with P1 severity everywhere.

- Inventory vs PRD claims
  - `inventory.json` includes security dependency `python-jose` (inventory.json:49-57) suggesting JWT path, but PRD still centers HTTP Basic as mainline with no staged migration plan in EN PRD.  
  - Some routers in inventory (`/metrics`, `/events`) do not show explicit acceptance criteria or requirement linkage in PRD.

- Bilingual content parity
  - PT PRD includes more granular requirements (RF-001..017) and references, while EN PRD aggregates into fewer FR items and lacks explicit acceptance criteria per requirement.  
  - Risk: The EN document cannot be used as a faithful mirror for audits.

- Minor content consistency
  - `Vector Search` is described as “infra ready, not used” (coerencia.md:141-148) but also appears in PRD EN “Data Layer” (PRD.en-US.md:30-41) without an explicit “not used” note. This can mislead readers about availability.

---

## 🔍 Score Validation (Coherence 76%)

- The “Score Geral do Projeto” in `coerencia.md` lists five dimension scores: 85, 78, 82, 75, 60 (coerencia.md:217-228).  
- Average = (85 + 78 + 82 + 75 + 60) / 5 = 76.0%.  
- Verdict: The stated coherence score of 76% is arithmetically accurate given the dimensions provided.  
- Caveat: This is a documentation/process coherence metric, not a production readiness score.

---

## 🔍 Security Hygiene Check (docs only)

- Searched the reviewed files for common secret patterns. Only placeholders found in `system-map.md` (e.g., `sk-...`, `secret_...`, `secure_password`) (system-map.md:392-397).  
- No actual tokens or secrets were present in the reviewed files.

---

## 🔍 Critical Gaps Alignment

- ProactivityEngine: Marked P0 consistently in PT PRD (PRD.pt-BR.md:130) and EN PRD (PRD.en-US.md:148) and backlog (backlog.csv:2).  
- Vector Search: Present in backlog as P1 (backlog.csv:6) and in coherence matrix as “infra ready, not used” (coerencia.md:141-148); not explicitly listed as a gap in EN PRD’s Critical Gaps.  
- Auth: JWT Auth present in backlog as P1 (backlog.csv:7) and coherence matrix flags HTTP Basic limitations (coerencia.md:168-180). EN PRD lacks a clear staged auth migration plan.

---

## 🔍 Bilingual Quality

- IDs and granularity differ: EN (FR/NFR) vs PT (RF/RNF). Numbers do not align.  
- PT PRD has detailed RF/RNF breakdown; EN PRD collapses multiple PT RFs into broader FRs.  
- Result: Cross-references (e.g., backlog → PRD EN) are not reliable without a mapping table.

---

## 🔍 Architecture vs Inventory

- High-level mapping is strong: Components and integrations in the mermaid diagram match `inventory.json` (services, integrations, data stores, middleware).  
- Notable inconsistencies:
  - `TrustedHostMiddleware` shown only in diagram; not present in `inventory.json` or EN PRD middleware lists.  
  - `events` router present in `inventory.json` but not explicit in diagram; ensure diagram shows all public endpoints (especially those audited in NFRs).

---

## 🔧 Recommendations

- Unify requirement IDs across languages
  - Adopt `RF-xxx`/`RNF-xxx` in both EN and PT PRDs.  
  - Provide a bilingual mapping table: each PT `RF-xxx` maps to EN `RF-xxx` with identical scope/title.

- Add a formal Traceability Matrix
  - Columns: `Requirement ID` → `Backlog ID(s)` → `ADR(s)` → `Endpoints` → `Code Path(s)` → `Tests`.  
  - Require backlog “Referência” to include ADR IDs (ADR-00x) and PRD IDs (RF-xxx/RNF-xxx) where applicable.

- Align “Critical Gaps” across all artifacts
  - Ensure Vector Search and JWT Auth appear in EN PRD Critical Gaps with P1.  
  - Add an explicit staged security plan: HTTP Basic (current) → JWT (P1) → optional 2FA enablement and session management.

- Normalize middleware inventory
  - Either implement and list `TrustedHostMiddleware` in `inventory.json` and EN PRD, or remove it from the diagram to avoid confusion.  
  - Add acceptance criteria for `/metrics` and `/events` where missing.

- Clarify Vector Search status
  - In PRD EN, explicitly annotate pgvector as “infra ready; feature P1 pending” and link to backlog item RF for discoverability.

- Improve EN PRD parity
  - Add acceptance criteria per FR.  
  - Mirror the granularity of PT RFs to ensure cross-language audits produce the same coverage.

- Security doc hygiene
  - Replace pseudo-secrets in docs with safe stubs (e.g., `OPENAI_API_KEY=<set in env>`).  
  - Add a “Secrets Handling” subsection that points to secure storage guidance and rotation policy.

---

## Overall Score (Strict)

- Completeness: 80 — strong set of artifacts with real content.  
- Consistency: 70 — mostly aligned; some cross-doc mismatches.  
- Traceability: 60 — references exist but lack ADR/ID linkage and a coverage matrix.  
- Architecture: 80 — diagrams and inventory largely match with a few omissions.  
- Bilingual quality: 55 — IDs and granularity diverge; EN parity missing.  
- Security hygiene (docs): 90 — no secrets in reviewed docs; auth migration needs planning.  

Weighted overall (strict): 70/100.

---

## Final Verdict

Usable as draft.

- Not production-ready due to missing P0/P1 features (ProactivityEngine, JWT Auth, Vector Search), uneven bilingual alignment, and incomplete traceability.  
- With the recommended alignment/mapping and a short focused effort on P0/P1 items, the PRD package can reach a production-ready documentation state.

---

## Appendices (Key References)

- EN PRD FR list: `PRD.en-US.md:66, 80, 99, 120, 134, 142, 148, 156`  
- PT PRD RF list: `PRD.pt-BR.md:59, 64, 69, 74, 82, 87, 92, 96, 100, 105, 111, 115, 120, 125, 130, 134, 138`  
- Coherence dimension scores: `coerencia.md:217-228`  
- Middleware mismatch mention (TrustedHost): `system-map.md:305-314` vs `inventory.json:229-262`  
- Backlog criticals: `backlog.csv:2-7`  
- Security placeholders: `system-map.md:392-397`

