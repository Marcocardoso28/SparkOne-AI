# SparkOne - Runbook de Operações

**Versão:** v1.1.0  
**Data:** Janeiro 2025  

---

## 🎯 Visão Geral

Este runbook contém procedimentos operacionais para manutenção diária, troubleshooting e operações de emergência do SparkOne em produção.

---

## 📋 Operações Diárias

### 1. Verificação de Saúde (Diário - 08:00)

```bash
# Health checks automáticos
curl -s http://localhost:8000/health | jq '.'
curl -s http://localhost:8000/health/database | jq '.'
curl -s http://localhost:8000/health/redis | jq '.'

# Verificar status dos containers
docker-compose -f docker-compose.prod.yml ps

# Verificar uso de recursos
docker stats --no-stream
```

### 2. Monitoramento de Logs

```bash
# Logs da aplicação
docker-compose -f docker-compose.prod.yml logs --tail=100 api

# Logs de erro
docker-compose -f docker-compose.prod.yml logs --tail=50 api | grep -i error

# Logs de segurança
docker-compose -f docker-compose.prod.yml logs --tail=50 api | grep -i "rate limit\|unauthorized"
```

### 3. Verificação de Métricas

```bash
# Métricas Prometheus
curl -s http://localhost:9090/api/v1/query?query=up | jq '.data.result'

# Latência da API
curl -s "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(sparkone_http_request_latency_seconds_bucket[5m]))" | jq '.data.result'

# Pool de conexões do banco
curl -s "http://localhost:9090/api/v1/query?query=sparkone_db_pool_in_use" | jq '.data.result'
```

---

## 🔧 Operações Semanais

### 1. Validação de Backup (Sexta-feira - 18:00)

```bash
# Executar backup manual
/opt/sparkone/ops/backup.sh

# Verificar integridade
/opt/sparkone/ops/verify_backup.sh

# Listar backups disponíveis
/opt/sparkone/ops/restore.sh --list
```

### 2. Análise de Performance

```bash
# Queries lentas
curl -s http://localhost:8000/profiler/slow-queries | jq '.'

# Métricas de uso de memória
curl -s "http://localhost:9090/api/v1/query?query=process_resident_memory_bytes" | jq '.data.result'

# Análise de logs de performance
docker-compose -f docker-compose.prod.yml logs api | grep -i "slow\|timeout" | tail -20
```

### 3. Verificação de Segurança

```bash
# Tentativas de login falhadas
docker-compose -f docker-compose.prod.yml logs api | grep -i "login.*fail" | tail -10

# Rate limiting
curl -s "http://localhost:9090/api/v1/query?query=rate(sparkone_rate_limit_hits_total[1h])" | jq '.data.result'

# Verificar headers de segurança
curl -I https://yourdomain.com | grep -E "(X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security)"
```

---

## 🚨 Troubleshooting

### 1. Problemas de Performance

**Sintomas:** Latência alta, timeouts, resposta lenta

```bash
# Diagnóstico
curl -s "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(sparkone_http_request_latency_seconds_bucket[5m]))" | jq '.data.result[0].value[1]'

# Verificar queries lentas
curl -s http://localhost:8000/profiler/slow-queries | jq '.slow_queries[] | select(.duration > 1.0)'

# Verificar pool de conexões
curl -s "http://localhost:9090/api/v1/query?query=sparkone_db_pool_in_use" | jq '.data.result[0].value[1]'

# Ações:
# 1. Se latência > 2s: Verificar queries lentas
# 2. Se pool > 80%: Verificar conexões ativas
# 3. Reiniciar aplicação se necessário
```

### 2. Problemas de Banco de Dados

**Sintomas:** Erro de conexão, queries falhando

```bash
# Testar conectividade
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;"

# Verificar logs do banco
docker-compose -f docker-compose.prod.yml logs postgres | tail -50

# Verificar health check
curl -s http://localhost:8000/health/database | jq '.'

# Ações:
# 1. Verificar credenciais
# 2. Verificar conectividade de rede
# 3. Restartar container se necessário
```

### 3. Problemas de Redis

**Sintomas:** Cache não funcionando, rate limiting falhando

```bash
# Testar Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# Verificar memória
docker-compose -f docker-compose.prod.yml exec redis redis-cli info memory

# Verificar logs
docker-compose -f docker-compose.prod.yml logs redis | tail -20

# Ações:
# 1. Limpar cache se necessário: FLUSHDB
# 2. Restartar Redis se problemas persistirem
```

### 4. Problemas de SSL/TLS

**Sintomas:** Certificados inválidos, erros HTTPS

```bash
# Verificar certificado
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com < /dev/null 2>/dev/null | openssl x509 -noout -dates

# Verificar logs do Traefik
docker-compose -f docker-compose.prod.yml logs traefik | grep -i "certificate\|ssl\|tls"

# Verificar DNS
nslookup yourdomain.com

# Ações:
# 1. Verificar propagação DNS
# 2. Forçar renovação do Let's Encrypt
# 3. Verificar configuração do Traefik
```

---

## 🔄 Procedimentos de Manutenção

### 1. Atualização de Aplicação

```bash
# 1. Backup antes da atualização
/opt/sparkone/ops/backup.sh

# 2. Pull do código
cd /opt/sparkone
git pull origin main

# 3. Build da nova imagem
docker-compose -f docker-compose.prod.yml build

# 4. Executar migrações (se necessário)
docker-compose -f docker-compose.prod.yml run --rm api alembic upgrade head

# 5. Deploy da nova versão
docker-compose -f docker-compose.prod.yml up -d

# 6. Verificar health checks
sleep 30
curl -s http://localhost:8000/health | jq '.'

# 7. Verificar logs
docker-compose -f docker-compose.prod.yml logs --tail=50 api
```

### 2. Rotação de Logs

```bash
# Limpar logs antigos (manter últimos 7 dias)
find /var/log -name "sparkone-*.log" -mtime +7 -delete

# Rotacionar logs do Docker
docker-compose -f docker-compose.prod.yml logs --tail=1000 api > /var/log/sparkone-$(date +%Y%m%d).log

# Limpar logs do Docker
docker system prune -f
```

### 3. Limpeza de Recursos

```bash
# Limpar imagens não utilizadas
docker image prune -f

# Limpar volumes não utilizados
docker volume prune -f

# Limpar redes não utilizadas
docker network prune -f

# Verificar espaço em disco
df -h
```

---

## 🚨 Procedimentos de Emergência

### 1. Rollback Rápido

```bash
# 1. Parar serviços
docker-compose -f docker-compose.prod.yml down

# 2. Voltar para commit anterior
cd /opt/sparkone
git checkout HEAD~1

# 3. Rebuild e restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 4. Verificar funcionamento
sleep 30
curl -s http://localhost:8000/health | jq '.'
```

### 2. Restore de Backup

```bash
# 1. Listar backups disponíveis
/opt/sparkone/ops/restore.sh --list

# 2. Restore do banco
/opt/sparkone/ops/restore.sh --db /opt/sparkone/backups/sparkone_db_YYYYMMDD_HHMMSS.sql

# 3. Restart serviços
docker-compose -f docker-compose.prod.yml restart api

# 4. Verificar funcionamento
curl -s http://localhost:8000/health | jq '.'
```

### 3. Recuperação de Desastre

```bash
# 1. Provisionar nova VPS
# 2. Configurar ambiente
# 3. Restaurar backup mais recente
# 4. Configurar DNS
# 5. Verificar todos os serviços
# 6. Atualizar monitoramento
```

---

## 📊 Monitoramento e Alertas

### 1. Métricas Críticas

| Métrica | Threshold | Ação |
|---------|-----------|------|
| **Latência P95** | > 2s | Investigar queries lentas |
| **Pool DB** | > 80% | Verificar conexões |
| **Memory Usage** | > 85% | Limpeza ou restart |
| **Error Rate** | > 5% | Investigar logs |
| **Disk Space** | > 90% | Limpeza de logs |

### 2. Alertas Configurados

- **High Latency** - P95 > 2s por 5 minutos
- **Database Pool High** - > 80% por 5 minutos
- **High Error Rate** - > 5% por 5 minutos
- **Service Down** - Health check falhando
- **SSL Certificate** - Expiração em 30 dias

### 3. Dashboards

- **Grafana Principal** - Métricas de sistema e aplicação
- **Grafana Security** - Tentativas de login, rate limiting
- **Grafana Database** - Performance de queries, pool de conexões

---

## 📞 Contatos de Emergência

### Escalação de Incidentes

1. **Nível 1** - Monitoramento automático detecta problema
2. **Nível 2** - Alertas enviados para equipe
3. **Nível 3** - Escalação para desenvolvedor sênior
4. **Nível 4** - Escalação para arquiteto/tech lead

### Contatos

- **Equipe DevOps:** devops@yourcompany.com
- **Desenvolvedor Sênior:** senior.dev@yourcompany.com
- **Tech Lead:** tech.lead@yourcompany.com
- **Emergência 24/7:** +55 11 99999-9999

---

## 📚 Referências

- [Guia de Deploy](./deployment-guide.md)
- [Documentação da API](../api.md)
- [Arquitetura do Sistema](../architecture/overview.md)
- [Infraestrutura](../architecture/infrastructure.md)

---

**Última atualização:** Janeiro 2025  
**Próxima revisão:** Fevereiro 2025  
**Versão:** 1.1.0
