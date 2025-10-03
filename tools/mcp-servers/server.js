#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { spawn } from 'child_process';
import { promisify } from 'util';

const server = new Server(
  {
    name: 'qwen-mcp-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Função para executar Qwen CLI
async function executeQwen(prompt, options = {}) {
  return new Promise((resolve, reject) => {
    const args = ['--prompt', prompt];

    // Adicionar opções se fornecidas
    if (options.model) args.push('--model', options.model);
    if (options.yolo) args.push('--yolo');
    if (options.debug) args.push('--debug');

    const qwen = spawn('qwen', args);

    let stdout = '';
    let stderr = '';

    qwen.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    qwen.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    qwen.on('close', (code) => {
      if (code === 0) {
        resolve({
          success: true,
          output: stdout,
          error: stderr
        });
      } else {
        reject(new Error(`Qwen CLI falhou com código ${code}: ${stderr}`));
      }
    });

    qwen.on('error', (error) => {
      reject(new Error(`Erro ao executar Qwen CLI: ${error.message}`));
    });
  });
}

// Registrar ferramentas disponíveis
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'qwen_analyze',
        description: 'Executa análise usando Qwen CLI com prompt personalizado',
        inputSchema: {
          type: 'object',
          properties: {
            prompt: {
              type: 'string',
              description: 'Prompt para análise no Qwen CLI'
            },
            model: {
              type: 'string',
              description: 'Modelo específico para usar (opcional)'
            },
            yolo: {
              type: 'boolean',
              description: 'Modo YOLO - aceita todas as ações automaticamente'
            },
            debug: {
              type: 'boolean',
              description: 'Ativar modo debug'
            }
          },
          required: ['prompt']
        }
      },
      {
        name: 'qwen_code_analysis',
        description: 'Análise específica de código usando Qwen CLI',
        inputSchema: {
          type: 'object',
          properties: {
            code: {
              type: 'string',
              description: 'Código para análise'
            },
            language: {
              type: 'string',
              description: 'Linguagem do código (opcional)'
            },
            analysis_type: {
              type: 'string',
              description: 'Tipo de análise: bugs, performance, security, readability',
              enum: ['bugs', 'performance', 'security', 'readability', 'general']
            }
          },
          required: ['code', 'analysis_type']
        }
      },
      {
        name: 'qwen_compare',
        description: 'Compara duas soluções ou textos usando Qwen CLI',
        inputSchema: {
          type: 'object',
          properties: {
            text1: {
              type: 'string',
              description: 'Primeiro texto/código para comparação'
            },
            text2: {
              type: 'string',
              description: 'Segundo texto/código para comparação'
            },
            comparison_criteria: {
              type: 'string',
              description: 'Critérios de comparação específicos'
            }
          },
          required: ['text1', 'text2']
        }
      }
    ]
  };
});

// Handler para executar ferramentas
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'qwen_analyze': {
        const { prompt, model, yolo, debug } = args;
        const result = await executeQwen(prompt, { model, yolo, debug });

        return {
          content: [
            {
              type: 'text',
              text: `**Análise Qwen CLI:**\n\n${result.output}`
            }
          ]
        };
      }

      case 'qwen_code_analysis': {
        const { code, language, analysis_type } = args;
        const analysisPrompts = {
          bugs: `Analise o seguinte código ${language || ''} e identifique possíveis bugs:\n\n\`\`\`\n${code}\n\`\`\``,
          performance: `Analise o seguinte código ${language || ''} e sugira melhorias de performance:\n\n\`\`\`\n${code}\n\`\`\``,
          security: `Analise o seguinte código ${language || ''} e identifique vulnerabilidades de segurança:\n\n\`\`\`\n${code}\n\`\`\``,
          readability: `Analise o seguinte código ${language || ''} e sugira melhorias de legibilidade:\n\n\`\`\`\n${code}\n\`\`\``,
          general: `Faça uma análise geral do seguinte código ${language || ''}:\n\n\`\`\`\n${code}\n\`\`\``
        };

        const prompt = analysisPrompts[analysis_type];
        const result = await executeQwen(prompt);

        return {
          content: [
            {
              type: 'text',
              text: `**Análise de Código (${analysis_type}):**\n\n${result.output}`
            }
          ]
        };
      }

      case 'qwen_compare': {
        const { text1, text2, comparison_criteria } = args;
        const prompt = `Compare os seguintes textos/códigos${comparison_criteria ? ` considerando: ${comparison_criteria}` : ''}:

**Opção 1:**
\`\`\`
${text1}
\`\`\`

**Opção 2:**
\`\`\`
${text2}
\`\`\`

Forneça uma análise comparativa detalhada.`;

        const result = await executeQwen(prompt);

        return {
          content: [
            {
              type: 'text',
              text: `**Comparação Qwen CLI:**\n\n${result.output}`
            }
          ]
        };
      }

      default:
        throw new Error(`Ferramenta desconhecida: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Erro ao executar ${name}: ${error.message}`
        }
      ],
      isError: true
    };
  }
});

// Iniciar servidor
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Qwen MCP Server iniciado');
}

main().catch((error) => {
  console.error('Erro ao iniciar servidor:', error);
  process.exit(1);
});