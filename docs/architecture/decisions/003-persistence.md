# ADA-003: Persistência PostgreSQL + Redis + pgvector

**Data**: 2024-04-10  
**Status**: Aprovado  
**Contexto**: Escolha da stack de persistência de dados

## Decisão

PostgreSQL 15 com extensão pgvector como banco primário; Redis para cache/rate limiting.

## Alternativas Consideradas

- **Supabase**: PostgreSQL gerenciado com recursos extras, mas dependência de vendor
- **Neon + Qdrant**: PostgreSQL serverless + vector DB dedicado, mas maior complexidade
- **DynamoDB**: NoSQL gerenciado, mas menos adequado para dados relacionais

## Consequências

### Positivas
- Stack conhecida e madura
- PostgreSQL com pgvector para busca semântica
- Redis para performance e rate limiting
- Suporte a transações ACID

### Negativas
- Requer monitoração de storage vetorial
- Backups automatizados necessários
- Configuração manual de replicação

## Implementação

### PostgreSQL
- Banco principal para dados relacionais
- Extensão pgvector para embeddings
- Migrações com Alembic

### Redis
- Cache de sessões
- Rate limiting
- Filas de tarefas

### Backup Strategy
- Backups automatizados diários
- Restore em ambiente de teste
- Monitoração de integridade

## Monitoramento

- Métricas de performance do PostgreSQL
- Uso de memória do Redis
- Integridade dos backups
- Performance das queries vetoriais

## Revisão

Esta decisão será revisada quando:
- Necessidade de maior escala
- Limitações de performance
- Mudanças nos requisitos de dados
