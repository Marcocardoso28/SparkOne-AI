# Checklist de Go-Live - SparkOne

Este checklist deve ser seguido antes de colocar o SparkOne em produção.

## Pré-Deploy

### ✅ Configuração do Servidor
- [ ] VPS configurada com Ubuntu 20.04+
- [ ] Docker e Docker Compose instalados
- [ ] Firewall configurado (portas 22, 80, 443)
- [ ] Usuário não-root com sudo configurado
- [ ] Estrutura de diretórios criada (`/opt/sparkone`)

### ✅ Banco de Dados
- [ ] PostgreSQL gerenciado configurado
- [ ] URL de conexão obtida
- [ ] Credenciais de acesso testadas
- [ ] Backup automático do provedor configurado

### ✅ Domínio e DNS
- [ ] Domínio registrado
- [ ] DNS configurado para apontar para a VPS
- [ ] Subdomínios configurados:
  - [ ] `yourdomain.com` (principal)
  - [ ] `www.yourdomain.com`
  - [ ] `grafana.yourdomain.com`
  - [ ] `prometheus.yourdomain.com`
  - [ ] `alertmanager.yourdomain.com`
  - [ ] `traefik.yourdomain.com`

### ✅ Configurações de Ambiente
- [ ] Arquivo `.env` configurado
- [ ] Todas as variáveis obrigatórias preenchidas:
  - [ ] `DATABASE_URL`
  - [ ] `WEB_PASSWORD`
  - [ ] `SMTP_*` (para alertas)
  - [ ] `ALLOWED_HOSTS`
  - [ ] `CORS_ORIGINS`
- [ ] Secrets configurados (se necessário):
  - [ ] Google Sheets credentials
  - [ ] Google Calendar credentials
  - [ ] Evolution API key
  - [ ] Notion API key

### ✅ Configurações de Segurança
- [ ] Senhas fortes configuradas
- [ ] 2FA habilitado para usuários
- [ ] Headers de segurança configurados
- [ ] Rate limiting configurado
- [ ] HSTS habilitado
- [ ] CORS configurado corretamente

## Deploy

### ✅ Build e Deploy
- [ ] Código atualizado no repositório
- [ ] Build da imagem Docker executado
- [ ] Migrações do banco executadas
- [ ] Serviços iniciados com `docker-compose.prod.yml`
- [ ] Health checks passando

### ✅ Certificados SSL
- [ ] Traefik configurado
- [ ] Let's Encrypt funcionando
- [ ] Certificados SSL válidos
- [ ] Redirecionamento HTTP → HTTPS funcionando

### ✅ Observabilidade
- [ ] Prometheus coletando métricas
- [ ] Grafana acessível e configurado
- [ ] Alertmanager configurado
- [ ] Alertas por email funcionando
- [ ] Logs estruturados funcionando

## Pós-Deploy

### ✅ Testes Funcionais
- [ ] Login funcionando
- [ ] 2FA funcionando
- [ ] Upload de arquivos funcionando
- [ ] Integrações funcionando:
  - [ ] Google Sheets
  - [ ] Google Calendar
  - [ ] WhatsApp (Evolution API)
  - [ ] Notion
- [ ] Webhooks funcionando
- [ ] API endpoints respondendo

### ✅ Backup e Restore
- [ ] Script de backup executado manualmente
- [ ] Backup verificado com sucesso
- [ ] Script de restore testado
- [ ] Cron jobs configurados
- [ ] Retenção de backups configurada

### ✅ Monitoramento
- [ ] Dashboards do Grafana funcionando
- [ ] Alertas configurados e testados
- [ ] Logs sendo coletados
- [ ] Métricas sendo expostas
- [ ] Uptime monitorado

### ✅ Performance
- [ ] Tempo de resposta < 2s
- [ ] Uso de memória < 80%
- [ ] Uso de CPU < 70%
- [ ] Espaço em disco suficiente
- [ ] Rate limiting funcionando

## Segurança

### ✅ Auditoria de Segurança
- [ ] Headers de segurança ativos
- [ ] Cookies seguros configurados
- [ ] CSRF protection ativo
- [ ] XSS protection ativo
- [ ] SQL injection protection ativo
- [ ] Logs de segurança ativos

### ✅ Acesso e Autenticação
- [ ] 2FA obrigatório para todos os usuários
- [ ] Senhas fortes exigidas
- [ ] Sessões com timeout configurado
- [ ] Rate limiting no login ativo
- [ ] Logs de tentativas de login

### ✅ Dados e Privacidade
- [ ] LGPD compliance básico
- [ ] Consentimento de dados implementado
- [ ] Retenção de dados configurada
- [ ] Exclusão de dados implementada
- [ ] Dados sensíveis mascarados nos logs

## CI/CD

### ✅ Pipeline de Deploy
- [ ] GitHub Actions configurado
- [ ] Secrets configurados no GitHub
- [ ] Deploy automático funcionando
- [ ] Rollback automático configurado
- [ ] Notificações de deploy funcionando

### ✅ Testes Automatizados
- [ ] Testes unitários passando
- [ ] Testes de integração passando
- [ ] Linting passando
- [ ] Coverage > 60%
- [ ] Smoke tests funcionando

## Documentação

### ✅ Documentação Técnica
- [ ] README atualizado
- [ ] Guia de deploy documentado
- [ ] API documentation atualizada
- [ ] Troubleshooting guide criado
- [ ] Runbook de operações criado

### ✅ Documentação de Usuário
- [ ] Guia de uso básico
- [ ] FAQ criado
- [ ] Contato de suporte definido
- [ ] Política de privacidade
- [ ] Termos de uso

## Go-Live

### ✅ Preparação Final
- [ ] Backup completo executado
- [ ] Plano de rollback definido
- [ ] Equipe de suporte disponível
- [ ] Monitoramento 24/7 configurado
- [ ] Contatos de emergência definidos

### ✅ Ativação
- [ ] DNS propagado
- [ ] Certificados SSL válidos
- [ ] Todos os serviços funcionando
- [ ] Testes finais executados
- [ ] Usuários notificados

### ✅ Pós-Ativação
- [ ] Monitoramento ativo por 24h
- [ ] Logs sendo analisados
- [ ] Performance sendo monitorada
- [ ] Feedback dos usuários coletado
- [ ] Issues documentados e resolvidos

## Checklist de Emergência

### ✅ Plano de Contingência
- [ ] Procedimento de rollback documentado
- [ ] Backup de emergência disponível
- [ ] Contatos de emergência definidos
- [ ] Procedimento de escalação definido
- [ ] Comunicação de incidentes definida

### ✅ Recuperação de Desastres
- [ ] RPO definido (1 hora)
- [ ] RTO definido (4 horas)
- [ ] Procedimento de restore testado
- [ ] Backup off-site configurado
- [ ] Plano de recuperação documentado

---

## Comandos Úteis

### Verificar Status
```bash
# Status dos containers
docker-compose -f docker-compose.prod.yml ps

# Logs da aplicação
docker-compose -f docker-compose.prod.yml logs -f api

# Verificar certificados
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

### Backup/Restore
```bash
# Backup manual
/opt/sparkone/ops/backup.sh

# Verificar backup
/opt/sparkone/ops/verify_backup.sh

# Restore
/opt/sparkone/ops/restore.sh --list
```

### Monitoramento
```bash
# Verificar métricas
curl http://localhost:8000/metrics

# Verificar health
curl http://localhost:8000/health

# Verificar logs
tail -f /var/log/sparkone-backup.log
```

---

**Data de Go-Live**: ___________
**Responsável**: ___________
**Aprovado por**: ___________

**Observações**:
_________________________________
_________________________________
_________________________________
