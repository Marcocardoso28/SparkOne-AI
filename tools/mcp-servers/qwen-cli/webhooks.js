#!/usr/bin/env node
import { EventEmitter } from 'events';
import crypto from 'crypto';
import { readFile, writeFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';
import os from 'os';
import got from 'got';
import { logger } from './logger.js';

/**
 * Enterprise-grade Webhook & Event System
 * Permite integração em tempo real com sistemas externos
 */
class WebhookManager extends EventEmitter {
  constructor(options = {}) {
    super();
    this.options = {
      enableWebhooks: options.enableWebhooks !== false,
      maxRetries: options.maxRetries || 3,
      retryDelay: options.retryDelay || 1000,
      timeout: options.timeout || 10000,
      enableSignatures: options.enableSignatures !== false,
      secretKey: options.secretKey || this.generateSecret(),
      webhooksFile: path.join(os.homedir(), '.qwen-mcp', 'webhooks.json'),
      enableEventBuffer: options.enableEventBuffer || true,
      bufferSize: options.bufferSize || 1000,
      ...options
    };

    this.webhooks = new Map();
    this.eventBuffer = [];
    this.retryQueue = [];

    this.init();
  }

  async init() {
    await this.loadWebhooks();
    this.startRetryProcessor();

    // Registrar eventos padrão do sistema
    this.registerSystemEvents();

    logger.info('Webhook manager initialized', {
      enableWebhooks: this.options.enableWebhooks,
      enableSignatures: this.options.enableSignatures,
      webhooksCount: this.webhooks.size
    });
  }

  generateSecret() {
    return crypto.randomBytes(32).toString('hex');
  }

  async loadWebhooks() {
    try {
      if (existsSync(this.options.webhooksFile)) {
        const data = await readFile(this.options.webhooksFile, 'utf-8');
        const webhooksData = JSON.parse(data);

        for (const [id, webhook] of Object.entries(webhooksData.webhooks || {})) {
          this.webhooks.set(id, webhook);
        }

        logger.info('Webhooks loaded', { count: this.webhooks.size });
      }
    } catch (error) {
      logger.warn('Failed to load webhooks', { error: error.message });
    }
  }

  async saveWebhooks() {
    try {
      const webhooksData = {
        webhooks: Object.fromEntries(this.webhooks),
        lastUpdated: new Date().toISOString()
      };

      await writeFile(this.options.webhooksFile, JSON.stringify(webhooksData, null, 2));
      logger.debug('Webhooks saved');
    } catch (error) {
      logger.error('Failed to save webhooks', { error: error.message });
    }
  }

  registerSystemEvents() {
    // Eventos de métricas
    this.on('request.completed', (data) => {
      this.triggerWebhooks('request.completed', data);
    });

    this.on('request.failed', (data) => {
      this.triggerWebhooks('request.failed', data);
    });

    // Eventos de sistema
    this.on('system.started', (data) => {
      this.triggerWebhooks('system.started', data);
    });

    this.on('system.shutdown', (data) => {
      this.triggerWebhooks('system.shutdown', data);
    });

    // Eventos de plugins
    this.on('plugin.loaded', (data) => {
      this.triggerWebhooks('plugin.loaded', data);
    });

    this.on('plugin.error', (data) => {
      this.triggerWebhooks('plugin.error', data);
    });

    // Eventos de auth
    this.on('auth.login', (data) => {
      this.triggerWebhooks('auth.login', data);
    });

    this.on('auth.failed', (data) => {
      this.triggerWebhooks('auth.failed', data);
    });

    // Eventos de health
    this.on('health.critical', (data) => {
      this.triggerWebhooks('health.critical', data);
    });

    this.on('health.recovered', (data) => {
      this.triggerWebhooks('health.recovered', data);
    });
  }

  async createWebhook(webhookData) {
    const webhookId = crypto.randomUUID();
    const webhook = {
      id: webhookId,
      url: webhookData.url,
      events: webhookData.events || ['*'],
      enabled: webhookData.enabled !== false,
      name: webhookData.name || 'Unnamed Webhook',
      description: webhookData.description || '',
      headers: webhookData.headers || {},
      secret: webhookData.secret,
      retryPolicy: {
        maxRetries: webhookData.maxRetries || this.options.maxRetries,
        retryDelay: webhookData.retryDelay || this.options.retryDelay,
        backoffMultiplier: webhookData.backoffMultiplier || 2
      },
      filters: webhookData.filters || {},
      createdAt: new Date().toISOString(),
      lastTriggered: null,
      successCount: 0,
      failureCount: 0,
      metadata: webhookData.metadata || {}
    };

    this.webhooks.set(webhookId, webhook);
    await this.saveWebhooks();

    logger.info('Webhook created', {
      id: webhookId,
      url: webhook.url,
      events: webhook.events,
      name: webhook.name
    });

    return webhook;
  }

  async updateWebhook(webhookId, updates) {
    const webhook = this.webhooks.get(webhookId);
    if (!webhook) {
      throw new Error(`Webhook not found: ${webhookId}`);
    }

    Object.assign(webhook, updates, {
      updatedAt: new Date().toISOString()
    });

    await this.saveWebhooks();
    logger.info('Webhook updated', { id: webhookId });

    return webhook;
  }

  async deleteWebhook(webhookId) {
    const webhook = this.webhooks.get(webhookId);
    if (!webhook) {
      throw new Error(`Webhook not found: ${webhookId}`);
    }

    this.webhooks.delete(webhookId);
    await this.saveWebhooks();

    logger.info('Webhook deleted', { id: webhookId, url: webhook.url });
  }

  async triggerWebhooks(eventType, eventData = {}) {
    if (!this.options.enableWebhooks) {
      return;
    }

    const event = {
      id: crypto.randomUUID(),
      type: eventType,
      data: eventData,
      timestamp: new Date().toISOString(),
      source: 'qwen-mcp-server'
    };

    // Adicionar ao buffer de eventos
    if (this.options.enableEventBuffer) {
      this.eventBuffer.push(event);
      if (this.eventBuffer.length > this.options.bufferSize) {
        this.eventBuffer = this.eventBuffer.slice(-this.options.bufferSize);
      }
    }

    logger.debug('Event triggered', { type: eventType, id: event.id });

    // Encontrar webhooks interessados neste evento
    const interestedWebhooks = Array.from(this.webhooks.values()).filter(webhook => {
      if (!webhook.enabled) return false;

      // Verificar se o webhook está interessado neste evento
      const isInterestedInEvent = webhook.events.includes('*') ||
                                 webhook.events.includes(eventType) ||
                                 webhook.events.some(pattern => this.matchEventPattern(eventType, pattern));

      if (!isInterestedInEvent) return false;

      // Aplicar filtros se existirem
      if (webhook.filters && Object.keys(webhook.filters).length > 0) {
        return this.applyFilters(event, webhook.filters);
      }

      return true;
    });

    // Enviar para cada webhook interessado
    const promises = interestedWebhooks.map(webhook =>
      this.sendWebhook(webhook, event)
    );

    await Promise.allSettled(promises);
  }

  matchEventPattern(eventType, pattern) {
    // Suporte a wildcards simples
    const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
    return regex.test(eventType);
  }

  applyFilters(event, filters) {
    for (const [key, value] of Object.entries(filters)) {
      const eventValue = this.getNestedValue(event, key);

      if (Array.isArray(value)) {
        if (!value.includes(eventValue)) return false;
      } else if (typeof value === 'object' && value.operator) {
        if (!this.applyOperatorFilter(eventValue, value)) return false;
      } else {
        if (eventValue !== value) return false;
      }
    }
    return true;
  }

  getNestedValue(obj, path) {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }

  applyOperatorFilter(value, filter) {
    switch (filter.operator) {
      case 'eq': return value === filter.value;
      case 'ne': return value !== filter.value;
      case 'gt': return value > filter.value;
      case 'gte': return value >= filter.value;
      case 'lt': return value < filter.value;
      case 'lte': return value <= filter.value;
      case 'contains': return String(value).includes(filter.value);
      case 'regex': return new RegExp(filter.value).test(String(value));
      default: return true;
    }
  }

  async sendWebhook(webhook, event, attempt = 1) {
    try {
      const payload = {
        webhook_id: webhook.id,
        event,
        delivery_attempt: attempt,
        timestamp: new Date().toISOString()
      };

      const headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Qwen-MCP-Server/3.0',
        'X-Webhook-Event': event.type,
        'X-Webhook-ID': webhook.id,
        'X-Delivery-Attempt': attempt.toString(),
        ...webhook.headers
      };

      // Adicionar assinatura se habilitada
      if (this.options.enableSignatures) {
        const signature = this.generateSignature(payload, webhook.secret || this.options.secretKey);
        headers['X-Webhook-Signature'] = signature;
      }

      const response = await got.post(webhook.url, {
        json: payload,
        headers,
        timeout: this.options.timeout,
        throwHttpErrors: true
      });

      // Sucesso
      webhook.lastTriggered = new Date().toISOString();
      webhook.successCount++;

      logger.info('Webhook delivered successfully', {
        webhookId: webhook.id,
        eventType: event.type,
        statusCode: response.statusCode,
        attempt
      });

      this.emit('webhook.success', {
        webhook,
        event,
        attempt,
        response: {
          statusCode: response.statusCode,
          headers: response.headers
        }
      });

    } catch (error) {
      webhook.failureCount++;

      logger.warn('Webhook delivery failed', {
        webhookId: webhook.id,
        eventType: event.type,
        attempt,
        error: error.message
      });

      this.emit('webhook.failure', {
        webhook,
        event,
        attempt,
        error: error.message
      });

      // Adicionar à fila de retry se não excedeu o limite
      if (attempt < webhook.retryPolicy.maxRetries) {
        const delay = webhook.retryPolicy.retryDelay * Math.pow(webhook.retryPolicy.backoffMultiplier, attempt - 1);

        this.retryQueue.push({
          webhook,
          event,
          attempt: attempt + 1,
          retryAt: Date.now() + delay
        });

        logger.info('Webhook queued for retry', {
          webhookId: webhook.id,
          nextAttempt: attempt + 1,
          retryIn: delay + 'ms'
        });
      }
    }
  }

  generateSignature(payload, secret) {
    const body = JSON.stringify(payload);
    const hmac = crypto.createHmac('sha256', secret);
    hmac.update(body);
    return 'sha256=' + hmac.digest('hex');
  }

  verifySignature(payload, signature, secret) {
    const expectedSignature = this.generateSignature(payload, secret);
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expectedSignature)
    );
  }

  startRetryProcessor() {
    setInterval(() => {
      this.processRetryQueue();
    }, 1000);
  }

  async processRetryQueue() {
    const now = Date.now();
    const readyToRetry = [];

    // Encontrar itens prontos para retry
    this.retryQueue = this.retryQueue.filter(item => {
      if (item.retryAt <= now) {
        readyToRetry.push(item);
        return false;
      }
      return true;
    });

    // Processar retries
    for (const item of readyToRetry) {
      await this.sendWebhook(item.webhook, item.event, item.attempt);
    }
  }

  getWebhook(webhookId) {
    return this.webhooks.get(webhookId);
  }

  listWebhooks() {
    return Array.from(this.webhooks.values()).map(webhook => ({
      id: webhook.id,
      name: webhook.name,
      url: webhook.url,
      events: webhook.events,
      enabled: webhook.enabled,
      successCount: webhook.successCount,
      failureCount: webhook.failureCount,
      lastTriggered: webhook.lastTriggered,
      createdAt: webhook.createdAt
    }));
  }

  getEventHistory(limit = 100) {
    return this.eventBuffer.slice(-limit);
  }

  getStats() {
    const webhooks = Array.from(this.webhooks.values());
    const enabled = webhooks.filter(w => w.enabled);

    return {
      total: webhooks.length,
      enabled: enabled.length,
      disabled: webhooks.length - enabled.length,
      totalDeliveries: webhooks.reduce((sum, w) => sum + w.successCount + w.failureCount, 0),
      successfulDeliveries: webhooks.reduce((sum, w) => sum + w.successCount, 0),
      failedDeliveries: webhooks.reduce((sum, w) => sum + w.failureCount, 0),
      pendingRetries: this.retryQueue.length,
      eventsInBuffer: this.eventBuffer.length
    };
  }

  async testWebhook(webhookId) {
    const webhook = this.webhooks.get(webhookId);
    if (!webhook) {
      throw new Error(`Webhook not found: ${webhookId}`);
    }

    const testEvent = {
      id: crypto.randomUUID(),
      type: 'webhook.test',
      data: {
        message: 'This is a test webhook delivery',
        webhookId,
        timestamp: new Date().toISOString()
      },
      timestamp: new Date().toISOString(),
      source: 'qwen-mcp-server'
    };

    await this.sendWebhook(webhook, testEvent);
    return testEvent;
  }

  enableWebhook(webhookId) {
    const webhook = this.webhooks.get(webhookId);
    if (webhook) {
      webhook.enabled = true;
      this.saveWebhooks();
      logger.info('Webhook enabled', { id: webhookId });
    }
  }

  disableWebhook(webhookId) {
    const webhook = this.webhooks.get(webhookId);
    if (webhook) {
      webhook.enabled = false;
      this.saveWebhooks();
      logger.info('Webhook disabled', { id: webhookId });
    }
  }
}

// Singleton instance
let webhookManagerInstance = null;

export function getWebhookManager(options = {}) {
  if (!webhookManagerInstance) {
    webhookManagerInstance = new WebhookManager(options);
  }
  return webhookManagerInstance;
}

export { WebhookManager };