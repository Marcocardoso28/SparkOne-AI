# ⚡ SparkOne - Quick Start

## 🚀 **Deploy em 5 Minutos**

### **1. Pré-requisitos**
- Docker Desktop instalado
- Chaves de API: OpenAI, OpenWeatherMap, NewsAPI

### **2. Setup Automático**
```bash
# Windows
.\setup-sparkone.ps1

# Linux/macOS  
./setup-sparkone.sh
```

### **3. Configurar APIs**
Edite o arquivo `.env` com suas chaves:
```env
OPENAI_API_KEY=sk-your-key
OPENWEATHER_API_KEY=your-key
NEWS_API_KEY=your-key
```

### **4. Acessar Sistema**
- **n8n:** http://localhost:5678 (admin/sparkone2024)
- **Evolution API:** http://localhost:8080
- **WhatsApp QR:** http://localhost:8080/sparkone-instance/qrcode

### **5. Importar Workflows**
No n8n, importe os arquivos JSON:
- `jarvis_agent_system.json`
- `jarvis_ai_assistant.json`
- `jarvis_voice_control.json`
- `sparkone_whatsapp_evolution.json`

### **6. Testar**
```bash
python test-sparkone.py
```

## 📱 **Comandos WhatsApp**
- `"Oi SparkOne!"` - Conversa
- `"comandos"` - Clima e notícias
- `"Como está o clima?"` - Meteorologia

## 🎯 **Pronto!**
Seu assistente IA está funcionando!

📚 **Documentação completa:** `README_JARVIS_SYSTEM.md`


