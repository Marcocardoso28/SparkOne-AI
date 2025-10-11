# Docker Secrets Checklist - SparkOne v1.1.0

**Status:** IN PROGRESS  
**Date:** 2025-10-05  
**Environment:** Production

---

## Required Secrets

### 1. Database Secrets
- [ ] `db_password` - PostgreSQL database password
- [ ] `db_user` - PostgreSQL username
- [ ] `db_name` - Database name

### 2. Application Secrets
- [ ] `jwt_secret` - JWT signing key (256-bit minimum)
- [ ] `jwt_refresh_secret` - JWT refresh token key
- [ ] `web_password` - Web UI basic auth password
- [ ] `session_secret` - Session encryption key

### 3. External API Keys
- [ ] `openai_api_key` - OpenAI API key (if using)
- [ ] `notion_api_key` - Notion integration token
- [ ] `google_calendar_credentials` - Google Calendar OAuth credentials
- [ ] `evolution_api_key` - Evolution API (WhatsApp) token

### 4. Redis Secrets
- [ ] `redis_password` - Redis authentication password

### 5. Monitoring & Observability
- [ ] `prometheus_password` - Prometheus basic auth
- [ ] `grafana_admin_password` - Grafana admin password

---

## Secret Creation Commands

### Create Database Password
```bash
echo "YOUR_DB_PASSWORD" | docker secret create db_password -
```

### Create JWT Secret (Generated)
```bash
openssl rand -hex 32 | docker secret create jwt_secret -
```

### Create JWT Refresh Secret (Generated)
```bash
openssl rand -hex 32 | docker secret create jwt_refresh_secret -
```

### Create Session Secret (Generated)
```bash
openssl rand -hex 32 | docker secret create session_secret -
```

### Create Web Password
```bash
echo "YOUR_WEB_PASSWORD" | docker secret create web_password -
```

### Create OpenAI API Key
```bash
echo "sk-YOUR_OPENAI_KEY" | docker secret create openai_api_key -
```

### Create Notion API Key
```bash
echo "secret_YOUR_NOTION_KEY" | docker secret create notion_api_key -
```

### Create Evolution API Key
```bash
echo "YOUR_EVOLUTION_KEY" | docker secret create evolution_api_key -
```

### Create Redis Password
```bash
openssl rand -hex 16 | docker secret create redis_password -
```

---

## Verification Commands

### List All Secrets
```bash
docker secret ls
```

### Inspect Secret (without revealing value)
```bash
docker secret inspect <secret_name>
```

### Remove Secret (if needed)
```bash
docker secret rm <secret_name>
```

---

## Security Guidelines

1. **Never commit secrets to Git**
2. **Use strong, randomly generated passwords**
3. **Rotate secrets every 90 days**
4. **Use different secrets for dev/staging/prod**
5. **Backup secrets in secure vault (e.g., 1Password, Vault)**
6. **Limit secret access to necessary services only**

---

## Secret Rotation Schedule

| Secret | Last Rotated | Next Rotation | Status |
|--------|--------------|---------------|--------|
| jwt_secret | 2025-10-05 | 2026-01-05 | ✅ Current |
| jwt_refresh_secret | 2025-10-05 | 2026-01-05 | ✅ Current |
| db_password | TBD | TBD | ⚠️ Pending |
| redis_password | TBD | TBD | ⚠️ Pending |
| openai_api_key | TBD | TBD | ⚠️ Pending |

---

## Emergency Procedures

### If Secret is Compromised
1. Immediately rotate the compromised secret
2. Update all services using the secret
3. Audit access logs for unauthorized usage
4. Document the incident
5. Notify security team

### Rollback Procedure
1. Keep previous secret version for 24h
2. Update services gradually
3. Verify functionality
4. Remove old secret after verification

---

**Status:** TEMPLATE - Secrets must be created before deployment  
**Owner:** DevOps Team  
**Last Updated:** 2025-10-05

