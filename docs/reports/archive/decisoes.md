# SparkOne — Registro de Decisões (ADA format)

## ADA-001 — FastAPI + Estrutura em camadas
- **Data**: 2024-03-18
- **Decisão**: manter FastAPI com routers finos, services aplicacionais e integrações externas desacopladas.
- **Alternativas**: Litestar, Django Rest Framework.
- **Consequências**: compatibilidade com stack atual, menor esforço de migração; revisão prevista caso serviço cresça para multi-tenant.

## ADA-002 — Orquestração Agno com plano de migração para LangGraph
- **Data**: 2024-05-02
- **Decisão**: utilizar Agno como núcleo de orquestração; preparar migração gradual para LangGraph quando flows condicionais complexos forem necessários.
- **Alternativas**: LangChain, CrewAI.
- **Consequências**: controle total sobre prompts; necessidade de investimento em testes ao migrar.

## ADA-003 — Persistência (PostgreSQL + Redis + pgvector)
- **Data**: 2024-04-10
- **Decisão**: PostgreSQL 15 com extensão pgvector como banco primário; Redis para cache/rate limiting.
- **Alternativas**: Supabase, Neon + Qdrant, DynamoDB.
- **Consequências**: stack conhecida; requer monitoração de storage vetorial e backups automatizados.

## ADA-004 — Segurança web com camadas incrementais
- **Data**: 2024-08-22
- **Decisão**: manter auth básica na Web UI em MVP com roadmap para OAuth2 + MFA e secret scanning automatizado.
- **Alternativas**: Auth0, Clerk, Cloudflare Access.
- **Consequências**: simplicidade imediata; exige reforço antes de exposição pública.

## ADA-005 — Gestão de conhecimento com pipelines controlados
- **Data**: 2024-09-30
- **Decisão**: ingestion de documentos via scripts dedicados + revisão manual com tagging.
- **Alternativas**: automação via agentes autônomos completos.
- **Consequências**: curadoria mais lenta porém segura; investimento em metadados para escalar.
