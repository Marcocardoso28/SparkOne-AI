#!/usr/bin/env node
import { EventEmitter } from 'events';
import { writeFile, readFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';
import os from 'os';
import cron from 'node-cron';
import { logger } from './logger.js';

/**
 * Enterprise-grade Metrics & Analytics System
 * Coleta, processa e analisa métricas do MCP server
 */
class MetricsCollector extends EventEmitter {
  constructor(options = {}) {
    super();
    this.options = {
      enableCollection: true,
      bufferSize: 1000,
      flushInterval: 30000,
      retentionDays: 30,
      enablePersistence: true,
      metricsDir: path.join(os.homedir(), '.qwen-mcp', 'metrics'),
      ...options
    };

    this.metrics = {
      requests: {
        total: 0,
        success: 0,
        errors: 0,
        byTool: {},
        byHour: {},
        responseTimes: []
      },
      performance: {
        cpuUsage: [],
        memoryUsage: [],
        uptime: Date.now()
      },
      system: {
        cacheHits: 0,
        cacheMisses: 0,
        rateLimitHits: 0,
        authFailures: 0
      },
      usage: {
        activeUsers: new Set(),
        peakConcurrency: 0,
        currentConcurrency: 0
      }
    };

    this.buffer = [];
    this.startTime = Date.now();

    this.init();
  }

  async init() {
    if (this.options.enablePersistence) {
      await this.ensureMetricsDir();
      await this.loadPersistedMetrics();
    }

    this.startPerformanceCollection();
    this.startFlushTimer();
    this.scheduleCleanup();

    logger.info('Metrics collector initialized', {
      enableCollection: this.options.enableCollection,
      metricsDir: this.options.metricsDir
    });
  }

  async ensureMetricsDir() {
    if (!existsSync(this.options.metricsDir)) {
      await mkdir(this.options.metricsDir, { recursive: true });
    }
  }

  async loadPersistedMetrics() {
    try {
      const metricsFile = path.join(this.options.metricsDir, 'current.json');
      if (existsSync(metricsFile)) {
        const data = await readFile(metricsFile, 'utf-8');
        const savedMetrics = JSON.parse(data);
        Object.assign(this.metrics, savedMetrics);
        logger.info('Loaded persisted metrics');
      }
    } catch (error) {
      logger.warn('Failed to load persisted metrics', { error: error.message });
    }
  }

  recordRequest(toolName, success = true, responseTime = 0, userId = null) {
    if (!this.options.enableCollection) return;

    const timestamp = Date.now();
    const hour = new Date().getHours();

    // Métricas básicas
    this.metrics.requests.total++;
    if (success) {
      this.metrics.requests.success++;
    } else {
      this.metrics.requests.errors++;
    }

    // Por ferramenta
    if (!this.metrics.requests.byTool[toolName]) {
      this.metrics.requests.byTool[toolName] = { count: 0, avgResponseTime: 0, errors: 0 };
    }
    this.metrics.requests.byTool[toolName].count++;
    if (!success) {
      this.metrics.requests.byTool[toolName].errors++;
    }

    // Por hora
    if (!this.metrics.requests.byHour[hour]) {
      this.metrics.requests.byHour[hour] = 0;
    }
    this.metrics.requests.byHour[hour]++;

    // Response times
    if (responseTime > 0) {
      this.metrics.requests.responseTimes.push({
        timestamp,
        toolName,
        responseTime
      });

      // Manter apenas últimas 1000 entradas
      if (this.metrics.requests.responseTimes.length > 1000) {
        this.metrics.requests.responseTimes = this.metrics.requests.responseTimes.slice(-1000);
      }

      // Atualizar média
      const toolMetrics = this.metrics.requests.byTool[toolName];
      toolMetrics.avgResponseTime = (toolMetrics.avgResponseTime * (toolMetrics.count - 1) + responseTime) / toolMetrics.count;
    }

    // Usuários únicos
    if (userId) {
      this.metrics.usage.activeUsers.add(userId);
    }

    // Buffer para persistência
    this.buffer.push({
      timestamp,
      type: 'request',
      toolName,
      success,
      responseTime,
      userId
    });

    this.emit('request', { toolName, success, responseTime, userId });
  }

  recordCacheHit(hit = true) {
    if (hit) {
      this.metrics.system.cacheHits++;
    } else {
      this.metrics.system.cacheMisses++;
    }
  }

  recordRateLimit() {
    this.metrics.system.rateLimitHits++;
  }

  recordAuthFailure() {
    this.metrics.system.authFailures++;
  }

  updateConcurrency(change) {
    this.metrics.usage.currentConcurrency += change;
    if (this.metrics.usage.currentConcurrency > this.metrics.usage.peakConcurrency) {
      this.metrics.usage.peakConcurrency = this.metrics.usage.currentConcurrency;
    }
  }

  startPerformanceCollection() {
    setInterval(() => {
      const memUsage = process.memoryUsage();
      const cpuUsage = process.cpuUsage();

      this.metrics.performance.memoryUsage.push({
        timestamp: Date.now(),
        rss: memUsage.rss,
        heapUsed: memUsage.heapUsed,
        heapTotal: memUsage.heapTotal,
        external: memUsage.external
      });

      this.metrics.performance.cpuUsage.push({
        timestamp: Date.now(),
        user: cpuUsage.user,
        system: cpuUsage.system
      });

      // Manter apenas últimas 100 entradas
      if (this.metrics.performance.memoryUsage.length > 100) {
        this.metrics.performance.memoryUsage = this.metrics.performance.memoryUsage.slice(-100);
      }
      if (this.metrics.performance.cpuUsage.length > 100) {
        this.metrics.performance.cpuUsage = this.metrics.performance.cpuUsage.slice(-100);
      }
    }, 10000); // A cada 10 segundos
  }

  startFlushTimer() {
    setInterval(async () => {
      await this.flush();
    }, this.options.flushInterval);
  }

  async flush() {
    if (!this.options.enablePersistence || this.buffer.length === 0) return;

    try {
      // Salvar métricas atuais
      const currentFile = path.join(this.options.metricsDir, 'current.json');
      await writeFile(currentFile, JSON.stringify(this.metrics, null, 2));

      // Salvar buffer de eventos
      const dateStr = new Date().toISOString().split('T')[0];
      const eventsFile = path.join(this.options.metricsDir, `events-${dateStr}.json`);

      let existingEvents = [];
      if (existsSync(eventsFile)) {
        const data = await readFile(eventsFile, 'utf-8');
        existingEvents = JSON.parse(data);
      }

      existingEvents.push(...this.buffer);
      await writeFile(eventsFile, JSON.stringify(existingEvents, null, 2));

      this.buffer = [];
      logger.debug('Metrics flushed to disk');
    } catch (error) {
      logger.error('Failed to flush metrics', { error: error.message });
    }
  }

  scheduleCleanup() {
    // Limpeza diária às 2h da manhã
    cron.schedule('0 2 * * *', async () => {
      await this.cleanup();
    });
  }

  async cleanup() {
    try {
      const files = await readdir(this.options.metricsDir);
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - this.options.retentionDays);

      for (const file of files) {
        if (file.startsWith('events-') && file.endsWith('.json')) {
          const dateStr = file.replace('events-', '').replace('.json', '');
          const fileDate = new Date(dateStr);

          if (fileDate < cutoffDate) {
            await unlink(path.join(this.options.metricsDir, file));
            logger.info('Cleaned up old metrics file', { file });
          }
        }
      }
    } catch (error) {
      logger.error('Failed to cleanup old metrics', { error: error.message });
    }
  }

  getMetrics() {
    const uptime = Date.now() - this.startTime;
    const requestsPerMinute = this.metrics.requests.total / (uptime / 60000);
    const errorRate = this.metrics.requests.total > 0
      ? (this.metrics.requests.errors / this.metrics.requests.total) * 100
      : 0;

    const avgResponseTime = this.metrics.requests.responseTimes.length > 0
      ? this.metrics.requests.responseTimes.reduce((sum, r) => sum + r.responseTime, 0) / this.metrics.requests.responseTimes.length
      : 0;

    const cacheHitRate = (this.metrics.system.cacheHits + this.metrics.system.cacheMisses) > 0
      ? (this.metrics.system.cacheHits / (this.metrics.system.cacheHits + this.metrics.system.cacheMisses)) * 100
      : 0;

    return {
      uptime,
      requests: {
        ...this.metrics.requests,
        perMinute: requestsPerMinute,
        errorRate,
        avgResponseTime
      },
      performance: this.metrics.performance,
      system: {
        ...this.metrics.system,
        cacheHitRate
      },
      usage: {
        ...this.metrics.usage,
        activeUsers: this.metrics.usage.activeUsers.size
      }
    };
  }

  async getDetailedReport() {
    const basicMetrics = this.getMetrics();

    // Top ferramentas mais usadas
    const topTools = Object.entries(basicMetrics.requests.byTool)
      .sort(([,a], [,b]) => b.count - a.count)
      .slice(0, 10);

    // Distribuição de response times
    const responseTimes = this.metrics.requests.responseTimes;
    const responseTimePercentiles = responseTimes.length > 0 ? {
      p50: this.calculatePercentile(responseTimes.map(r => r.responseTime), 50),
      p90: this.calculatePercentile(responseTimes.map(r => r.responseTime), 90),
      p99: this.calculatePercentile(responseTimes.map(r => r.responseTime), 99)
    } : null;

    return {
      ...basicMetrics,
      analysis: {
        topTools,
        responseTimePercentiles,
        busyHours: Object.entries(basicMetrics.requests.byHour)
          .sort(([,a], [,b]) => b - a)
          .slice(0, 5)
      }
    };
  }

  calculatePercentile(values, percentile) {
    const sorted = values.sort((a, b) => a - b);
    const index = Math.ceil((percentile / 100) * sorted.length) - 1;
    return sorted[index] || 0;
  }

  reset() {
    this.metrics = {
      requests: {
        total: 0,
        success: 0,
        errors: 0,
        byTool: {},
        byHour: {},
        responseTimes: []
      },
      performance: {
        cpuUsage: [],
        memoryUsage: [],
        uptime: Date.now()
      },
      system: {
        cacheHits: 0,
        cacheMisses: 0,
        rateLimitHits: 0,
        authFailures: 0
      },
      usage: {
        activeUsers: new Set(),
        peakConcurrency: 0,
        currentConcurrency: 0
      }
    };

    this.buffer = [];
    this.startTime = Date.now();
    logger.info('Metrics reset');
  }
}

// Singleton instance
let metricsInstance = null;

export function getMetricsCollector(options = {}) {
  if (!metricsInstance) {
    metricsInstance = new MetricsCollector(options);
  }
  return metricsInstance;
}

export { MetricsCollector };

// CLI para visualizar métricas
if (import.meta.url === `file://${process.argv[1]}`) {
  const metrics = getMetricsCollector();

  const command = process.argv[2] || 'current';

  switch (command) {
    case 'current':
      console.log('📊 Current Metrics:');
      console.log(JSON.stringify(metrics.getMetrics(), null, 2));
      break;

    case 'detailed':
      console.log('📈 Detailed Report:');
      const report = await metrics.getDetailedReport();
      console.log(JSON.stringify(report, null, 2));
      break;

    case 'reset':
      metrics.reset();
      console.log('✅ Metrics reset');
      break;

    default:
      console.log('Usage: node metrics.js [current|detailed|reset]');
  }
}