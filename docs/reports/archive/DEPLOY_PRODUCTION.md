# Guia de Deploy para Produção - SparkOne

Este documento descreve o processo completo para fazer deploy do SparkOne em produção.

## Pré-requisitos

### 1. VPS/Server
- Ubuntu 20.04+ ou similar
- Mínimo 4GB RAM, 2 CPU cores
- 50GB+ de espaço em disco
- Acesso root ou sudo

### 2. Domínio
- Domínio configurado (ex: `yourdomain.com`)
- DNS apontando para o IP da VPS

### 3. Banco de Dados
- PostgreSQL gerenciado (Neon, ElephantSQL, RDS, etc.)
- URL de conexão do banco

### 4. Serviços Externos
- Conta no GitHub para CI/CD
- Email SMTP para alertas
- (Opcional) Slack para notificações

## Configuração da VPS

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

## Configuração da Aplicação

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

**Configurações importantes no .env.prod:**

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
```

### 3. Configurar Secrets

```bash
# Criar arquivos de credenciais (se necessário)
touch /opt/sparkone/secrets/google-sheets-credentials.json
touch /opt/sparkone/secrets/google-calendar-credentials.json
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

**Substituir `yourdomain.com` pelo seu domínio real.**

## Deploy

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

### 2. Configurar CI/CD

#### GitHub Actions Secrets

No repositório GitHub, configurar os seguintes secrets:

- `HOST`: IP da VPS
- `USERNAME`: usuário SSH
- `SSH_KEY`: chave privada SSH
- `PORT`: porta SSH (geralmente 22)
- `SLACK_WEBHOOK`: (opcional) webhook do Slack

#### Testar Deploy Automático

```bash
# Fazer push para main
git add .
git commit -m "Deploy para produção"
git push origin main
```

## Configuração de Backups

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

## Monitoramento

### 1. Acessar Dashboards

- **Aplicação**: https://yourdomain.com
- **Grafana**: https://grafana.yourdomain.com (admin/admin123)
- **Prometheus**: https://prometheus.yourdomain.com
- **Alertmanager**: https://alertmanager.yourdomain.com
- **Traefik**: https://traefik.yourdomain.com

### 2. Configurar Alertas

Os alertas por email são configurados automaticamente. Verificar:

1. Configurações SMTP no `.env.prod`
2. Alertas no Alertmanager
3. Regras no Prometheus

## Manutenção

### 1. Atualizações

```bash
# Atualizar aplicação
cd /opt/sparkone
git pull origin main
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Executar migrações se necessário
docker-compose -f docker-compose.prod.yml run --rm api alembic upgrade head
```

### 2. Logs

```bash
# Ver logs da aplicação
docker-compose -f docker-compose.prod.yml logs -f api

# Ver logs de backup
tail -f /var/log/sparkone-backup.log

# Ver logs do sistema
journalctl -u docker -f
```

### 3. Restore

```bash
# Listar backups disponíveis
/opt/sparkone/ops/restore.sh --list

# Restore do banco
/opt/sparkone/ops/restore.sh --db /opt/sparkone/backups/sparkone_db_20240101_020000.sql

# Restore de arquivos
/opt/sparkone/ops/restore.sh --files /opt/sparkone/backups/sparkone_files_20240101_020000.tar.gz
```

## Troubleshooting

### 1. Problemas Comuns

**Certificados SSL não funcionam:**
```bash
# Verificar logs do Traefik
docker-compose -f docker-compose.prod.yml logs traefik

# Verificar DNS
nslookup yourdomain.com
```

**Banco de dados não conecta:**
```bash
# Testar conexão
PGPASSWORD=senha psql -h host -p 5432 -U user -d database

# Verificar logs da aplicação
docker-compose -f docker-compose.prod.yml logs api
```

**Backups falhando:**
```bash
# Verificar permissões
ls -la /opt/sparkone/backups/

# Verificar logs
tail -f /var/log/sparkone-backup.log
```

### 2. Comandos Úteis

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

## Segurança

### 1. Checklist de Segurança

- [ ] 2FA habilitado para todos os usuários
- [ ] Senhas fortes configuradas
- [ ] Firewall configurado
- [ ] Certificados SSL válidos
- [ ] Headers de segurança ativos
- [ ] Rate limiting configurado
- [ ] Logs de segurança ativos
- [ ] Backups funcionando
- [ ] Atualizações automáticas

### 2. Monitoramento de Segurança

- Verificar logs de tentativas de login
- Monitorar alertas de segurança
- Revisar logs de acesso regularmente
- Verificar integridade dos backups

## Suporte

Para problemas ou dúvidas:

1. Verificar logs da aplicação
2. Consultar documentação
3. Verificar status dos serviços
4. Executar testes de conectividade

---

**Última atualização**: Janeiro 2024
**Versão**: 1.0
