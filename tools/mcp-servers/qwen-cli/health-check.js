#!/usr/bin/env node
import { exec } from 'child_process';
import { promisify } from 'util';
import { readFile, access } from 'fs/promises';
import { createServer } from 'http';
import os from 'os';
import path from 'path';
import { logger } from './logger.js';
import { getMetricsCollector } from './metrics.js';
import { getAuthManager } from './auth.js';
import { getPluginManager } from './plugins.js';

const execAsync = promisify(exec);

/**
 * Enterprise-grade Health Check & Observability System
 * Monitora status do sistema, dependências e performance
 */
class HealthChecker {
  constructor(options = {}) {
    this.options = {
      enableHealthEndpoint: options.enableHealthEndpoint !== false,
      healthPort: options.healthPort || 3001,
      checkInterval: options.checkInterval || 30000,
      enableAutoRestart: options.enableAutoRestart || false,
      maxFailures: options.maxFailures || 3,
      enableDependencyChecks: options.enableDependencyChecks !== false,
      ...options
    };

    this.checks = new Map();
    this.status = {
      overall: 'unknown',
      lastCheck: null,
      uptime: Date.now(),
      failures: 0,
      dependencies: {},
      system: {},
      components: {}
    };

    this.init();
  }

  async init() {
    this.registerDefaultChecks();

    if (this.options.enableHealthEndpoint) {
      this.startHealthEndpoint();
    }

    this.startPeriodicChecks();

    logger.info('Health checker initialized', {
      enableHealthEndpoint: this.options.enableHealthEndpoint,
      healthPort: this.options.healthPort,
      checkInterval: this.options.checkInterval
    });
  }

  registerDefaultChecks() {
    // Check básico do processo
    this.addCheck('process', async () => {
      const memUsage = process.memoryUsage();
      const cpuUsage = process.cpuUsage();

      return {
        status: 'healthy',
        details: {
          pid: process.pid,
          uptime: process.uptime(),
          memoryUsage: {
            rss: memUsage.rss,
            heapUsed: memUsage.heapUsed,
            heapTotal: memUsage.heapTotal,
            external: memUsage.external
          },
          cpuUsage
        }
      };
    });

    // Check do sistema operacional
    this.addCheck('system', async () => {
      const loadAvg = os.loadavg();
      const freeMem = os.freemem();
      const totalMem = os.totalmem();

      return {
        status: loadAvg[0] < os.cpus().length ? 'healthy' : 'warning',
        details: {
          platform: os.platform(),
          arch: os.arch(),
          nodeVersion: process.version,
          loadAverage: loadAvg,
          memory: {
            free: freeMem,
            total: totalMem,
            usage: ((totalMem - freeMem) / totalMem * 100).toFixed(2) + '%'
          },
          cpus: os.cpus().length
        }
      };
    });

    // Check do Qwen CLI
    this.addCheck('qwen-cli', async () => {
      try {
        const { stdout, stderr } = await execAsync('qwen --help', { timeout: 5000 });
        return {
          status: 'healthy',
          details: {
            available: true,
            version: 'detected',
            path: await this.findQwenPath()
          }
        };
      } catch (error) {
        return {
          status: 'unhealthy',
          error: error.message,
          details: {
            available: false,
            error: 'Qwen CLI not accessible'
          }
        };
      }
    });

    // Check das métricas
    this.addCheck('metrics', async () => {
      try {
        const metrics = getMetricsCollector();
        const stats = metrics.getMetrics();

        return {
          status: 'healthy',
          details: {
            requests: stats.requests.total,
            errors: stats.requests.errors,
            errorRate: stats.requests.errorRate,
            uptime: stats.uptime
          }
        };
      } catch (error) {
        return {
          status: 'warning',
          error: error.message,
          details: { available: false }
        };
      }
    });

    // Check do sistema de auth
    this.addCheck('auth', async () => {
      try {
        const auth = getAuthManager();
        const stats = auth.getStats();

        return {
          status: 'healthy',
          details: stats
        };
      } catch (error) {
        return {
          status: 'warning',
          error: error.message,
          details: { available: false }
        };
      }
    });

    // Check dos plugins
    this.addCheck('plugins', async () => {
      try {
        const pluginManager = getPluginManager();
        const stats = pluginManager.getStats();

        return {
          status: 'healthy',
          details: stats
        };
      } catch (error) {
        return {
          status: 'warning',
          error: error.message,
          details: { available: false }
        };
      }
    });

    // Check de conectividade de rede
    this.addCheck('network', async () => {
      try {
        // Test DNS resolution
        await execAsync('nslookup google.com', { timeout: 5000 });

        // Test HTTP connectivity
        const response = await fetch('https://httpbin.org/status/200', {
          signal: AbortSignal.timeout(5000)
        });

        return {
          status: response.ok ? 'healthy' : 'warning',
          details: {
            dns: 'working',
            http: response.ok ? 'working' : 'issues',
            responseTime: response.headers.get('x-response-time') || 'unknown'
          }
        };
      } catch (error) {
        return {
          status: 'warning',
          error: error.message,
          details: {
            connectivity: 'limited',
            error: 'Network connectivity issues'
          }
        };
      }
    });

    // Check de espaço em disco
    this.addCheck('disk', async () => {
      try {
        const { stdout } = await execAsync('df -h /', { timeout: 5000 });
        const lines = stdout.trim().split('\n');
        const data = lines[1].split(/\s+/);

        const usage = parseInt(data[4]);
        const status = usage > 90 ? 'critical' : usage > 80 ? 'warning' : 'healthy';

        return {
          status,
          details: {
            filesystem: data[0],
            size: data[1],
            used: data[2],
            available: data[3],
            usage: data[4],
            mountpoint: data[5]
          }
        };
      } catch (error) {
        return {
          status: 'warning',
          error: error.message,
          details: { available: false }
        };
      }
    });
  }

  addCheck(name, checkFunction, options = {}) {
    this.checks.set(name, {
      name,
      function: checkFunction,
      enabled: options.enabled !== false,
      critical: options.critical || false,
      timeout: options.timeout || 10000,
      interval: options.interval || this.options.checkInterval,
      lastRun: null,
      lastResult: null
    });
  }

  async runCheck(name) {
    const check = this.checks.get(name);
    if (!check || !check.enabled) {
      return null;
    }

    const startTime = Date.now();

    try {
      const result = await Promise.race([
        check.function(),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Check timeout')), check.timeout)
        )
      ]);

      const endTime = Date.now();
      const finalResult = {
        name,
        status: result.status,
        details: result.details || {},
        error: result.error || null,
        duration: endTime - startTime,
        timestamp: new Date().toISOString(),
        critical: check.critical
      };

      check.lastRun = new Date().toISOString();
      check.lastResult = finalResult;

      return finalResult;
    } catch (error) {
      const endTime = Date.now();
      const errorResult = {
        name,
        status: 'unhealthy',
        details: {},
        error: error.message,
        duration: endTime - startTime,
        timestamp: new Date().toISOString(),
        critical: check.critical
      };

      check.lastRun = new Date().toISOString();
      check.lastResult = errorResult;

      return errorResult;
    }
  }

  async runAllChecks() {
    const results = new Map();
    const promises = [];

    for (const [name, check] of this.checks.entries()) {
      if (check.enabled) {
        promises.push(
          this.runCheck(name).then(result => {
            if (result) {
              results.set(name, result);
            }
          })
        );
      }
    }

    await Promise.allSettled(promises);

    // Calcular status geral
    let overallStatus = 'healthy';
    let criticalFailures = 0;
    let warnings = 0;

    for (const result of results.values()) {
      if (result.status === 'unhealthy') {
        if (result.critical) {
          criticalFailures++;
          overallStatus = 'critical';
        } else {
          warnings++;
          if (overallStatus === 'healthy') {
            overallStatus = 'warning';
          }
        }
      } else if (result.status === 'warning') {
        warnings++;
        if (overallStatus === 'healthy') {
          overallStatus = 'warning';
        }
      }
    }

    this.status = {
      overall: overallStatus,
      lastCheck: new Date().toISOString(),
      uptime: Date.now() - this.status.uptime,
      failures: criticalFailures,
      warnings,
      components: Object.fromEntries(results)
    };

    logger.info('Health check completed', {
      status: overallStatus,
      criticalFailures,
      warnings,
      totalChecks: results.size
    });

    return this.status;
  }

  startPeriodicChecks() {
    setInterval(async () => {
      try {
        await this.runAllChecks();

        // Auto-restart logic
        if (this.options.enableAutoRestart && this.status.failures >= this.options.maxFailures) {
          logger.error('Critical failures detected, considering restart', {
            failures: this.status.failures,
            maxFailures: this.options.maxFailures
          });
          // Em produção, implementar lógica de restart
        }
      } catch (error) {
        logger.error('Failed to run periodic health checks', { error: error.message });
      }
    }, this.options.checkInterval);
  }

  startHealthEndpoint() {
    const server = createServer((req, res) => {
      res.setHeader('Content-Type', 'application/json');
      res.setHeader('Access-Control-Allow-Origin', '*');

      const url = new URL(req.url, `http://localhost:${this.options.healthPort}`);

      switch (url.pathname) {
        case '/health':
          this.handleHealthEndpoint(req, res);
          break;

        case '/health/live':
          this.handleLivenessEndpoint(req, res);
          break;

        case '/health/ready':
          this.handleReadinessEndpoint(req, res);
          break;

        case '/metrics':
          this.handleMetricsEndpoint(req, res);
          break;

        case '/info':
          this.handleInfoEndpoint(req, res);
          break;

        default:
          res.statusCode = 404;
          res.end(JSON.stringify({ error: 'Not found' }));
      }
    });

    server.listen(this.options.healthPort, () => {
      logger.info('Health endpoint started', { port: this.options.healthPort });
    });

    return server;
  }

  async handleHealthEndpoint(req, res) {
    try {
      const health = await this.runAllChecks();
      const statusCode = health.overall === 'healthy' ? 200 :
                        health.overall === 'warning' ? 200 : 503;

      res.statusCode = statusCode;
      res.end(JSON.stringify(health, null, 2));
    } catch (error) {
      res.statusCode = 500;
      res.end(JSON.stringify({ error: error.message }));
    }
  }

  handleLivenessEndpoint(req, res) {
    // Liveness probe - verifica se o processo está vivo
    res.statusCode = 200;
    res.end(JSON.stringify({
      status: 'alive',
      timestamp: new Date().toISOString(),
      uptime: process.uptime()
    }));
  }

  async handleReadinessEndpoint(req, res) {
    // Readiness probe - verifica se está pronto para receber tráfego
    try {
      const criticalChecks = ['qwen-cli', 'process'];
      const results = [];

      for (const checkName of criticalChecks) {
        const result = await this.runCheck(checkName);
        if (result) {
          results.push(result);
        }
      }

      const isReady = results.every(r => r.status === 'healthy');
      res.statusCode = isReady ? 200 : 503;
      res.end(JSON.stringify({
        status: isReady ? 'ready' : 'not_ready',
        checks: results,
        timestamp: new Date().toISOString()
      }));
    } catch (error) {
      res.statusCode = 500;
      res.end(JSON.stringify({ error: error.message }));
    }
  }

  handleMetricsEndpoint(req, res) {
    try {
      const metrics = getMetricsCollector();
      const data = metrics.getMetrics();
      res.statusCode = 200;
      res.end(JSON.stringify(data, null, 2));
    } catch (error) {
      res.statusCode = 500;
      res.end(JSON.stringify({ error: error.message }));
    }
  }

  handleInfoEndpoint(req, res) {
    const info = {
      name: 'Qwen MCP Server',
      version: '3.0.0',
      description: 'Enterprise-grade MCP Server for Qwen CLI',
      node: process.version,
      platform: os.platform(),
      arch: os.arch(),
      uptime: process.uptime(),
      startTime: new Date(Date.now() - process.uptime() * 1000).toISOString(),
      environment: process.env.NODE_ENV || 'development'
    };

    res.statusCode = 200;
    res.end(JSON.stringify(info, null, 2));
  }

  async findQwenPath() {
    try {
      const { stdout } = await execAsync('which qwen', { timeout: 2000 });
      return stdout.trim();
    } catch {
      return 'not found';
    }
  }

  getHealthStatus() {
    return this.status;
  }

  enableCheck(name) {
    const check = this.checks.get(name);
    if (check) {
      check.enabled = true;
      logger.info('Health check enabled', { name });
    }
  }

  disableCheck(name) {
    const check = this.checks.get(name);
    if (check) {
      check.enabled = false;
      logger.info('Health check disabled', { name });
    }
  }

  listChecks() {
    return Array.from(this.checks.values()).map(check => ({
      name: check.name,
      enabled: check.enabled,
      critical: check.critical,
      lastRun: check.lastRun,
      lastStatus: check.lastResult?.status,
      lastDuration: check.lastResult?.duration
    }));
  }
}

// Singleton instance
let healthCheckerInstance = null;

export function getHealthChecker(options = {}) {
  if (!healthCheckerInstance) {
    healthCheckerInstance = new HealthChecker(options);
  }
  return healthCheckerInstance;
}

export { HealthChecker };

// CLI para executar health checks
if (import.meta.url === `file://${process.argv[1]}`) {
  const healthChecker = getHealthChecker();

  const command = process.argv[2] || 'check';

  switch (command) {
    case 'check':
      console.log('🏥 Running health checks...');
      const result = await healthChecker.runAllChecks();
      console.log(JSON.stringify(result, null, 2));
      process.exit(result.overall === 'critical' ? 1 : 0);
      break;

    case 'list':
      console.log('📋 Available health checks:');
      const checks = healthChecker.listChecks();
      console.table(checks);
      break;

    case 'serve':
      console.log('🌐 Starting health endpoint...');
      healthChecker.startHealthEndpoint();
      break;

    default:
      console.log('Usage: node health-check.js [check|list|serve]');
  }
}