# Notes de Alinhamento - ProactivityEngine
## Riscos, Premissas e Esclarecimentos

**Versão:** 1.0  
**Data:** Janeiro 2025  
**Status:** Documento de Alinhamento  
**Baseline:** baseline_v1.md (Score: 78/100)  

---

## Resumo Executivo

Este documento consolida **riscos críticos**, **premissas técnicas** e **esclarecimentos necessários** identificados durante a análise do PRD baseline para implementação do **ProactivityEngine**. O objetivo é garantir alinhamento entre stakeholders e mitigar bloqueadores antes da execução.

---

## Premissas Técnicas

### **P1: Arquitetura Worker Container**
**Status:** ✅ Validada  
**Descrição:** Implementação de container separado para processamento assíncrono  
**Justificativa:** Separar responsabilidades entre API (síncrona) e jobs (assíncronos)  
**Impacto:** Requer modificação no `docker-compose.yml` e nova imagem Docker  

**Validação Necessária:**
- [ ] Confirmar recursos de infraestrutura disponíveis para container adicional
- [ ] Validar estratégia de deployment em produção (orquestração)
- [ ] Definir política de restart e health checks

### **P2: APScheduler como Scheduler Principal**
**Status:** ✅ Validada (ADR-007)  
**Descrição:** Uso do APScheduler para automação temporal  
**Justificativa:** Biblioteca madura, integração nativa com Python/FastAPI  
**Alternativas Consideradas:** Celery, Cron, Kubernetes CronJobs  

**Validação Necessária:**
- [ ] Confirmar que APScheduler atende requisitos de escala (100+ usuários)
- [ ] Validar estratégia de persistência de jobs (PostgreSQL vs Redis)
- [ ] Definir política de retry e dead letter queue

### **P3: Evolution API como Canal Principal**
**Status:** ⚠️ Dependência Externa  
**Descrição:** WhatsApp como canal primário para notificações proativas  
**Justificativa:** Canal já integrado e preferido pelo usuário  
**Risco:** Dependência de serviço terceirizado  

**Validação Necessária:**
- [ ] Confirmar SLA e disponibilidade da Evolution API
- [ ] Validar rate limits e custos de mensagens proativas
- [ ] Definir estratégia de fallback (email, push, logs)

### **P4: Timezone e Localização**
**Status:** ⚠️ Requer Esclarecimento  
**Descrição:** Configuração de timezone para schedules automáticos  
**Premissa Atual:** `America/Sao_Paulo` como padrão  
**Risco:** Usuários em timezones diferentes  

**Esclarecimentos Necessários:**
- [ ] **UNKNOWN:** SparkOne suportará múltiplos usuários com timezones diferentes?
- [ ] **UNKNOWN:** Como configurar timezone por usuário?
- [ ] **UNKNOWN:** Horário de brief diário será configurável por usuário?

---

## Riscos Críticos

### **R1: Dependência da Evolution API**
**Probabilidade:** Média (30%)  
**Impacto:** Alto  
**Categoria:** Dependência Externa  

**Descrição:** Evolution API pode ficar indisponível ou ter rate limiting inesperado  
**Cenários de Falha:**
- API retorna 5xx por períodos prolongados
- Rate limiting mais restritivo que esperado
- Mudanças na API sem aviso prévio
- Problemas de conectividade de rede

**Mitigações Propostas:**
1. **Retry Logic:** 3 tentativas com backoff exponencial
2. **Circuit Breaker:** Parar tentativas após falhas consecutivas
3. **Fallback:** Log estruturado quando WhatsApp falhar
4. **Monitoramento:** Alertas para taxa de falha > 5%
5. **Backup Channel:** Preparar integração com email (futuro)

**Ações Imediatas:**
- [ ] Implementar mock da Evolution API para testes
- [ ] Configurar monitoramento de disponibilidade
- [ ] Documentar procedimento de fallback

### **R2: Sobrecarga de Notificações**
**Probabilidade:** Alta (60%)  
**Impacto:** Médio  
**Categoria:** Experiência do Usuário  

**Descrição:** Usuário pode receber notificações excessivas, causando spam  
**Cenários de Problema:**
- Múltiplas tarefas com deadline no mesmo dia
- Eventos consecutivos com lembretes sobrepostos
- Brief diário + lembretes simultâneos
- Falha no rate limiting

**Mitigações Propostas:**
1. **Rate Limiting Rigoroso:** 60 notificações/hora por usuário
2. **Agrupamento Inteligente:** Consolidar lembretes similares
3. **Configuração de Usuário:** Permitir desabilitar tipos de notificação
4. **Quiet Hours:** Não enviar notificações entre 22h-7h
5. **Deduplicação:** Evitar lembretes duplicados para mesma tarefa/evento

**Ações Imediatas:**
- [ ] Definir política de agrupamento de notificações
- [ ] Implementar configurações de usuário para frequência
- [ ] Criar dashboard para monitorar volume de notificações

### **R3: Performance do Worker Container**
**Probabilidade:** Média (40%)  
**Impacto:** Alto  
**Categoria:** Performance  

**Descrição:** Worker pode não conseguir processar jobs em tempo hábil  
**Cenários de Problema:**
- Queries lentas para buscar tarefas/eventos próximos
- Concorrência insuficiente para múltiplos usuários
- Memory leaks em jobs de longa duração
- Deadlocks entre jobs simultâneos

**Mitigações Propostas:**
1. **Otimização de Queries:** Índices específicos para deadline/datetime
2. **Concorrência Configurável:** `WORKER_CONCURRENCY=4` (ajustável)
3. **Timeout de Jobs:** Máximo 30 segundos por job
4. **Monitoramento:** Métricas de latência e throughput
5. **Scaling Horizontal:** Preparar para múltiplos workers (futuro)

**Ações Imediatas:**
- [ ] Criar índices otimizados no PostgreSQL
- [ ] Implementar timeout e circuit breaker nos jobs
- [ ] Configurar métricas de performance

### **R4: Falhas de Sincronização**
**Probabilidade:** Média (35%)  
**Impacto:** Alto  
**Categoria:** Integridade de Dados  

**Descrição:** Dessincronia entre dados locais e APIs externas (Notion, Google)  
**Cenários de Problema:**
- Tarefa deletada no Notion mas lembrete ainda ativo
- Evento cancelado no Google Calendar mas notificação enviada
- Race conditions entre sync e jobs de lembrete
- Dados stale no cache Redis

**Mitigações Propostas:**
1. **Validação Pré-Envio:** Verificar existência antes de enviar lembrete
2. **TTL Agressivo:** Cache Redis com TTL de 5 minutos
3. **Sync Frequente:** Sincronização a cada 15 minutos
4. **Graceful Degradation:** Continuar funcionando com dados locais
5. **Reconciliação:** Job diário para corrigir inconsistências

**Ações Imediatas:**
- [ ] Implementar validação pré-envio de lembretes
- [ ] Configurar TTL otimizado no Redis
- [ ] Criar job de reconciliação diária

---

## Esclarecimentos Necessários

### **E1: Modelo de Usuários**
**Status:** ⚠️ UNKNOWN  
**Criticidade:** Alta  

**Questões Pendentes:**
- SparkOne é single-user ou multi-user?
- Como identificar usuário para notificações personalizadas?
- Configurações de notificação são globais ou por usuário?
- Como gerenciar timezones diferentes?

**Impacto na Implementação:**
- Estrutura de dados (user_id em todas as tabelas?)
- Configuração de schedules (global vs por usuário)
- Rate limiting (global vs por usuário)
- Personalização de horários

**Recomendação:**
Assumir **single-user** para MVP, preparar estrutura para **multi-user** futuro

### **E2: Estratégia de Fallback**
**Status:** ⚠️ UNKNOWN  
**Criticidade:** Média  

**Questões Pendentes:**
- O que fazer quando Evolution API falhar?
- Usuário deve ser notificado sobre falhas de entrega?
- Existe canal alternativo (email, push) disponível?
- Como recuperar notificações perdidas?

**Impacto na Implementação:**
- Arquitetura de retry e fallback
- Logging e auditoria de falhas
- Interface para reenvio manual
- Integração com canais alternativos

**Recomendação:**
Implementar **logging estruturado** como fallback mínimo, preparar para **email** futuro

### **E3: Configurações de Usuário**
**Status:** ⚠️ UNKNOWN  
**Criticidade:** Média  

**Questões Pendentes:**
- Usuário pode configurar horário do brief diário?
- Usuário pode desabilitar tipos específicos de lembrete?
- Como configurar antecedência de lembretes (2h para tarefas, 30min para eventos)?
- Existe interface web para configurações?

**Impacto na Implementação:**
- Modelo de dados para configurações
- API endpoints para CRUD de configurações
- Interface web (se necessária)
- Validação de configurações

**Recomendação:**
Implementar **configurações básicas** via variáveis de ambiente, preparar para **interface web** futuro

### **E4: Integração com Agno Library**
**Status:** ⚠️ UNKNOWN  
**Criticidade:** Baixa (P1)  

**Questões Pendentes:**
- Quando a biblioteca Agno estará disponível?
- ProactivityEngine deve ser compatível com Agno desde o início?
- Como migrar de AgnoBridge para Agno sem breaking changes?
- Agno terá funcionalidades de scheduling nativas?

**Impacto na Implementação:**
- Arquitetura de interfaces (preparar para migração)
- Abstração de dependências
- Estratégia de migração
- Compatibilidade de APIs

**Recomendação:**
Focar em **AgnoBridge** para MVP, criar **interfaces abstratas** para facilitar migração futura

---

## Decisões Arquiteturais Pendentes

### **DA1: Persistência de Jobs**
**Opções:**
1. **PostgreSQL:** Consistência, queries complexas, auditoria
2. **Redis:** Performance, TTL automático, simplicidade
3. **Híbrido:** Redis para queue, PostgreSQL para histórico

**Recomendação:** **Híbrido** - Redis para job queue, PostgreSQL para job history
**Justificativa:** Melhor performance + auditoria completa

### **DA2: Estratégia de Retry**
**Opções:**
1. **Exponential Backoff:** 1s, 2s, 4s, 8s
2. **Fixed Interval:** 30s entre tentativas
3. **Immediate + Delayed:** Imediato, depois 5min, depois 1h

**Recomendação:** **Exponential Backoff** com máximo de 3 tentativas
**Justificativa:** Padrão da indústria, evita sobrecarga

### **DA3: Granularidade de Configuração**
**Opções:**
1. **Global:** Configurações aplicam para todos os usuários
2. **Por Usuário:** Cada usuário tem configurações próprias
3. **Por Tipo:** Configurações diferentes para tarefas vs eventos

**Recomendação:** **Global** para MVP, **Por Usuário** para futuro
**Justificativa:** Simplicidade inicial, escalabilidade futura

---

## Matriz de Dependências Críticas

| Componente | Depende De | Tipo | Criticidade | Status |
|------------|------------|------|-------------|--------|
| ProactivityEngine | Worker Container | Técnica | Alta | ⚠️ Não Implementado |
| Worker Container | APScheduler | Técnica | Alta | ⚠️ Não Implementado |
| NotificationManager | Evolution API | Externa | Alta | ✅ Disponível |
| Daily Brief Job | BriefService | Técnica | Média | ✅ Implementado |
| TaskMonitor | TaskService | Técnica | Média | ✅ Implementado |
| EventMonitor | CalendarService | Técnica | Média | ✅ Implementado |
| Job Persistence | PostgreSQL | Técnica | Alta | ✅ Disponível |
| Job Queue | Redis | Técnica | Alta | ✅ Disponível |

---

## Plano de Mitigação de Riscos

### **Fase 1: Preparação (Antes do Sprint 1)**
- [ ] **Validar Evolution API:** Testar rate limits e disponibilidade
- [ ] **Configurar Monitoramento:** Métricas básicas de infraestrutura
- [ ] **Preparar Mocks:** Evolution API mock para testes
- [ ] **Otimizar Queries:** Criar índices necessários no PostgreSQL

### **Fase 2: Implementação (Durante Sprints)**
- [ ] **Implementar Retry Logic:** Em todos os pontos de falha
- [ ] **Configurar Rate Limiting:** Rigoroso desde o início
- [ ] **Logging Estruturado:** Para auditoria e debugging
- [ ] **Health Checks:** Para todos os componentes críticos

### **Fase 3: Validação (Pós-Implementação)**
- [ ] **Testes de Carga:** Simular múltiplos usuários
- [ ] **Testes de Falha:** Simular indisponibilidade da Evolution API
- [ ] **Monitoramento Contínuo:** Alertas para métricas críticas
- [ ] **Documentação:** Runbooks para troubleshooting

---

## Critérios de Go/No-Go

### **Critérios Obrigatórios (Go)**
- [ ] Evolution API disponível e funcional
- [ ] PostgreSQL e Redis configurados
- [ ] Docker Compose funcional para desenvolvimento
- [ ] Testes unitários com cobertura > 80%
- [ ] Logging estruturado implementado

### **Critérios de Bloqueio (No-Go)**
- [ ] Evolution API indisponível por > 24h
- [ ] Falhas críticas em testes de integração
- [ ] Performance inaceitável (> 30s para jobs)
- [ ] Problemas de segurança identificados
- [ ] Recursos de infraestrutura insuficientes

---

## Próximos Passos

### **Ações Imediatas (Antes da Implementação)**
1. **Validar Premissas:** Confirmar modelo de usuários e configurações
2. **Esclarecer Unknowns:** Definir estratégias de fallback e personalização
3. **Preparar Infraestrutura:** Configurar monitoramento e mocks
4. **Alinhar Stakeholders:** Revisar riscos e mitigações

### **Durante a Implementação**
1. **Monitoramento Contínuo:** Acompanhar métricas de risco
2. **Validação Incremental:** Testar cada componente isoladamente
3. **Documentação Ativa:** Atualizar decisões e aprendizados
4. **Comunicação Regular:** Status updates sobre riscos e bloqueadores

### **Pós-Implementação**
1. **Retrospectiva:** Avaliar efetividade das mitigações
2. **Otimização:** Ajustar configurações baseado em dados reais
3. **Planejamento P1:** Preparar próximas funcionalidades
4. **Documentação Final:** Consolidar lições aprendidas

---

**Documento Preparado por:** Execution Agent  
**Baseado em:** PRD Baseline v1.0, execution_plan_proactivity.md  
**Próxima Revisão:** Após validação de premissas e esclarecimentos  
**Status:** Aguardando validação de stakeholders