# Observabilidade SparkOne

## Visão Geral

Este documento descreve a configuração completa de observabilidade do SparkOne, incluindo métricas, dashboards, alertas e procedimentos operacionais.

## Arquitetura de Monitoramento

### Stack de Observabilidade
- **Prometheus**: Coleta e armazenamento de métricas
- **Grafana**: Visualização e dashboards
- **AlertManager**: Gerenciamento de alertas
- **FastAPI**: Exposição de métricas via `/metrics`

### Fluxo de Dados
```
SparkOne App → Métricas Prometheus → Grafana Dashboard
                    ↓
              AlertManager → Notificações
```

## Métricas Coletadas

### Métricas de API
- `sparkone_http_requests_total`: Total de requisições HTTP por método e status
- `sparkone_http_request_latency_seconds`: Latência das requisições em percentis
- `sparkone_active_connections`: Conexões ativas no banco de dados

### Métricas de Integração
- `sparkone_notion_sync_total`: Sincronizações com Notion (sucesso/falha)
- `sparkone_sheets_sync_total`: Sincronizações com Google Sheets (sucesso/falha)
- `sparkone_whatsapp_notifications_total`: Notificações WhatsApp enviadas

### Métricas de Performance
- `sparkone_database_query_duration_seconds`: Tempo de execução de queries
- `sparkone_message_processing_duration_seconds`: Tempo de processamento de mensagens
- `sparkone_pending_tasks_total`: Número de tarefas pendentes

### Métricas de Saúde
- `sparkone_database_health`: Status do banco de dados (1=saudável, 0=indisponível)
- `sparkone_redis_health`: Status do Redis (1=saudável, 0=indisponível)
- `up`: Status geral do serviço

### Métricas de Testes E2E
- `sparkone_e2e_test_failures_total`: Falhas em testes end-to-end
- `sparkone_e2e_test_duration_seconds`: Duração dos testes E2E

## Configuração do Prometheus

### Arquivo de Configuração
Localização: `ops/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alerts.yml"

scrape_configs:
  - job_name: 'sparkone'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### Alertas Configurados
Localização: `ops/prometheus/alerts.yml`

#### Categorias de Alertas

**Sincronização**
- `NotionSyncFailures`: Falhas na sincronização com Notion
- `SheetsSyncFailures`: Falhas na sincronização com Google Sheets

**Performance**
- `HighRequestRate`: Taxa de requisições elevada (>100/min)
- `HighLatency`: Latência elevada (P95 > 2s)
- `DatabaseSlowQueries`: Queries lentas (>500ms)

**Recursos**
- `HighCPUUsage`: CPU acima de 85%
- `HighMemoryUsage`: Memória acima de 85%
- `DatabaseConnectionsHigh`: Muitas conexões ativas (>50)

**Saúde do Sistema**
- `ServiceDown`: SparkOne fora do ar
- `DatabaseDown`: PostgreSQL indisponível
- `RedisDown`: Redis indisponível

**Qualidade**
- `E2ETestFailures`: Falhas em testes E2E
- `E2ETestSlowPerformance`: Testes E2E lentos

**Negócio**
- `TaskBacklogHigh`: Backlog elevado de tarefas
- `MessageProcessingDelay`: Processamento lento de mensagens
- `WhatsAppNotificationFailures`: Falhas em notificações

## Dashboard Grafana

### Configuração
Localização: `ops/grafana/dashboard-overview.json`

### Painéis Disponíveis

#### Performance da API
- **HTTP Requests Rate**: Taxa de requisições por segundo
- **Request Latency Percentiles**: P50, P95, P99 de latência
- **Active DB Connections**: Conexões ativas no PostgreSQL

#### Integrações
- **Notion Sync Failures**: Falhas de sincronização (1h)
- **Sheets Sync Failures**: Falhas de sincronização (1h)
- **WhatsApp Notifications**: Notificações enviadas (1h)

#### Sistema
- **CPU Usage**: Utilização de CPU
- **Memory Usage**: Utilização de memória
- **Database Query Time**: Tempo médio de queries

#### Qualidade
- **E2E Test Performance**: Performance dos testes E2E
- **Pending Tasks**: Tarefas pendentes no sistema
- **Message Processing Time**: Tempo de processamento por canal

### Importação do Dashboard

1. Acesse Grafana (http://localhost:3000)
2. Vá em "+" → "Import"
3. Carregue o arquivo `ops/grafana/dashboard-overview.json`
4. Configure o datasource como "Prometheus"

## Procedimentos Operacionais

### Inicialização do Stack

```bash
# Iniciar Prometheus
cd ops/prometheus
prometheus --config.file=prometheus.yml

# Iniciar Grafana
cd ops/grafana
grafana-server --config=grafana.ini

# Verificar métricas do SparkOne
curl http://localhost:8000/metrics
```

### Verificação de Saúde

```bash
# Health check geral
curl http://localhost:8000/health

# Health check detalhado
curl http://localhost:8000/health/detailed

# Métricas específicas
curl http://localhost:8000/metrics | grep sparkone_
```

### Troubleshooting

#### Métricas não aparecem
1. Verificar se o endpoint `/metrics` está respondendo
2. Confirmar configuração do Prometheus
3. Verificar logs do Prometheus

#### Alertas não disparam
1. Verificar sintaxe das regras em `alerts.yml`
2. Confirmar que as métricas existem
3. Testar expressões PromQL no Prometheus UI

#### Dashboard vazio
1. Verificar conexão com Prometheus
2. Confirmar que as métricas estão sendo coletadas
3. Verificar queries dos painéis

### Runbooks de Incidentes

#### Alta Latência (HighLatency)
1. Verificar dashboard de performance
2. Analisar queries lentas no banco
3. Verificar uso de CPU/memória
4. Escalar recursos se necessário

#### Falhas de Sincronização
1. Verificar logs da aplicação
2. Testar conectividade com APIs externas
3. Verificar credenciais e tokens
4. Reiniciar serviços se necessário

#### Serviço Fora do Ar (ServiceDown)
1. Verificar logs da aplicação
2. Verificar recursos do sistema
3. Reiniciar aplicação
4. Escalar se necessário

## Configuração de Notificações

### Slack (Recomendado)
```yaml
# alertmanager.yml
route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'slack-notifications'

receivers:
- name: 'slack-notifications'
  slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#alerts'
    title: 'SparkOne Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

### Email
```yaml
receivers:
- name: 'email-notifications'
  email_configs:
  - to: 'ops@sparkone.com'
    from: 'alerts@sparkone.com'
    smarthost: 'smtp.gmail.com:587'
    auth_username: 'alerts@sparkone.com'
    auth_password: 'app_password'
    subject: 'SparkOne Alert: {{ .GroupLabels.alertname }}'
```

## Métricas Customizadas

### Adicionando Nova Métrica

1. **Definir no código**:
```python
# src/app/core/metrics.py
NEW_METRIC = Counter(
    'sparkone_new_metric_total',
    'Descrição da nova métrica',
    ['label1', 'label2']
)
```

2. **Instrumentar o código**:
```python
# Onde a métrica deve ser coletada
NEW_METRIC.labels(label1='value1', label2='value2').inc()
```

3. **Adicionar ao dashboard**:
```json
{
  "targets": [
    {
      "expr": "rate(sparkone_new_metric_total[5m])",
      "legendFormat": "Nova Métrica"
    }
  ]
}
```

4. **Criar alerta se necessário**:
```yaml
- alert: NewMetricHigh
  expr: rate(sparkone_new_metric_total[5m]) > 10
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "Nova métrica elevada"
```

## Retenção e Backup

### Prometheus
- Retenção padrão: 15 dias
- Backup diário recomendado
- Configurar storage remoto para produção

### Grafana
- Backup de dashboards via API
- Versionamento de configurações
- Backup de datasources

## Segurança

### Autenticação
- Grafana: Configurar LDAP/OAuth
- Prometheus: Reverse proxy com autenticação
- AlertManager: Basic auth ou OAuth

### Rede
- Firewall restritivo
- VPN para acesso externo
- TLS para comunicação

## Monitoramento de Custos

### Métricas de Recursos
- CPU/Memória por serviço
- Armazenamento utilizado
- Bandwidth de rede

### Alertas de Custo
- Uso excessivo de recursos
- Crescimento anômalo de dados
- Limites de API atingidos

## Próximos Passos

1. **Distributed Tracing**: Implementar Jaeger/Zipkin
2. **Log Aggregation**: Configurar ELK Stack
3. **Synthetic Monitoring**: Testes automatizados de disponibilidade
4. **Capacity Planning**: Previsão de crescimento
5. **SLI/SLO**: Definir Service Level Indicators e Objectives

## Referências

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [FastAPI Metrics](https://fastapi.tiangolo.com/advanced/middleware/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)