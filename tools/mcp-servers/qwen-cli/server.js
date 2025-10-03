#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema
} from '@modelcontextprotocol/sdk/types.js';
import { spawn, exec } from 'child_process';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';

const server = new Server(
  {
    name: 'qwen-mcp-server',
    version: '2.0.0',
  },
  {
    capabilities: {
      tools: {},
      resources: {},
      prompts: {}
    },
  }
);

// Configuração avançada similar ao Gemini CLI
const CONFIG_FILE = path.join(os.homedir(), '.qwen-mcp-settings.json');

async function loadConfig() {
  try {
    const data = await fs.readFile(CONFIG_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    return {
      mcpServers: {},
      global: {
        timeout: 30000,
        includeTools: [],
        excludeTools: [],
        trust: false
      }
    };
  }
}

// Função avançada para executar Qwen CLI
async function executeQwen(prompt, options = {}) {
  const config = await loadConfig();
  const globalConfig = config.global || {};

  return new Promise((resolve, reject) => {
    const args = ['-p', prompt];

    // Aplicar configurações globais e locais
    if (options.model) args.push('--model', options.model);
    if (options.yolo || globalConfig.yolo) args.push('--yolo');
    if (options.debug || globalConfig.debug) args.push('--debug');
    if (options.sandbox !== undefined) {
      args.push(options.sandbox ? '--sandbox' : '--no-sandbox');
    }

    // Qwen usa OAuth configurado em ~/.qwen/settings.json
    // Não precisamos passar API keys manualmente

    // Log removido para não interferir com stdio MCP

    // Usar exec para executar comando shell diretamente com escape correto
    const escapedArgs = args.map(arg => {
      if (typeof arg === 'string') {
        return `'${arg.replace(/'/g, `'"'"'`)}'`;
      }
      return arg;
    });

    const command = `sudo -u marcocardoso -i qwen ${escapedArgs.join(' ')}`;

    const timeout = options.timeout || globalConfig.timeout || 30000;

    exec(command, {
      timeout: timeout,
      env: { ...process.env, ...options.env }
    }, (error, stdout, stderr) => {
      if (error) {
        if (error.code === 'ETIMEDOUT') {
          reject(new Error(`Timeout após ${timeout}ms`));
          return;
        }

        reject(new Error(`Erro ao executar Qwen CLI: ${error.message}`));
        return;
      }

      // Sucesso - retornar resultado
      resolve({
        success: true,
        output: stdout,
        error: stderr,
        exitCode: 0
      });
    });
  });
}

// Sistema de filtros de ferramentas (igual ao Gemini CLI)
function shouldIncludeTool(toolName, config) {
  const globalConfig = config.global || {};

  // Se há includeTools definido, só incluir se estiver na lista
  if (globalConfig.includeTools && globalConfig.includeTools.length > 0) {
    return globalConfig.includeTools.includes(toolName);
  }

  // Se há excludeTools definido, excluir se estiver na lista
  if (globalConfig.excludeTools && globalConfig.excludeTools.length > 0) {
    return !globalConfig.excludeTools.includes(toolName);
  }

  return true;
}

// Registrar recursos (similar ao Gemini CLI)
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: 'qwen://status',
        name: 'Status do Qwen CLI',
        description: 'Status e informações do Qwen CLI',
        mimeType: 'application/json'
      },
      {
        uri: 'qwen://config',
        name: 'Configuração MCP',
        description: 'Configuração atual do servidor MCP',
        mimeType: 'application/json'
      },
      {
        uri: 'qwen://models',
        name: 'Modelos Disponíveis',
        description: 'Lista de modelos disponíveis no Qwen CLI',
        mimeType: 'application/json'
      }
    ]
  };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;

  switch (uri) {
    case 'qwen://status':
      try {
        const result = await executeQwen('--help', { timeout: 5000 });
        return {
          contents: [
            {
              uri,
              mimeType: 'application/json',
              text: JSON.stringify({
                status: 'available',
                version: 'unknown',
                help: result.output
              }, null, 2)
            }
          ]
        };
      } catch (error) {
        return {
          contents: [
            {
              uri,
              mimeType: 'application/json',
              text: JSON.stringify({
                status: 'error',
                error: error.message
              }, null, 2)
            }
          ]
        };
      }

    case 'qwen://config':
      const config = await loadConfig();
      return {
        contents: [
          {
            uri,
            mimeType: 'application/json',
            text: JSON.stringify(config, null, 2)
          }
        ]
      };

    case 'qwen://models':
      return {
        contents: [
          {
            uri,
            mimeType: 'application/json',
            text: JSON.stringify({
              available_models: [
                'qwen-turbo',
                'qwen-plus',
                'qwen-max',
                'qwen-math',
                'qwen-coder'
              ],
              note: 'Execute qwen --help para ver modelos atuais'
            }, null, 2)
          }
        ]
      };

    default:
      throw new Error(`Recurso não encontrado: ${uri}`);
  }
});

// Registrar prompts (similar ao Gemini CLI)
server.setRequestHandler(ListPromptsRequestSchema, async () => {
  return {
    prompts: [
      {
        name: 'code_analyzer',
        description: 'Analisador de código especializado',
        arguments: [
          {
            name: 'code',
            description: 'Código para analisar',
            required: true
          },
          {
            name: 'language',
            description: 'Linguagem de programação',
            required: false
          },
          {
            name: 'focus',
            description: 'Foco da análise (bugs, performance, security, style)',
            required: false
          }
        ]
      },
      {
        name: 'architecture_review',
        description: 'Revisão de arquitetura de software',
        arguments: [
          {
            name: 'description',
            description: 'Descrição da arquitetura',
            required: true
          },
          {
            name: 'technology_stack',
            description: 'Stack tecnológico utilizado',
            required: false
          }
        ]
      }
    ]
  };
});

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case 'code_analyzer':
      const { code, language, focus } = args;
      const analysisType = focus || 'general';

      return {
        messages: [
          {
            role: 'user',
            content: {
              type: 'text',
              text: `Como especialista em ${language || 'programação'}, analise o seguinte código com foco em ${analysisType}:

\`\`\`${language || ''}
${code}
\`\`\`

Forneça uma análise detalhada incluindo:
1. Problemas identificados
2. Sugestões de melhoria
3. Boas práticas aplicáveis
4. Considerações de segurança (se aplicável)`
            }
          }
        ]
      };

    case 'architecture_review':
      const { description, technology_stack } = args;

      return {
        messages: [
          {
            role: 'user',
            content: {
              type: 'text',
              text: `Como arquiteto de software, revise a seguinte arquitetura:

**Descrição:**
${description}

${technology_stack ? `**Stack Tecnológico:**\n${technology_stack}\n` : ''}

Forneça uma revisão completa incluindo:
1. Análise da arquitetura proposta
2. Pontos fortes e fracos
3. Sugestões de melhoria
4. Considerações de escalabilidade
5. Riscos potenciais
6. Alternativas recomendadas`
            }
          }
        ]
      };

    default:
      throw new Error(`Prompt não encontrado: ${name}`);
  }
});

// Registrar ferramentas com filtros avançados
server.setRequestHandler(ListToolsRequestSchema, async () => {
  const config = await loadConfig();

  const allTools = [
    {
      name: 'qwen_analyze',
      description: 'Análise geral usando Qwen CLI com configurações avançadas'
    },
    {
      name: 'qwen_code_analysis',
      description: 'Análise especializada de código com múltiplos focos'
    },
    {
      name: 'qwen_compare',
      description: 'Comparação avançada entre textos/códigos'
    },
    {
      name: 'qwen_interactive',
      description: 'Sessão interativa com Qwen CLI'
    },
    {
      name: 'qwen_batch',
      description: 'Processamento em lote de múltiplos prompts'
    },
    {
      name: 'qwen_model_switch',
      description: 'Trocar modelo do Qwen dinamicamente'
    }
  ];

  // Aplicar filtros
  const filteredTools = allTools.filter(tool => shouldIncludeTool(tool.name, config));

  // Adicionar schemas completos
  return {
    tools: filteredTools.map(tool => ({
      name: tool.name,
      description: tool.description,
      inputSchema: getToolSchema(tool.name)
    }))
  };
});

function getToolSchema(toolName) {
  const schemas = {
    qwen_analyze: {
      type: 'object',
      properties: {
        prompt: { type: 'string', description: 'Prompt para análise' },
        model: { type: 'string', description: 'Modelo específico (qwen-turbo, qwen-plus, qwen-max)' },
        yolo: { type: 'boolean', description: 'Modo YOLO - aceita todas as ações' },
        debug: { type: 'boolean', description: 'Ativar modo debug' },
        sandbox: { type: 'boolean', description: 'Executar em sandbox' },
        timeout: { type: 'number', description: 'Timeout personalizado em ms' },
        openai_api_key: { type: 'string', description: 'OpenAI API key para autenticação' },
        tavily_api_key: { type: 'string', description: 'Tavily API key para busca web' }
      },
      required: ['prompt']
    },
    qwen_code_analysis: {
      type: 'object',
      properties: {
        code: { type: 'string', description: 'Código para análise' },
        language: { type: 'string', description: 'Linguagem do código' },
        analysis_type: {
          type: 'string',
          enum: ['bugs', 'performance', 'security', 'readability', 'architecture', 'best_practices'],
          description: 'Tipo de análise especializada'
        },
        depth: {
          type: 'string',
          enum: ['surface', 'deep', 'comprehensive'],
          description: 'Profundidade da análise'
        }
      },
      required: ['code', 'analysis_type']
    },
    qwen_compare: {
      type: 'object',
      properties: {
        text1: { type: 'string', description: 'Primeiro item para comparação' },
        text2: { type: 'string', description: 'Segundo item para comparação' },
        comparison_type: {
          type: 'string',
          enum: ['code', 'architecture', 'performance', 'security', 'general'],
          description: 'Tipo de comparação'
        },
        criteria: { type: 'string', description: 'Critérios específicos' }
      },
      required: ['text1', 'text2']
    },
    qwen_interactive: {
      type: 'object',
      properties: {
        initial_prompt: { type: 'string', description: 'Prompt inicial' },
        mode: {
          type: 'string',
          enum: ['code', 'analysis', 'review', 'debug'],
          description: 'Modo da sessão interativa'
        }
      },
      required: ['initial_prompt']
    },
    qwen_batch: {
      type: 'object',
      properties: {
        prompts: {
          type: 'array',
          items: { type: 'string' },
          description: 'Lista de prompts para processar'
        },
        parallel: { type: 'boolean', description: 'Processar em paralelo' }
      },
      required: ['prompts']
    },
    qwen_model_switch: {
      type: 'object',
      properties: {
        new_model: {
          type: 'string',
          enum: ['qwen-turbo', 'qwen-plus', 'qwen-max', 'qwen-math', 'qwen-coder'],
          description: 'Novo modelo para usar'
        }
      },
      required: ['new_model']
    }
  };

  return schemas[toolName] || { type: 'object', properties: {} };
}

// Handler avançado para executar ferramentas
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const config = await loadConfig();

  // Verificar se a ferramenta está permitida
  if (!shouldIncludeTool(name, config)) {
    return {
      content: [
        {
          type: 'text',
          text: `❌ Ferramenta '${name}' não está disponível devido às configurações de filtro.`
        }
      ],
      isError: true
    };
  }

  try {
    switch (name) {
      case 'qwen_analyze': {
        const { prompt, model, yolo, debug, sandbox, timeout, openai_api_key, tavily_api_key } = args;
        const result = await executeQwen(prompt, {
          model,
          yolo,
          debug,
          sandbox,
          timeout,
          openai_api_key,
          tavily_api_key
        });

        return {
          content: [
            {
              type: 'text',
              text: `**🤖 Análise Qwen CLI**\n\n${result.output}\n\n---\n*Executado com: qwen --prompt "${prompt}"${model ? ` --model ${model}` : ''}*`
            }
          ]
        };
      }

      case 'qwen_code_analysis': {
        const { code, language, analysis_type, depth } = args;
        const depthPrompts = {
          surface: 'Faça uma análise rápida e pontual',
          deep: 'Faça uma análise detalhada e aprofundada',
          comprehensive: 'Faça uma análise abrangente e exaustiva'
        };

        const analysisPrompts = {
          bugs: `${depthPrompts[depth || 'deep']} do seguinte código ${language || ''} identificando bugs e erros:\n\n\`\`\`${language || ''}\n${code}\n\`\`\``,
          performance: `${depthPrompts[depth || 'deep']} do seguinte código ${language || ''} focando em otimizações de performance:\n\n\`\`\`${language || ''}\n${code}\n\`\`\``,
          security: `${depthPrompts[depth || 'deep']} do seguinte código ${language || ''} identificando vulnerabilidades de segurança:\n\n\`\`\`${language || ''}\n${code}\n\`\`\``,
          readability: `${depthPrompts[depth || 'deep']} do seguinte código ${language || ''} sugerindo melhorias de legibilidade:\n\n\`\`\`${language || ''}\n${code}\n\`\`\``,
          architecture: `${depthPrompts[depth || 'deep']} da arquitetura do seguinte código ${language || ''}:\n\n\`\`\`${language || ''}\n${code}\n\`\`\``,
          best_practices: `${depthPrompts[depth || 'deep']} do seguinte código ${language || ''} verificando aderência às melhores práticas:\n\n\`\`\`${language || ''}\n${code}\n\`\`\``
        };

        const prompt = analysisPrompts[analysis_type];
        const result = await executeQwen(prompt);

        return {
          content: [
            {
              type: 'text',
              text: `**🔍 Análise de Código (${analysis_type})**\n**Profundidade:** ${depth || 'deep'}\n**Linguagem:** ${language || 'não especificada'}\n\n${result.output}`
            }
          ]
        };
      }

      case 'qwen_compare': {
        const { text1, text2, comparison_type, criteria } = args;
        const prompt = `Compare os seguintes ${comparison_type || 'textos'}${criteria ? ` considerando: ${criteria}` : ''}:

**${comparison_type === 'code' ? 'Código' : 'Item'} 1:**
\`\`\`
${text1}
\`\`\`

**${comparison_type === 'code' ? 'Código' : 'Item'} 2:**
\`\`\`
${text2}
\`\`\`

Forneça uma análise comparativa detalhada com prós e contras de cada opção.`;

        const result = await executeQwen(prompt);

        return {
          content: [
            {
              type: 'text',
              text: `**⚖️ Comparação Avançada (${comparison_type || 'geral'})**\n\n${result.output}`
            }
          ]
        };
      }

      case 'qwen_batch': {
        const { prompts, parallel } = args;

        if (parallel) {
          const promises = prompts.map(prompt => executeQwen(prompt));
          const results = await Promise.allSettled(promises);

          const output = results.map((result, index) => {
            if (result.status === 'fulfilled') {
              return `**Resultado ${index + 1}:**\n${result.value.output}`;
            } else {
              return `**Erro ${index + 1}:**\n${result.reason.message}`;
            }
          }).join('\n\n---\n\n');

          return {
            content: [
              {
                type: 'text',
                text: `**📦 Processamento em Lote (Paralelo)**\n\n${output}`
              }
            ]
          };
        } else {
          let output = '';
          for (let i = 0; i < prompts.length; i++) {
            try {
              const result = await executeQwen(prompts[i]);
              output += `**Resultado ${i + 1}:**\n${result.output}\n\n---\n\n`;
            } catch (error) {
              output += `**Erro ${i + 1}:**\n${error.message}\n\n---\n\n`;
            }
          }

          return {
            content: [
              {
                type: 'text',
                text: `**📦 Processamento em Lote (Sequencial)**\n\n${output}`
              }
            ]
          };
        }
      }

      default:
        throw new Error(`Ferramenta desconhecida: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `❌ **Erro ao executar ${name}:**\n${error.message}`
        }
      ],
      isError: true
    };
  }
});

// Iniciar servidor com logging para arquivo
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);

  // Log para arquivo em vez de stderr (que interfere com MCP stdio)
  const logFile = path.join(os.homedir(), '.qwen-mcp.log');
  const timestamp = new Date().toISOString();
  const config = await loadConfig();

  const logMessage = `[${timestamp}] 🚀 Qwen MCP Server v2.0 iniciado\n📁 Config: ${CONFIG_FILE}\n🔧 Ferramentas ativas: ${Object.keys(config.mcpServers || {}).length}\n\n`;

  try {
    await fs.appendFile(logFile, logMessage);
  } catch (error) {
    // Silent fail - não podemos usar console.error aqui
  }
}

main().catch(async (error) => {
  // Log erro para arquivo em vez de stderr
  const logFile = path.join(os.homedir(), '.qwen-mcp.log');
  const timestamp = new Date().toISOString();
  const errorMessage = `[${timestamp}] ❌ Erro ao iniciar servidor: ${error.message}\n`;

  try {
    await fs.appendFile(logFile, errorMessage);
  } catch (logError) {
    // Silent fail
  }

  process.exit(1);
});