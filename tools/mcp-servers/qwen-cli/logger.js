#!/usr/bin/env node

import pino from 'pino';
import { createWriteStream } from 'fs';
import { mkdir } from 'fs/promises';
import path from 'path';
import os from 'os';

/**
 * Sistema de Logging Enterprise-grade
 * Compatível com padrões de observabilidade e monitoramento
 */

const LOG_DIR = path.join(os.homedir(), '.qwen-mcp', 'logs');

// Garantir que o diretório de logs existe
try {
  await mkdir(LOG_DIR, { recursive: true });
} catch (error) {
  // Ignorar se já existir
}

// Configuração de transports
const transports = [];

// Console transport (desenvolvimento)
if (process.env.NODE_ENV !== 'production') {
  transports.push({
    target: 'pino-pretty',
    options: {
      colorize: true,
      translateTime: 'yyyy-mm-dd HH:MM:ss',
      ignore: 'pid,hostname',
      messageFormat: '{levelName} - {msg}'
    }
  });
}

// File transport (produção)
const logFile = path.join(LOG_DIR, 'qwen-mcp.log');
transports.push({
  target: 'pino/file',
  options: { destination: logFile }
});

// Error-only transport
const errorFile = path.join(LOG_DIR, 'error.log');
transports.push({
  target: 'pino/file',
  level: 'error',
  options: { destination: errorFile }
});

// Configuração do logger
const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  timestamp: pino.stdTimeFunctions.isoTime,
  transport: {
    targets: transports
  },
  base: {
    pid: process.pid,
    hostname: os.hostname(),
    service: 'qwen-mcp-server',
    version: '3.0.0'
  }
});

/**
 * Logger com contexto para MCP operations
 */
class MCPLogger {
  constructor(context = {}) {
    this.context = context;
    this.baseLogger = logger;
  }

  withContext(additionalContext) {
    return new MCPLogger({ ...this.context, ...additionalContext });
  }

  _log(level, message, data = {}) {
    const logData = {
      ...this.context,
      ...data,
      timestamp: new Date().toISOString()
    };

    this.baseLogger[level](logData, message);
  }

  // Métodos de logging padrão
  trace(message, data) { this._log('trace', message, data); }
  debug(message, data) { this._log('debug', message, data); }
  info(message, data) { this._log('info', message, data); }
  warn(message, data) { this._log('warn', message, data); }
  error(message, data) { this._log('error', message, data); }
  fatal(message, data) { this._log('fatal', message, data); }

  // Métodos especializados para MCP
  toolCall(toolName, args, duration = null) {
    this._log('info', `Tool called: ${toolName}`, {
      tool: toolName,
      args: typeof args === 'string' ? args.substring(0, 200) : args,
      duration,
      type: 'tool_call'
    });
  }

  toolResult(toolName, success, duration) {
    this._log('info', `Tool completed: ${toolName}`, {
      tool: toolName,
      success,
      duration,
      type: 'tool_result'
    });
  }

  toolError(toolName, error, duration) {
    this._log('error', `Tool failed: ${toolName}`, {
      tool: toolName,
      error: error.message,
      stack: error.stack,
      duration,
      type: 'tool_error'
    });
  }

  qwenExecution(prompt, model, duration) {
    this._log('info', 'Qwen CLI execution', {
      prompt: prompt.substring(0, 100),
      model,
      duration,
      type: 'qwen_execution'
    });
  }

  cacheHit(key, type) {
    this._log('debug', `Cache hit: ${key}`, {
      cacheKey: key,
      cacheType: type,
      type: 'cache_hit'
    });
  }

  cacheMiss(key, type) {
    this._log('debug', `Cache miss: ${key}`, {
      cacheKey: key,
      cacheType: type,
      type: 'cache_miss'
    });
  }

  rateLimitHit(identifier, limit) {
    this._log('warn', `Rate limit hit: ${identifier}`, {
      identifier,
      limit,
      type: 'rate_limit'
    });
  }

  serverStart(port, mode) {
    this._log('info', `Server started`, {
      port,
      mode,
      type: 'server_start'
    });
  }

  serverStop() {
    this._log('info', 'Server stopped', {
      type: 'server_stop'
    });
  }

  configChange(key, oldValue, newValue) {
    this._log('info', `Configuration changed: ${key}`, {
      configKey: key,
      oldValue: typeof oldValue === 'string' ? oldValue.substring(0, 50) : oldValue,
      newValue: typeof newValue === 'string' ? newValue.substring(0, 50) : newValue,
      type: 'config_change'
    });
  }

  healthCheck(status, checks) {
    this._log('info', `Health check: ${status}`, {
      status,
      checks,
      type: 'health_check'
    });
  }

  securityEvent(event, details) {
    this._log('warn', `Security event: ${event}`, {
      event,
      details,
      type: 'security_event'
    });
  }

  performance(operation, duration, metadata = {}) {
    this._log('info', `Performance: ${operation}`, {
      operation,
      duration,
      ...metadata,
      type: 'performance'
    });
  }
}

// Instância padrão
const mcpLogger = new MCPLogger({
  service: 'qwen-mcp-server',
  version: '3.0.0'
});

export { logger, MCPLogger, mcpLogger as default, LOG_DIR };