#!/usr/bin/env node

import { program } from 'commander';
import chalk from 'chalk';
import inquirer from 'inquirer';
import { spawn } from 'child_process';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';

// Configuração similar ao Gemini CLI
const CONFIG_FILE = path.join(os.homedir(), '.qwen-mcp-settings.json');

async function loadConfig() {
  try {
    const data = await fs.readFile(CONFIG_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    return { mcpServers: {} };
  }
}

async function saveConfig(config) {
  await fs.writeFile(CONFIG_FILE, JSON.stringify(config, null, 2));
}

async function testConnection(name, serverConfig) {
  return new Promise((resolve) => {
    console.log(chalk.yellow(`Testando conexão com ${name}...`));

    const args = serverConfig.args || [];
    const child = spawn(serverConfig.command, args, {
      cwd: serverConfig.cwd,
      env: { ...process.env, ...serverConfig.env },
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let connected = false;
    const timeout = setTimeout(() => {
      if (!connected) {
        child.kill();
        resolve({ success: false, error: 'Timeout' });
      }
    }, serverConfig.timeout || 5000);

    child.on('spawn', () => {
      connected = true;
      clearTimeout(timeout);
      child.kill();
      resolve({ success: true });
    });

    child.on('error', (error) => {
      clearTimeout(timeout);
      resolve({ success: false, error: error.message });
    });
  });
}

// Comando ADD - Igual ao Gemini CLI
program
  .command('add')
  .description('Adicionar servidor MCP')
  .argument('<name>', 'Nome do servidor')
  .argument('<command>', 'Comando para executar')
  .argument('[args...]', 'Argumentos do comando')
  .option('--transport <type>', 'Tipo de transporte (stdio, http, sse)', 'stdio')
  .option('--timeout <ms>', 'Timeout em millisegundos', '5000')
  .option('--trust', 'Marcar servidor como confiável')
  .option('--cwd <dir>', 'Diretório de trabalho')
  .option('-e, --env <key=value>', 'Variáveis de ambiente', [])
  .option('--include-tools <tools>', 'Ferramentas a incluir (comma-separated)')
  .option('--exclude-tools <tools>', 'Ferramentas a excluir (comma-separated)')
  .option('--header <key:value>', 'Headers HTTP (para http/sse)', [])
  .action(async (name, command, args, options) => {
    const config = await loadConfig();

    // Processar environment variables
    const env = {};
    options.env.forEach(envVar => {
      const [key, value] = envVar.split('=');
      env[key] = value;
    });

    // Processar headers
    const headers = {};
    options.header.forEach(header => {
      const [key, value] = header.split(':');
      headers[key.trim()] = value.trim();
    });

    const serverConfig = {
      command,
      args: args || [],
      transport: options.transport,
      timeout: parseInt(options.timeout),
      trust: options.trust || false,
      cwd: options.cwd,
      env,
      headers: Object.keys(headers).length > 0 ? headers : undefined,
      includeTools: options.includeTools ? options.includeTools.split(',').map(t => t.trim()) : undefined,
      excludeTools: options.excludeTools ? options.excludeTools.split(',').map(t => t.trim()) : undefined
    };

    config.mcpServers[name] = serverConfig;
    await saveConfig(config);

    console.log(chalk.green(`✓ Servidor MCP '${name}' adicionado com sucesso`));

    // Testar conexão
    const result = await testConnection(name, serverConfig);
    if (result.success) {
      console.log(chalk.green(`✓ Conexão testada com sucesso`));
    } else {
      console.log(chalk.red(`✗ Falha na conexão: ${result.error}`));
    }
  });

// Comando REMOVE - Igual ao Gemini CLI
program
  .command('remove')
  .description('Remover servidor MCP')
  .argument('<name>', 'Nome do servidor')
  .action(async (name) => {
    const config = await loadConfig();

    if (!config.mcpServers[name]) {
      console.log(chalk.red(`Servidor '${name}' não encontrado`));
      return;
    }

    delete config.mcpServers[name];
    await saveConfig(config);
    console.log(chalk.green(`✓ Servidor MCP '${name}' removido com sucesso`));
  });

// Comando LIST - Igual ao Gemini CLI
program
  .command('list')
  .description('Listar servidores MCP configurados')
  .action(async () => {
    const config = await loadConfig();

    console.log(chalk.bold('Verificando status dos servidores MCP...\n'));

    if (Object.keys(config.mcpServers).length === 0) {
      console.log(chalk.yellow('Nenhum servidor MCP configurado'));
      return;
    }

    for (const [name, serverConfig] of Object.entries(config.mcpServers)) {
      const result = await testConnection(name, serverConfig);
      const status = result.success ?
        chalk.green('✓ Conectado') :
        chalk.red(`✗ Falha: ${result.error}`);

      console.log(`${chalk.bold(name)}: ${serverConfig.command} ${(serverConfig.args || []).join(' ')} - ${status}`);

      if (serverConfig.trust) {
        console.log(`  ${chalk.blue('🔐 Servidor confiável')}`);
      }
      if (serverConfig.includeTools) {
        console.log(`  ${chalk.green('✓ Ferramentas incluídas:')} ${serverConfig.includeTools.join(', ')}`);
      }
      if (serverConfig.excludeTools) {
        console.log(`  ${chalk.red('✗ Ferramentas excluídas:')} ${serverConfig.excludeTools.join(', ')}`);
      }
      console.log();
    }
  });

// Comando AUTH - Inspirado no Gemini CLI
program
  .command('auth')
  .description('Gerenciar autenticação OAuth')
  .argument('[server]', 'Nome do servidor para autenticar')
  .action(async (server) => {
    const config = await loadConfig();

    if (!server) {
      console.log(chalk.bold('Servidores que requerem autenticação:'));
      // Implementar listagem de servidores OAuth
      return;
    }

    if (!config.mcpServers[server]) {
      console.log(chalk.red(`Servidor '${server}' não encontrado`));
      return;
    }

    console.log(chalk.blue(`Iniciando autenticação OAuth para '${server}'...`));
    // Implementar fluxo OAuth
  });

// Comando STATUS - Diagnóstico avançado
program
  .command('status')
  .description('Status detalhado dos servidores MCP')
  .action(async () => {
    const config = await loadConfig();

    console.log(chalk.bold('=== Status Detalhado dos Servidores MCP ===\n'));

    for (const [name, serverConfig] of Object.entries(config.mcpServers)) {
      console.log(chalk.bold.blue(`📋 Servidor: ${name}`));
      console.log(`   Comando: ${serverConfig.command}`);
      console.log(`   Args: ${(serverConfig.args || []).join(' ')}`);
      console.log(`   Transport: ${serverConfig.transport || 'stdio'}`);
      console.log(`   Timeout: ${serverConfig.timeout || 5000}ms`);
      console.log(`   CWD: ${serverConfig.cwd || 'current'}`);
      console.log(`   Trust: ${serverConfig.trust ? 'Yes' : 'No'}`);

      if (serverConfig.env && Object.keys(serverConfig.env).length > 0) {
        console.log(`   Env Vars: ${Object.keys(serverConfig.env).join(', ')}`);
      }

      const result = await testConnection(name, serverConfig);
      console.log(`   Status: ${result.success ? chalk.green('CONNECTED') : chalk.red('FAILED')}`);

      if (!result.success) {
        console.log(`   Error: ${result.error}`);
      }
      console.log();
    }
  });

// Comando CONFIG - Mostrar configuração
program
  .command('config')
  .description('Mostrar configuração atual')
  .option('--json', 'Saída em formato JSON')
  .action(async (options) => {
    const config = await loadConfig();

    if (options.json) {
      console.log(JSON.stringify(config, null, 2));
    } else {
      console.log(chalk.bold('Configuração atual:'));
      console.log(chalk.gray(`Arquivo: ${CONFIG_FILE}`));
      console.log();
      console.log(JSON.stringify(config, null, 2));
    }
  });

program
  .name('qwen-mcp')
  .description('CLI para gerenciar servidores MCP do Qwen - Estilo Gemini CLI')
  .version('2.0.0');

program.parse();