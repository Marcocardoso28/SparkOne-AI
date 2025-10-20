# 🚀 Guia de Deploy Completo - SparkOne

## 📋 Visão Geral

Este guia fornece instruções passo-a-passo para fazer o deploy completo do sistema SparkOne, incluindo todas as dependências, configurações e testes de validação.

## 🛠️ Pré-requisitos

### **Sistema Operacional:**
- Windows 10/11 com WSL2 OU
- Linux (Ubuntu 20.04+ recomendado) OU  
- macOS 10.15+

### **Software Necessário:**
- **Docker Desktop** (versão 4.0+)
- **Docker Compose** (incluído no Docker Desktop)
- **Git** (para clonar o repositório)
- **Python 3.8+** (para scripts de teste)

### **APIs Obrigatórias:**
1. **OpenAI API Key** - [Obter aqui](https://platform.openai.com/api-keys)
2. **OpenWeatherMap API** - [Obter aqui](https://openweathermap.org/api)
3. **NewsAPI Key** - [Obter aqui](https://newsapi.org/register)

## 📥 Instalação

### **1. Clone o Repositório**
```bash
git clone <seu-repositorio>
cd N8N
```

### **2. Configure as Variáveis de Ambiente**
```bash
# Copie o template
cp env.template .env

# Edite o arquivo .env com suas chaves
nano .env  # ou use seu editor preferido
```

**Configure as seguintes variáveis obrigatórias:**
```env
OPENAI_API_KEY=sk-your-actual-openai-key
OPENWEATHER_API_KEY=your-actual-weather-key
NEWS_API_KEY=your-actual-news-key
```

### **3. Execute o Setup Automatizado**

#### **No Windows (PowerShell):**
```powershell
# Execute como Administrador
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup-sparkone.ps1
```

#### **No Linux/macOS:**
```bash
chmod +x setup-sparkone.sh
./setup-sparkone.sh
```

### **4. Deploy Manual (Alternativo)**

Se preferir fazer o deploy manual:

```bash
# 1. Parar containers existentes
docker-compose down --remove-orphans

# 2. Iniciar serviços
docker-compose up -d

# 3. Aguardar inicialização
sleep 15

# 4. Verificar status
docker-compose ps
```

## 🔧 Configuração do n8n

### **1. Acessar Interface**
- URL: http://localhost:5678
- Usuário: `admin`
- Senha: `sparkone2024`

### **2. Importar Workflows**
1. Acesse **Workflows** → **Import from File**
2. Importe os seguintes arquivos JSON:
   - `jarvis_agent_system.json`
   - `jarvis_ai_assistant.json` 
   - `jarvis_voice_control.json`
   - `sparkone_whatsapp_evolution.json`

### **3. Configurar Credenciais**

#### **OpenAI API:**
- Nome: `OpenAI API`
- Tipo: `OpenAI API`
- API Key: `sua_openai_api_key`

#### **Evolution API:**
- Nome: `Evolution API`
- Tipo: `HTTP Header Auth`
- Header Name: `apikey`
- Header Value: `sparkone_2024_secure_key`

#### **Google Sheets (Opcional):**
- Nome: `Google Sheets`
- Tipo: `Google Sheets OAuth2 API`
- Configure conforme instruções do Google

## 📱 Configuração WhatsApp

### **1. Criar Instância**
```bash
curl -X POST http://localhost:8080/instance/create \
  -H "Content-Type: application/json" \
  -H "apikey: sparkone_2024_secure_key" \
  -d '{
    "instanceName": "sparkone-instance",
    "token": "sparkone-whatsapp-token",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }'
```

### **2. Conectar WhatsApp**
1. Acesse: http://localhost:8080/sparkone-instance/qrcode
2. Escaneie o QR Code com seu WhatsApp
3. Aguarde a conexão ser estabelecida

### **3. Configurar Webhook**
1. No Evolution API, configure o webhook:
   - URL: `https://your-domain.com/webhook/evolution-webhook`
   - Eventos: `messages.upsert`

## 🧪 Testes e Validação

### **1. Teste Automatizado**
```bash
# Instalar dependências Python
pip install requests

# Executar suite de testes
python test-sparkone.py
```

### **2. Testes Manuais**

#### **Teste WhatsApp:**
1. Envie mensagem: "Oi SparkOne!"
2. Aguarde resposta
3. Teste comando: "comandos"

#### **Teste Clima:**
1. Envie: "Como está o clima hoje?"
2. Verifique se retorna dados meteorológicos

#### **Teste Notícias:**
1. Envie: "Quais as principais notícias?"
2. Verifique se retorna notícias recentes

#### **Teste Controle por Voz:**
```bash
curl -X POST http://localhost:5678/webhook/sparkone-voice \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "command": "ligar luzes da sala",
      "action": "ligar"
    }
  }'
```

## 🔍 Troubleshooting

### **Problemas Comuns:**

#### **1. Evolution API não inicia:**
```bash
# Verificar logs
docker logs sparkone-evolution-api

# Reiniciar container
docker restart sparkone-evolution-api
```

#### **2. n8n não acessível:**
```bash
# Verificar porta
netstat -tulpn | grep 5678

# Verificar logs
docker logs sparkone-n8n
```

#### **3. WhatsApp não conecta:**
- Verifique se o QR Code não expirou
- Recrie a instância se necessário
- Verifique logs do Evolution API

#### **4. Workflows não funcionam:**
- Verifique se as credenciais estão configuradas
- Confirme se os workflows estão ativos
- Verifique logs de execução no n8n

#### **5. APIs externas falham:**
- Confirme se as chaves de API estão corretas
- Verifique limites de rate limiting
- Teste as APIs diretamente

## 📊 Monitoramento

### **1. Logs dos Serviços**
```bash
# Evolution API
docker logs -f sparkone-evolution-api

# n8n
docker logs -f sparkone-n8n

# Todos os serviços
docker-compose logs -f
```

### **2. Status dos Containers**
```bash
docker-compose ps
```

### **3. Uso de Recursos**
```bash
docker stats
```

## 🔒 Segurança

### **1. Variáveis de Ambiente**
- Nunca commite o arquivo `.env`
- Use senhas fortes para APIs
- Rotacione chaves periodicamente

### **2. Firewall**
- Configure firewall para permitir apenas portas necessárias
- Use HTTPS em produção
- Configure autenticação básica no n8n

### **3. Backup**
```bash
# Backup dos dados
docker run --rm -v sparkone-n8n_n8n-data:/data -v $(pwd):/backup alpine tar czf /backup/n8n-backup.tar.gz -C /data .
```

## 🚀 Deploy em Produção

### **1. Configurações de Produção**
- Use domínio próprio
- Configure SSL/TLS
- Use banco de dados externo
- Configure monitoramento

### **2. Exemplo com Nginx**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5678;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /webhook/ {
        proxy_pass http://localhost:5678;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **3. Variáveis de Produção**
```env
N8N_WEBHOOK_URL=https://your-domain.com/
EVOLUTION_WEBHOOK_URL=https://your-domain.com/webhook/evolution-webhook
```

## 📈 Expansão e Customização

### **1. Adicionar Novos Workflows**
1. Crie novos workflows no n8n
2. Exporte como JSON
3. Adicione ao repositório
4. Documente funcionalidades

### **2. Integrações Adicionais**
- Slack, Discord, Telegram
- Google Calendar, Notion
- Home Assistant, Philips Hue
- APIs customizadas

### **3. Monitoramento Avançado**
- Prometheus + Grafana
- ELK Stack
- Alertas automáticos

## ✅ Checklist de Deploy

- [ ] Docker e Docker Compose instalados
- [ ] Arquivo `.env` configurado com todas as chaves
- [ ] Serviços iniciados com `docker-compose up -d`
- [ ] Evolution API acessível em http://localhost:8080
- [ ] n8n acessível em http://localhost:5678
- [ ] Workflows importados no n8n
- [ ] Credenciais configuradas no n8n
- [ ] Instância WhatsApp criada
- [ ] WhatsApp conectado via QR Code
- [ ] Webhooks funcionando
- [ ] Testes automatizados passando
- [ ] Testes manuais realizados
- [ ] Sistema funcionando completamente

## 🆘 Suporte

### **Documentação:**
- README_JARVIS_SYSTEM.md - Visão geral do sistema
- CONFIGURACAO_SPARKONE.md - Configuração detalhada

### **Logs e Debug:**
- Sempre verifique os logs primeiro
- Use `docker-compose logs -f` para monitoramento
- Execute `python test-sparkone.py` para diagnóstico

### **Contato:**
- Issues no repositório
- Documentação oficial n8n: https://docs.n8n.io
- Evolution API docs: https://doc.evolution-api.com

---

**🎉 Parabéns! Seu sistema SparkOne está pronto para uso!**

⚡ **Desenvolvido com n8n, OpenAI, Evolution API e muito mais**

