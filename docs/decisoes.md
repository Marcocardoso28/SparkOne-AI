# Decisões Arquiteturais do SparkOne

## ADR-001: Escolha do Framework Web (FastAPI)

**Status**: Aceito  
**Data**: 2024  
**Contexto**: Necessidade de um framework web assíncrono para alta performance

**Decisão**: Utilizar FastAPI como framework principal

**Justificativa**:
- Suporte nativo a async/await
- Documentação automática com OpenAPI/Swagger
- Validação automática com Pydantic
- Excelente performance comparado a Flask/Django
- Ecossistema maduro para APIs REST

**Consequências**:
- ✅ Alta performance para operações I/O intensivas
- ✅ Documentação automática da API
- ✅ Type hints nativos
- ⚠️ Curva de aprendizado para programação assíncrona

---

## ADR-002: Arquitetura de Orquestração (Agno vs LangGraph)

**Status**: Aceito (MVP), Evoluindo (Trilha Avançada)  
**Data**: 2024  
**Contexto**: Necessidade de orquestrar múltiplos agentes especializados

**Decisão**: 
- **MVP**: Agno Orchestrator customizado
- **Trilha Avançada**: Migração para LangGraph

**Justificativa**:
- Agno oferece controle total sobre o fluxo
- LangGraph fornece handoffs inteligentes e estado compartilhado
- Migração gradual permite validação da arquitetura

**Consequências**:
- ✅ Flexibilidade total no MVP
- ✅ Preparação para multiagente avançado
- ⚠️ Necessidade de migração futura

---

## ADR-003: Banco de Dados (PostgreSQL + pgvector)

**Status**: Aceito  
**Data**: 2024  
**Contexto**: Necessidade de persistência relacional e busca vetorial

**Decisão**: PostgreSQL 15+ com extensão pgvector

**Justificativa**:
- ACID compliance para dados críticos
- pgvector para embeddings sem banco adicional
- Maturidade e confiabilidade
- Suporte nativo no SQLAlchemy

**Consequências**:
- ✅ Consistência transacional
- ✅ Busca semântica integrada
- ✅ Backup e recovery maduros
- ⚠️ Possível limitação de escala para vetores (migração futura para Qdrant)

---

## ADR-004: Cache e Filas (Redis)

**Status**: Aceito  
**Data**: 2024  
**Contexto**: Necessidade de cache, TTL e processamento assíncrono

**Decisão**: Redis 7 para cache, sessões e filas

**Justificativa**:
- Performance excepcional para cache
- TTL nativo para recomendações
- Pub/Sub para eventos
- Rate limiting integrado

**Consequências**:
- ✅ Performance de cache excelente
- ✅ Funcionalidades avançadas (TTL, Pub/Sub)
- ⚠️ Dependência adicional na infraestrutura

---

## ADR-005: Autenticação Web (Básica vs OAuth2)

**Status**: Aceito (MVP), Evoluindo  
**Data**: 2024  
**Contexto**: Necessidade de proteger a interface web

**Decisão**: 
- **MVP**: Autenticação básica com senha
- **Futuro**: OAuth2 + MFA para produção

**Justificativa**:
- Simplicidade para desenvolvimento local
- Segurança adequada para uso pessoal
- Preparação para autenticação robusta

**Consequências**:
- ✅ Implementação rápida
- ✅ Segurança básica adequada
- ⚠️ Limitações para uso multiusuário

---

## ADR-006: Integração WhatsApp (Evolution API)

**Status**: Aceito  
**Data**: 2024  
**Contexto**: Necessidade de integração com WhatsApp Business

**Decisão**: Utilizar Evolution API como ponte

**Justificativa**:
- API REST simples e documentada
- Suporte a webhooks
- Comunidade ativa no Brasil
- Alternativa ao WhatsApp Business API oficial

**Consequências**:
- ✅ Integração rápida e funcional
- ✅ Custo reduzido comparado à API oficial
- ⚠️ Dependência de projeto terceirizado

---

## ADR-007: Gerenciamento de Tarefas (Notion)

**Status**: Aceito  
**Data**: 2024  
**Contexto**: Necessidade de integração com sistema de produtividade

**Decisão**: Notion como backend principal para tarefas

**Justificativa**:
- API robusta e bem documentada
- Interface familiar para usuários
- Flexibilidade de estrutura de dados
- Sincronização bidirecional

**Consequências**:
- ✅ UX familiar para gerenciamento
- ✅ Flexibilidade de organização
- ⚠️ Dependência de serviço externo

---

## ADR-008: Calendários (CalDAV + Google Calendar)

**Status**: Aceito  
**Data**: 2024  
**Contexto**: Suporte a diferentes provedores de calendário

**Decisão**: Implementar adaptadores para CalDAV e Google Calendar

**Justificativa**:
- CalDAV é padrão aberto
- Google Calendar tem ampla adoção
- Flexibilidade de escolha por usuário
- Arquitetura de adaptadores reutilizável

**Consequências**:
- ✅ Compatibilidade ampla
- ✅ Flexibilidade de escolha
- ⚠️ Complexidade adicional de manutenção

---

## ADR-009: Embeddings (OpenAI vs Local)

**Status**: Aceito (Híbrido)  
**Data**: 2024  
**Contexto**: Necessidade de embeddings para busca semântica

**Decisão**: Suporte a OpenAI e modelos locais (nomic-embed)

**Justificativa**:
- OpenAI oferece qualidade superior
- Modelos locais garantem privacidade
- Configuração flexível por ambiente

**Consequências**:
- ✅ Flexibilidade de deployment
- ✅ Opção de privacidade total
- ⚠️ Complexidade de configuração

---

## ADR-010: Testes (pytest + TestClient)

**Status**: Aceito  
**Data**: 2024  
**Contexto**: Necessidade de cobertura de testes robusta

**Decisão**: pytest com FastAPI TestClient e fixtures assíncronas

**Justificativa**:
- pytest é padrão na comunidade Python
- TestClient integra perfeitamente com FastAPI
- Fixtures assíncronas para testes de integração
- Mocking flexível para dependências externas

**Consequências**:
- ✅ Testes rápidos e confiáveis
- ✅ Cobertura de integração real
- ✅ Mocking de APIs externas

---

## ADR-011: Observabilidade (structlog + Prometheus)

**Status**: Aceito  
**Data**: 2024  
**Contexto**: Necessidade de monitoramento e debugging

**Decisão**: structlog para logging, Prometheus para métricas

**Justificativa**:
- structlog oferece logs estruturados
- Prometheus é padrão para métricas
- Integração com Grafana para dashboards
- Correlação de requests

**Consequências**:
- ✅ Debugging eficiente
- ✅ Monitoramento proativo
- ✅ Alertas automatizados

---

## ADR-012: Containerização (Docker Compose)

**Status**: Aceito  
**Data**: 2024  
**Contexto**: Necessidade de ambiente reproduzível

**Decisão**: Docker Compose para desenvolvimento local

**Justificativa**:
- Ambiente consistente entre desenvolvedores
- Isolamento de dependências
- Facilita CI/CD
- Preparação para Kubernetes

**Consequências**:
- ✅ Ambiente reproduzível
- ✅ Onboarding simplificado
- ✅ Preparação para produção

---

## Decisões Pendentes

### DP-001: Migração para Litestar
**Status**: Em Avaliação  
**Contexto**: Litestar oferece ~30% mais throughput que FastAPI

### DP-002: Implementação CISA AI Security
**Status**: Planejado  
**Contexto**: Guidelines de segurança para sistemas de IA

### DP-003: Migração pgvector → Qdrant
**Status**: Futuro  
**Contexto**: Qdrant oferece performance superior para vetores

---

## Princípios de Decisão

1. **Simplicidade primeiro**: Escolher soluções simples que funcionem
2. **Evolução gradual**: Permitir migração incremental
3. **Padrões da comunidade**: Preferir soluções amplamente adotadas
4. **Testabilidade**: Priorizar arquiteturas testáveis
5. **Observabilidade**: Garantir visibilidade do sistema
6. **Segurança por design**: Considerar segurança desde o início