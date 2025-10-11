# SparkOne - Guia de Deploy para Produção

**Versão:** v1.1.0  
**Data:** Janeiro 2025  

---

## 🎯 Visão Geral

Este guia fornece instruções completas para fazer deploy do SparkOne em produção. O sistema está **100% pronto** com todos os endpoints funcionais e testes validados.

---

## 📋 Pré-requisitos

### 1. Servidor/VPS
- **OS:** Ubuntu 20.04+ ou similar
- **Recursos:** Mínimo 4GB RAM, 2 CPU cores
- **Armazenamento:** 50GB+ de espaço em disco
- **Acesso:** Root ou sudo

### 2. Domínio e DNS
- **Domínio:** Configurado (ex: `yourdomain.com`)
- **DNS:** Apontando para IP da VPS
- **Subdomínios:** Configurados para serviços
  - `yourdomain.com` (principal)
  - `grafana.yourdomain.com`
  - `prometheus.yourdomain.com`

### 3. Banco de Dados
- **PostgreSQL:** Gerenciado (Neon, ElephantSQL, RDS, etc.)
- **URL:** String de conexão obtida
- **Backup:** Automático do provedor

### 4. Serviços Externos
- **GitHub:** Para CI/CD
- **Email SMTP:** Para alertas
- **APIs:** Google Sheets, Calendar, Evolution API, Notion

---

## 🔧 Configuração da VPS

### 1. Instalar Dependências

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Instalar PostgreSQL client
sudo apt install postgresql-client -y

# Instalar outras dependências
sudo apt install git curl wget unzip -y
```

### 2. Configurar Firewall

```bash
# Configurar UFW
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 3. Criar Estrutura de Diretórios

```bash
# Criar diretório da aplicação
sudo mkdir -p /opt/sparkone
sudo chown $USER:$USER /opt/sparkone

# Criar diretórios necessários
mkdir -p /opt/sparkone/{backups,secrets,uploads,logs}
```

---

## 📦 Configuração da Aplicação

### 1. Clonar Repositório

```bash
cd /opt/sparkone
git clone https://github.com/seu-usuario/sparkone.git .
```

### 2. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp config/production.env .env.prod

# Editar configurações
nano .env.prod
```

**Configurações importantes no `.env.prod`:**

```env
# Ambiente
ENVIRONMENT=production
DEBUG=false

# Banco de dados (Postgres gerenciado)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database

# Domínio
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Segurança
WEB_PASSWORD=senha_super_segura_aqui
SECURITY_HSTS_ENABLED=true
SECURITY_HSTS_PRELOAD=true

# Email para alertas
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_de_app

# 2FA
TOTP_ISSUER=SparkOne

# APIs Externas
GOOGLE_SHEETS_CREDENTIALS_FILE=/opt/sparkone/secrets/google-sheets-credentials.json
GOOGLE_CALENDAR_CREDENTIALS_FILE=/opt/sparkone/secrets/google-calendar-credentials.json
EVOLUTION_API_URL=https://sua-evolution-api.com
EVOLUTION_API_KEY=sua_chave_evolution
NOTION_API_KEY=sua_chave_notion
```

### 3. Configurar Secrets

```bash
# Criar arquivos de credenciais
touch /opt/sparkone/secrets/google-sheets-credentials.json
touch /opt/sparkone/secrets/google-calendar-credentials.json

# Adicionar credenciais (copiar conteúdo dos arquivos JSON)
nano /opt/sparkone/secrets/google-sheets-credentials.json
nano /opt/sparkone/secrets/google-calendar-credentials.json
```

### 4. Configurar Traefik

```bash
# Criar diretório para certificados
sudo mkdir -p /opt/sparkone/ops/traefik/letsencrypt
sudo chown -R $USER:$USER /opt/sparkone/ops/traefik/letsencrypt

# Atualizar configuração do Traefik
nano ops/traefik/traefik.yml
nano ops/traefik/dynamic/sparkone.yml
```

**Substituir `yourdomain.com` pelo seu domínio real em todos os arquivos.**

---

## 🚀 Deploy

### 1. Build e Deploy Inicial

```bash
cd /opt/sparkone

# Build da imagem
docker-compose -f docker-compose.prod.yml build

# Executar migrações
docker-compose -f docker-compose.prod.yml run --rm api alembic upgrade head

# Iniciar serviços
docker-compose -f docker-compose.prod.yml up -d

# Verificar status
docker-compose -f docker-compose.prod.yml ps
```

### 2. Verificar Deploy

```bash
# Verificar health checks
curl http://localhost:8000/health
curl http://localhost:8000/health/database
curl http://localhost:8000/health/redis

# Verificar logs
docker-compose -f docker-compose.prod.yml logs -f api

# Verificar certificados SSL
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

---

## 🔒 Configuração de Segurança

### 1. Checklist de Segurança

- [ ] **2FA habilitado** para todos os usuários
- [ ] **Senhas fortes** configuradas
- [ ] **Firewall** configurado (portas 22, 80, 443)
- [ ] **Certificados SSL** válidos
- [ ] **Headers de segurança** ativos
- [ ] **Rate limiting** configurado
- [ ] **Logs de segurança** ativos
- [ ] **Backups** funcionando

### 2. Configurar 2FA

```bash
# Criar usuário administrativo
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@yourdomain.com",
    "password": "senha_forte_aqui"
  }'

# Configurar 2FA para o usuário
curl -X POST http://localhost:8000/auth/setup-2fa \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin"
  }'
```

---

## 📊 Monitoramento

### 1. Acessar Dashboards

- **Aplicação:** https://yourdomain.com
- **Grafana:** https://grafana.yourdomain.com (admin/admin123)
- **Prometheus:** https://prometheus.yourdomain.com
- **Alertmanager:** https://alertmanager.yourdomain.com
- **Traefik:** https://traefik.yourdomain.com

### 2. Configurar Alertas

Os alertas por email são configurados automaticamente. Verificar:

1. Configurações SMTP no `.env.prod`
2. Alertas no Alertmanager
3. Regras no Prometheus

---

## 💾 Backup e Restore

### 1. Configurar Cron

```bash
# Editar crontab
crontab -e

# Adicionar linhas:
# Backup diário às 2h da manhã
0 2 * * * /opt/sparkone/ops/backup.sh >> /var/log/sparkone-backup.log 2>&1

# Verificação de backup às 3h da manhã
0 3 * * * /opt/sparkone/ops/verify_backup.sh >> /var/log/sparkone-backup.log 2>&1
```

### 2. Testar Backups

```bash
# Executar backup manual
/opt/sparkone/ops/backup.sh

# Verificar backup
/opt/sparkone/ops/verify_backup.sh

# Listar backups
/opt/sparkone/ops/restore.sh --list
```

---

## 🔄 CI/CD

### 1. Configurar GitHub Actions

No repositório GitHub, configurar os seguintes secrets:

- `HOST`: IP da VPS
- `USERNAME`: usuário SSH
- `SSH_KEY`: chave privada SSH
- `PORT`: porta SSH (geralmente 22)
- `SLACK_WEBHOOK`: (opcional) webhook do Slack

### 2. Testar Deploy Automático

```bash
# Fazer push para main
git add .
git commit -m "Deploy para produção"
git push origin main
```

---

## ✅ Checklist de Go-Live

### Pré-Deploy
- [ ] VPS configurada com Ubuntu 20.04+
- [ ] Docker e Docker Compose instalados
- [ ] Firewall configurado
- [ ] PostgreSQL gerenciado configurado
- [ ] Domínio e DNS configurados
- [ ] Variáveis de ambiente configuradas
- [ ] Secrets configurados

### Deploy
- [ ] Build da imagem Docker executado
- [ ] Migrações do banco executadas
- [ ] Serviços iniciados com docker-compose
- [ ] Health checks passando
- [ ] Certificados SSL válidos
- [ ] Traefik funcionando

### Pós-Deploy
- [ ] Login funcionando
- [ ] 2FA funcionando
- [ ] Integrações funcionando
- [ ] Webhooks funcionando
- [ ] API endpoints respondendo
- [ ] Backup funcionando
- [ ] Monitoramento configurado

### Segurança
- [ ] Headers de segurança ativos
- [ ] Rate limiting funcionando
- [ ] Logs de segurança ativos
- [ ] 2FA obrigatório
- [ ] Senhas fortes exigidas

---

## 🔧 Comandos Úteis

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

## 🚨 Troubleshooting

### Problemas Comuns

**1. Certificados SSL não funcionam:**
```bash
# Verificar logs do Traefik
docker-compose -f docker-compose.prod.yml logs traefik

# Verificar DNS
nslookup yourdomain.com
```

**2. Banco de dados não conecta:**
```bash
# Testar conexão
PGPASSWORD=senha psql -h host -p 5432 -U user -d database

# Verificar logs da aplicação
docker-compose -f docker-compose.prod.yml logs api
```

**3. Backups falhando:**
```bash
# Verificar permissões
ls -la /opt/sparkone/backups/

# Verificar logs
tail -f /var/log/sparkone-backup.log
```

### Comandos de Emergência
```bash
# Reiniciar serviços
docker-compose -f docker-compose.prod.yml restart

# Ver uso de recursos
docker stats

# Limpar containers antigos
docker system prune -f

# Verificar espaço em disco
df -h
```

---

## 📞 Suporte

Para problemas ou dúvidas:

1. **Verificar logs** da aplicação
2. **Consultar documentação** técnica
3. **Verificar status** dos serviços
4. **Executar testes** de conectividade
5. **Consultar** [guia de manutenção](./maintenance.md)

---

**Última atualização:** Janeiro 2025  
**Versão:** 1.1.0  
**Status:** ✅ **PRODUCTION_READY**
