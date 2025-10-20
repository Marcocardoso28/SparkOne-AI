# ⚡ Guia de Configuração - Sistema SparkOne

## 🚀 Passo a Passo Completo

### **1. Configurar Evolution API**

#### **Instalação via Docker:**
```bash
# Criar diretório para Evolution API
mkdir evolution-api
cd evolution-api

# Executar Evolution API
docker run --name evolution-api -d \
  -p 8080:8080 \
  -e AUTHENTICATION_API_KEY=sparkone_2024_secure_key \
  -e WEBHOOK_GLOBAL_URL=https://your-n8n-domain.com/webhook/ \
  -e WEBHOOK_GLOBAL_ENABLED=true \
  -e WEBHOOK_GLOBAL_WEBHOOK_BY_EVENTS=true \
  -e WEBHOOK_GLOBAL_WEBHOOK_BY_EVENTS_ENABLED=APPLICATION_STARTUP,QRCODE_UPDATED,MESSAGES_UPSERT \
  -v evolution-data:/evolution/instances \
  evolutionapi/evolution-api:latest
```

#### **Verificar se está funcionando:**
```bash
# Verificar logs
docker logs evolution-api

# Testar API
curl http://localhost:8080/manager/fetchInstances
```

### **2. Configurar n8n**

#### **Importar Workflows:**
1. Acesse seu n8n
2. Vá em **Workflows** → **Import from File**
3. Importe os arquivos:
   - `sparkone_whatsapp_evolution.json`
   - `sparkone_agent_system.json`
   - `sparkone_voice_control.json`
   - `sparkone_ai_assistant.json`

#### **Configurar Credenciais:**

**OpenAI API:**
- Nome: `OpenAI API`
- Tipo: `OpenAI API`
- API Key: `sua_openai_api_key`

**HTTP Header Auth (para Evolution):**
- Nome: `Evolution API`
- Tipo: `HTTP Header Auth`
- Header Name: `apikey`
- Header Value: `sparkone_2024_secure_key`

### **3. Variáveis de Ambiente no n8n**

Configure as seguintes variáveis no n8n:

```env
# Evolution API
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sparkone_2024_secure_key
EVOLUTION_INSTANCE_NAME=sparkone-instance

# OpenAI
OPENAI_API_KEY=sk-your-openai-key

# Weather & News
OPENWEATHER_API_KEY=your_openweather_key
NEWS_API_KEY=your_news_api_key

# Google Sheets (opcional)
SPARKONE_LOG_SHEET_ID=your_google_sheet_id
SPARKONE_REMINDERS_SHEET_ID=your_reminders_sheet_id

# Smart Home (opcional)
SMART_LIGHT_DEVICE_ID=your_smart_light_id
SMART_THERMOSTAT_DEVICE_ID=your_thermostat_id
SPARKONE_PLAYLIST_ID=your_spotify_playlist_id
```

### **4. Conectar WhatsApp**

#### **Criar Instância:**
```bash
# Criar instância no Evolution API
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

#### **Conectar WhatsApp:**
1. Acesse: `http://localhost:8080/sparkone-instance/qrcode`
2. Escaneie o QR Code com seu WhatsApp
3. Aguarde a conexão ser estabelecida

### **5. Testar Sistema**

#### **Teste Básico:**
1. Envie uma mensagem para o WhatsApp conectado
2. Verifique se o webhook está recebendo dados no n8n
3. Confirme se o SparkOne responde

#### **Comandos de Teste:**
- "Oi SparkOne!" - Resposta básica
- "comandos" - Clima e notícias
- "Como você está?" - Conversa livre

### **6. Monitoramento**

#### **Verificar Logs:**
```bash
# Evolution API logs
docker logs -f evolution-api

# n8n execution logs
# Acesse n8n → Executions
```

#### **Webhooks Ativos:**
- `https://your-n8n.com/webhook/sparkone-whatsapp`
- `https://your-n8n.com/webhook/sparkone-voice`
- `https://your-n8n.com/webhook/evolution-webhook`

## 🔧 Troubleshooting

### **Problemas Comuns:**

**1. Evolution API não conecta:**
- Verifique se a porta 8080 está livre
- Confirme as variáveis de ambiente
- Reinicie o container

**2. Webhook não recebe dados:**
- Verifique a URL do webhook no Evolution
- Confirme se o n8n está acessível publicamente
- Teste o webhook manualmente

**3. SparkOne não responde:**
- Verifique as credenciais do OpenAI
- Confirme se o workflow está ativo
- Veja os logs de execução no n8n

**4. QR Code não aparece:**
- Aguarde alguns segundos
- Recrie a instância se necessário
- Verifique os logs do Evolution

## ✅ Checklist de Configuração

- [ ] Evolution API rodando na porta 8080
- [ ] Instância criada no Evolution
- [ ] WhatsApp conectado via QR Code
- [ ] Workflows importados no n8n
- [ ] Credenciais configuradas
- [ ] Variáveis de ambiente definidas
- [ ] Webhooks funcionando
- [ ] Teste básico realizado
- [ ] SparkOne respondendo no WhatsApp

## 🚀 Próximos Passos

Após a configuração básica funcionando:
1. Personalizar respostas do SparkOne
2. Adicionar mais comandos
3. Configurar automações avançadas
4. Integrar com outros sistemas
5. Implementar funcionalidades específicas

---

**Status:** ⏳ Aguardando configuração inicial





