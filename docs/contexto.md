# SparkOne — Contexto Consolidado (2025)

## Visão
Criar um copiloto pessoal que combina ingestão multicanal (WhatsApp, Web, Sheets) com agentes especializados para lembrar compromissos, organizar tarefas e responder com a persona "SparkOne".

## Objetivos 2025H1
- Entregar um assistente confiável para uso diário focando em tarefas, agenda e briefs automáticos.
- Garantir privacidade e segurança adequadas para dados pessoais (LGPD-ready).
- Abrir caminho para operação autônoma (integração com agentes externos e automação de rotinas).

## Domínios Principais
- **Interação**: canais (WhatsApp, Web UI), normalização e prompts.
- **Produtividade**: tarefas (Notion), agenda (Google/CalDAV), briefings.
- **Conhecimento**: ingestão de documentos e busca semântica.
- **Infraestrutura**: observabilidade, automação de back-ups, segurança e conformidade.

## Casos de Uso Prioritários
1. Receber tarefas via WhatsApp e sincronizar com Notion/Sheets.
2. Consolidar agenda, tarefas e últimos contatos em um briefing matinal.
3. Registrar insights (voz/texto) e armazenar em memória longa para consultas futuras.
4. Disparar alertas proativos (ex.: compromissos em conflito, mensagens sem resposta).

## Macro-Arquitetura
```text
Canais → Normalizador → Orquestração (Agno) → Serviços Domínio → Persistência (PostgreSQL + Redis + pgvector)
                                          ↘ Observabilidade / Alertas ↘ Webhooks externos
```

## Princípios
- **Modular**: separar interfaces (routers), domínio (services), integrações e infraestrutura.
- **Seguro por padrão**: rate limiting, logging com rastreabilidade, política de segredos rígida.
- **Observável**: métricas de ponta a ponta (ingestão → resposta) e tracing distribuído.
- **Automatizado**: provisionamento via Docker/Compose, testes em CI, pipelines de backup.
