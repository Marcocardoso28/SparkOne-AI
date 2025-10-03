# Architectural Decision Records (ADRs)
## SparkOne Project Decisions

**Last Updated:** January 2025  
**Status:** Active Documentation  

---

## ADR-001: FastAPI as Primary Web Framework

**Date:** 2024 (Inferred from implementation)  
**Status:** ✅ Accepted  
**Deciders:** Marco Cardoso, Development Team  

### Context
Need for a modern, high-performance web framework for the SparkOne personal assistant API with strong typing support and automatic documentation generation.

### Decision
Use FastAPI as the primary web framework instead of alternatives like Flask, Django, or Starlette.

**Source:** `src/app/main.py`, `pyproject.toml`

### Consequences

**Positive:**
- Automatic OpenAPI/Swagger documentation generation
- Built-in Pydantic validation and serialization
- High performance with async/await support
- Strong typing with Python type hints
- Modern development experience

**Negative:**
- Smaller ecosystem compared to Django
- Learning curve for team members unfamiliar with async Python
- Dependency on Pydantic for data validation

**Implementation Evidence:**
```python
# src/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SparkOne API",
    description="Personal Assistant API",
    version="0.1.0"
)
```

---

## ADR-002: Agno Bridge Pattern for Orchestration

**Date:** 2024 (Inferred from implementation)  
**Status:** ✅ Accepted (Temporary)  
**Deciders:** Marco Cardoso  

### Context
The Agno library for intelligent orchestration is still under development, but SparkOne needs message routing and classification capabilities immediately.

### Decision
Implement an "Agno Bridge" using LLM-based classification to emulate Agno behavior until the full library is ready for integration.

**Source:** `src/app/agents/agno.py`

### Consequences

**Positive:**
- Unblocks development while Agno library matures
- Provides immediate intelligent routing capabilities
- Allows experimentation with message classification
- Easier to test and debug than full Agno integration

**Negative:**
- Technical debt that requires future migration
- Potential performance overhead from LLM calls
- May not match exact Agno behavior
- Duplicate effort when migrating to full Agno

**Implementation Evidence:**
```python
# src/app/agents/agno.py
class AgnoBridge:
    """Temporary bridge to emulate Agno behavior using LLM classification"""
    
    async def classify_message(self, message: str) -> MessageType:
        # LLM-based classification logic
        pass
```

**Migration Plan:** Replace with full Agno library integration in Q1 2025.

---

## ADR-003: PostgreSQL with pgvector for Data Persistence

**Date:** 2024 (Inferred from implementation)  
**Status:** ✅ Accepted  
**Deciders:** Marco Cardoso, Development Team  

### Context
Need for a robust database solution that supports both relational data and vector embeddings for semantic search capabilities.

### Decision
Use PostgreSQL 15+ with the pgvector extension as the primary database, with SQLite as a fallback for local development.

**Source:** `docker-compose.yml`, `src/app/config.py`

### Consequences

**Positive:**
- Mature, reliable relational database
- Native vector search capabilities with pgvector
- Strong consistency and ACID properties
- Excellent Python ecosystem support (asyncpg, SQLAlchemy)
- Supports complex queries and relationships

**Negative:**
- Additional complexity compared to simpler databases
- Requires PostgreSQL-specific knowledge
- pgvector extension dependency
- Higher resource usage than SQLite

**Implementation Evidence:**
```yaml
# docker-compose.yml
db:
  image: pgvector/pgvector:pg15
  environment:
    POSTGRES_DB: sparkone
    POSTGRES_USER: sparkone
    POSTGRES_PASSWORD: sparkone
```

---

## ADR-004: Multi-Provider LLM Support

**Date:** 2024 (Inferred from implementation)  
**Status:** ✅ Accepted  
**Deciders:** Marco Cardoso  

### Context
Need flexibility in LLM providers for cost optimization, local deployment options, and vendor independence.

### Decision
Support multiple LLM providers (OpenAI, local models) with configurable switching via environment variables.

**Source:** `src/app/config.py`

### Consequences

**Positive:**
- Vendor independence and flexibility
- Cost optimization options
- Local deployment capability
- Fallback options for reliability

**Negative:**
- Increased configuration complexity
- Need to handle provider-specific differences
- Testing complexity across providers
- Potential inconsistency in responses

**Implementation Evidence:**
```python
# src/app/config.py
class SparkOneConfig(BaseSettings):
    openai_api_key: Optional[str] = Field(env="OPENAI_API_KEY")
    local_llm_url: Optional[str] = Field(env="LOCAL_LLM_URL")
    llm_provider: Literal["openai", "local"] = Field(default="openai")
```

---

## ADR-005: Redis for Caching and Rate Limiting

**Date:** 2024 (Inferred from implementation)  
**Status:** ✅ Accepted  
**Deciders:** Development Team  

### Context
Need for high-performance caching and distributed rate limiting across multiple application instances.

### Decision
Use Redis as the caching layer and rate limiting backend.

**Source:** `docker-compose.yml`, middleware implementation

### Consequences

**Positive:**
- High-performance in-memory operations
- Distributed rate limiting support
- Session storage capabilities
- Pub/sub for future real-time features

**Negative:**
- Additional infrastructure dependency
- Memory usage considerations
- Data volatility (not persistent by default)
- Network latency for cache operations

**Implementation Evidence:**
```yaml
# docker-compose.yml
cache:
  image: redis:7-alpine
  ports:
    - "6379:6379"
```

---

## ADR-006: Docker Compose for Local Development

**Date:** 2024 (Inferred from implementation)  
**Status:** ✅ Accepted  
**Deciders:** Development Team  

### Context
Need for consistent development environment that matches production infrastructure.

### Decision
Use Docker Compose for local development with PostgreSQL, Redis, and application services.

**Source:** `docker-compose.yml`

### Consequences

**Positive:**
- Consistent development environment
- Easy onboarding for new developers
- Production-like local setup
- Isolated service dependencies

**Negative:**
- Docker learning curve for team members
- Resource usage on development machines
- Potential performance overhead
- Complexity for simple changes

**Implementation Evidence:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - cache
```

---

## ADR-007: Comprehensive Security Middleware Stack

**Date:** 2024 (Inferred from implementation)  
**Status:** ✅ Accepted  
**Deciders:** Marco Cardoso, Security Review  

### Context
Need for production-ready security measures including CORS, rate limiting, security headers, and audit logging.

### Decision
Implement a comprehensive middleware stack with multiple security layers.

**Source:** `src/app/main.py`, middleware implementations

### Consequences

**Positive:**
- Defense in depth security approach
- Compliance with security best practices
- Audit trail for security events
- Protection against common web vulnerabilities

**Negative:**
- Performance overhead from multiple middleware layers
- Configuration complexity
- Potential for middleware conflicts
- Debugging complexity

**Implementation Evidence:**
```python
# src/app/main.py
app.add_middleware(CORSMiddleware, ...)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SecurityLoggingMiddleware)
```

---

## ADR-008: Structured Logging with Correlation IDs

**Date:** 2024 (Inferred from implementation)  
**Status:** ✅ Accepted  
**Deciders:** Development Team  

### Context
Need for comprehensive logging and request tracing across distributed services.

### Decision
Use structured logging with correlation IDs for request tracing and observability.

**Source:** Middleware implementation, logging configuration

### Consequences

**Positive:**
- Improved debugging and troubleshooting
- Request tracing across service boundaries
- Machine-readable log format
- Better observability and monitoring

**Negative:**
- Log volume increase
- Storage requirements
- Performance impact of logging
- Complexity in log analysis tools

---

## ADR-009: HTTP Basic Authentication for Web UI

**Date:** 2024 (Inferred from implementation)  
**Status:** ✅ Accepted  
**Deciders:** Marco Cardoso  

### Context
Need for simple authentication mechanism for the web interface without complex user management.

### Decision
Use HTTP Basic Authentication for the web UI with a single password.

**Source:** `src/app/routers/web.py`

### Consequences

**Positive:**
- Simple implementation and configuration
- No complex user management required
- Suitable for single-user personal assistant
- Standard HTTP authentication mechanism

**Negative:**
- Not suitable for multi-user scenarios
- Password transmitted with each request
- Limited security features (no 2FA, session management)
- Potential for credential exposure

**Future Consideration:** Upgrade to OAuth2 or JWT for multi-user support.

---

## ADR-010: Notion API for Task Management

**Date:** 2024 (Inferred from implementation)  
**Status:** ✅ Accepted  
**Deciders:** Marco Cardoso  

### Context
Need for integration with existing productivity workflow using Notion for task management.

### Decision
Integrate with Notion API for task synchronization while maintaining local PostgreSQL snapshots.

**Source:** `src/app/services/tasks.py`, `src/app/integrations/notion.py`

### Consequences

**Positive:**
- Leverages existing Notion workflow
- Rich task management features
- Familiar user interface
- API-based integration flexibility

**Negative:**
- External dependency on Notion service
- API rate limiting considerations
- Potential data synchronization issues
- Vendor lock-in for task management

**Implementation Evidence:**
```python
# src/app/integrations/notion.py
class NotionClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"
```

---

## Pending Decisions

### PD-001: Migration to Full Agno Library
**Status:** 🔄 In Planning
**Timeline:** Q1 2025 (March 2025 target)
**Owner:** Marco Cardoso (Lead Developer)
**Context:** Replace AgnoBridge with full Agno library integration
**Considerations:** API compatibility, performance impact, migration strategy
**Action Items:**
- Monitor Agno library release status (monthly check)
- Create migration plan document by Feb 2025
- Set up testing environment for Agno integration
- Allocate 2-week sprint for migration execution

### PD-002: CI/CD Pipeline Selection
**Status:** 🔄 In Planning
**Timeline:** Q1 2025 (February 2025 target)
**Owner:** DevOps Team / Marco Cardoso
**Context:** Automated testing and deployment pipeline
**Options:** GitHub Actions (preferred), GitLab CI, Jenkins
**Decision Criteria:** Cost, integration with GitHub, ease of setup
**Action Items:**
- Evaluate GitHub Actions workflow templates (by Jan 15)
- Set up basic CI pipeline with pytest (by Feb 1)
- Add deployment automation (by Feb 15)

### PD-003: Production Deployment Strategy
**Status:** 🔄 In Planning
**Timeline:** Q2 2025 (April-May 2025)
**Owner:** Infrastructure Team / Marco Cardoso
**Context:** Production hosting and infrastructure
**Options:** VPS with Docker (preferred for MVP), Kubernetes (future), Cloud providers
**Decision Criteria:** Cost, scalability, maintenance overhead
**Action Items:**
- Select VPS provider by March 2025
- Set up staging environment by April 2025
- Production deployment by May 2025

### PD-004: Multi-User Support Architecture
**Status:** 🔄 Future Consideration
**Timeline:** Q3 2025 (July-Sept 2025)
**Owner:** Architecture Team / Marco Cardoso
**Context:** Scaling beyond single-user personal assistant
**Considerations:** Authentication (JWT/OAuth), data isolation, resource management, billing
**Action Items:**
- Design multi-tenant database schema (Q2 2025)
- Implement user management system (Q3 2025)
- Add organization/team support (Q3 2025)

---

## Decision Review Process

### Review Schedule
- **Quarterly Review:** Assess active decisions and their outcomes
- **Pre-Major Release:** Review all architectural decisions
- **Post-Incident:** Review decisions related to incidents

### Review Criteria
1. **Technical Debt:** Is the decision creating unsustainable technical debt?
2. **Performance Impact:** Is the decision affecting system performance?
3. **Security Implications:** Are there new security considerations?
4. **Maintenance Burden:** Is the decision increasing maintenance complexity?
5. **Business Alignment:** Does the decision still align with business goals?

### Decision Modification Process
1. **Proposal:** Document proposed changes with rationale
2. **Impact Analysis:** Assess technical and business impact
3. **Stakeholder Review:** Get input from affected team members
4. **Implementation Plan:** Create migration/change plan
5. **Documentation Update:** Update ADR with new status

---

**Document Maintained By:** Development Team  
**Review Frequency:** Quarterly  
**Last Review:** January 2025

---

## ADR-011: JWT Authentication Migration (P1)

**Date:** 2025  
**Status:** ✅ Accepted (Planned execution in P1)  
**Deciders:** Marco Cardoso, Development Team

### Context
HTTP Basic is sufficient for a single-user internal web UI, but it is inadequate for broader usage, API expansion, and multi-client consumption. A migration path to JWT is required to strengthen authentication and enable future session/role features.

### Decision
Adopt JWT-based authentication for API/Web endpoints as P1 work, retaining HTTP Basic for the minimal web UI until JWT is fully integrated.

**Related Requirements:** RNF-007 (current), RNF-020 (target)  
**Related Backlog:** RF-007 “Implementar Autenticação JWT”  
**Dependencies:** `python-jose[cryptography]` (inventory.json), middleware/hooks integration

### Consequences

**Positive:**
- Stronger authentication model suitable for API clients
- Foundation for roles/permissions and token refresh
- Aligns security posture with production readiness

**Negative:**
- Additional implementation complexity (token issuance/refresh)
- Requires changes to clients/tooling

### Implementation Notes
- Introduce login/refresh endpoints and JWT validation middleware
- Preserve HTTP Basic temporarily for `/web` until parity is achieved
- Document token lifetime, refresh strategy, and rotation

**Review:** Upon completion, deprecate HTTP Basic for general API usage
