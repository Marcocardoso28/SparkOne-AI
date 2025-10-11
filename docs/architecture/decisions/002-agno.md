# ADA-002: Orquestração Agno com Migração para LangGraph

**Data**: 2024-05-02  
**Status**: Aprovado  
**Contexto**: Escolha do sistema de orquestração de agentes de IA

## Decisão

Utilizar Agno como núcleo de orquestração; preparar migração gradual para LangGraph quando flows condicionais complexos forem necessários.

## Alternativas Consideradas

- **LangChain**: Framework maduro, mas com abstrações que limitam controle
- **CrewAI**: Framework especializado em agentes colaborativos, mas menos flexível

## Consequências

### Positivas
- Controle total sobre prompts e fluxos
- Flexibilidade para implementar lógica customizada
- Migração gradual possível

### Negativas
- Necessidade de investimento em testes ao migrar
- Maior complexidade inicial
- Dependência de implementação customizada

## Implementação

### Fase Atual (Agno)
- Orquestração básica de agentes
- Controle direto sobre prompts
- Integração com provedores de LLM

### Fase Futura (LangGraph)
- Fluxos condicionais complexos
- Estado persistente entre agentes
- Visualização de workflows

## Critérios de Migração

A migração para LangGraph será considerada quando:
- Necessidade de fluxos condicionais complexos
- Estado persistente entre agentes
- Visualização e debugging de workflows
- Performance superior comprovada

## Revisão

Esta decisão será revisada quando:
- Limitações do Agno se tornarem evidentes
- Necessidade de fluxos mais complexos
- Mudanças nos requisitos de orquestração
