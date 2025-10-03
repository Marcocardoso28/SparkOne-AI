# Qwen MCP Server

MCP Server para integração com Qwen CLI, permitindo que Claude acesse as capacidades de análise do Qwen.

## Ferramentas Disponíveis

### `qwen_analyze`
Executa análise geral usando Qwen CLI
- **prompt**: Prompt para análise
- **model**: Modelo específico (opcional)
- **yolo**: Modo automático (opcional)
- **debug**: Modo debug (opcional)

### `qwen_code_analysis`
Análise específica de código
- **code**: Código para análise
- **language**: Linguagem do código (opcional)
- **analysis_type**: Tipo de análise (bugs, performance, security, readability, general)

### `qwen_compare`
Compara dois textos ou códigos
- **text1**: Primeiro texto/código
- **text2**: Segundo texto/código
- **comparison_criteria**: Critérios específicos (opcional)

## Instalação

```bash
# Instalar dependências
cd ~/qwen-mcp-server
npm install

# Registrar no Claude
claude mcp add qwen-cli "cd ~/qwen-mcp-server && node server.js"

# Verificar status
claude mcp list
```

## Uso

Após a instalação, você pode usar as ferramentas via Claude:

```
Claude, use o qwen_analyze para analisar: "Como otimizar este algoritmo?"

Claude, use o qwen_code_analysis para verificar bugs neste código JavaScript: [código]
```

## Troubleshooting

```bash
# Testar execução direta
cd ~/qwen-mcp-server && node server.js

# Verificar logs
claude mcp list
```