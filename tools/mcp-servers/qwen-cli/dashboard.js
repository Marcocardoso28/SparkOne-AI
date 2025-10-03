#!/usr/bin/env node
import express from 'express';
import { readFile } from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { logger } from './logger.js';
import { getMetricsCollector } from './metrics.js';
import { getHealthChecker } from './health-check.js';
import { getAuthManager } from './auth.js';
import { getPluginManager } from './plugins.js';
import { getWebhookManager } from './webhooks.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Enterprise-grade Web Dashboard
 * Interface web para administração e monitoramento do MCP server
 */
class Dashboard {
  constructor(options = {}) {
    this.options = {
      port: options.port || 3000,
      enableAuth: options.enableAuth || false,
      enableCORS: options.enableCORS || true,
      ...options
    };

    this.app = express();
    this.setupMiddleware();
    this.setupRoutes();
  }

  setupMiddleware() {
    // CORS
    if (this.options.enableCORS) {
      this.app.use((req, res, next) => {
        res.header('Access-Control-Allow-Origin', '*');
        res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
        res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
        if (req.method === 'OPTIONS') {
          res.sendStatus(200);
        } else {
          next();
        }
      });
    }

    // JSON parser
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));

    // Request logging
    this.app.use((req, res, next) => {
      logger.info('Dashboard request', {
        method: req.method,
        url: req.url,
        ip: req.ip,
        userAgent: req.get('User-Agent')
      });
      next();
    });

    // Auth middleware (opcional)
    if (this.options.enableAuth) {
      const authManager = getAuthManager();
      this.app.use('/api', authManager.createAuthMiddleware());
    }
  }

  setupRoutes() {
    // Dashboard HTML
    this.app.get('/', async (req, res) => {
      try {
        const htmlPath = path.join(__dirname, 'dashboard.html');
        const html = await readFile(htmlPath, 'utf-8');
        res.setHeader('Content-Type', 'text/html');
        res.send(html);
      } catch (error) {
        logger.error('Failed to serve dashboard HTML', { error: error.message });
        res.status(500).json({ error: 'Failed to load dashboard' });
      }
    });

    // API Routes
    this.setupAPIRoutes();

    // Health endpoints (para load balancers)
    this.app.get('/health', async (req, res) => {
      try {
        const healthChecker = getHealthChecker();
        const health = await healthChecker.runAllChecks();

        const statusCode = health.overall === 'healthy' ? 200 :
                          health.overall === 'warning' ? 200 : 503;

        res.status(statusCode).json(health);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    this.app.get('/metrics', async (req, res) => {
      try {
        const metrics = getMetricsCollector();
        const data = await metrics.getDetailedReport();
        res.json(data);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'Not found',
        path: req.originalUrl,
        method: req.method
      });
    });

    // Error handler
    this.app.use((error, req, res, next) => {
      logger.error('Dashboard error', {
        error: error.message,
        stack: error.stack,
        url: req.url,
        method: req.method
      });

      res.status(500).json({
        error: 'Internal server error',
        message: error.message
      });
    });
  }

  setupAPIRoutes() {
    const api = express.Router();

    // System info
    api.get('/info', async (req, res) => {
      try {
        const info = {
          name: 'Qwen MCP Server',
          version: '3.0.0',
          description: 'Enterprise-grade MCP Server for Qwen CLI',
          node: process.version,
          platform: process.platform,
          arch: process.arch,
          uptime: process.uptime(),
          startTime: new Date(Date.now() - process.uptime() * 1000).toISOString(),
          environment: process.env.NODE_ENV || 'development',
          pid: process.pid
        };

        res.json(info);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Metrics endpoints
    api.get('/metrics', async (req, res) => {
      try {
        const metrics = getMetricsCollector();
        const data = await metrics.getDetailedReport();
        res.json(data);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    api.get('/metrics/current', async (req, res) => {
      try {
        const metrics = getMetricsCollector();
        const data = metrics.getMetrics();
        res.json(data);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    api.post('/metrics/reset', async (req, res) => {
      try {
        const metrics = getMetricsCollector();
        metrics.reset();
        res.json({ message: 'Metrics reset successfully' });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Health endpoints
    api.get('/health', async (req, res) => {
      try {
        const healthChecker = getHealthChecker();
        const health = await healthChecker.runAllChecks();
        res.json(health);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    api.get('/health/:checkName', async (req, res) => {
      try {
        const healthChecker = getHealthChecker();
        const result = await healthChecker.runCheck(req.params.checkName);

        if (result) {
          res.json(result);
        } else {
          res.status(404).json({ error: 'Health check not found' });
        }
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    api.get('/health/checks/list', async (req, res) => {
      try {
        const healthChecker = getHealthChecker();
        const checks = healthChecker.listChecks();
        res.json(checks);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Auth endpoints
    api.get('/auth/stats', async (req, res) => {
      try {
        const authManager = getAuthManager();
        const stats = authManager.getStats();
        res.json(stats);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    api.post('/auth/users', async (req, res) => {
      try {
        const authManager = getAuthManager();
        const user = await authManager.createUser(req.body);
        res.status(201).json(user);
      } catch (error) {
        res.status(400).json({ error: error.message });
      }
    });

    api.post('/auth/apikeys', async (req, res) => {
      try {
        const authManager = getAuthManager();
        const { userId, ...options } = req.body;
        const apiKey = await authManager.generateApiKey(userId, options);
        res.status(201).json({ apiKey });
      } catch (error) {
        res.status(400).json({ error: error.message });
      }
    });

    // Plugin endpoints
    api.get('/plugins', async (req, res) => {
      try {
        const pluginManager = getPluginManager();
        const plugins = pluginManager.listPlugins();
        res.json(plugins);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    api.get('/plugins/stats', async (req, res) => {
      try {
        const pluginManager = getPluginManager();
        const stats = pluginManager.getStats();
        res.json(stats);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    api.post('/plugins/:name/enable', async (req, res) => {
      try {
        const pluginManager = getPluginManager();
        pluginManager.enablePlugin(req.params.name);
        res.json({ message: 'Plugin enabled' });
      } catch (error) {
        res.status(400).json({ error: error.message });
      }
    });

    api.post('/plugins/:name/disable', async (req, res) => {
      try {
        const pluginManager = getPluginManager();
        pluginManager.disablePlugin(req.params.name);
        res.json({ message: 'Plugin disabled' });
      } catch (error) {
        res.status(400).json({ error: error.message });
      }
    });

    api.post('/plugins/:name/reload', async (req, res) => {
      try {
        const pluginManager = getPluginManager();
        const plugin = await pluginManager.reloadPlugin(req.params.name);
        res.json(plugin);
      } catch (error) {
        res.status(400).json({ error: error.message });
      }
    });

    // Webhook endpoints
    api.get('/webhooks', async (req, res) => {
      try {
        const webhookManager = getWebhookManager();
        const webhooks = webhookManager.listWebhooks();
        res.json(webhooks);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    api.get('/webhooks/stats', async (req, res) => {
      try {
        const webhookManager = getWebhookManager();
        const stats = webhookManager.getStats();
        res.json(stats);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    api.post('/webhooks', async (req, res) => {
      try {
        const webhookManager = getWebhookManager();
        const webhook = await webhookManager.createWebhook(req.body);
        res.status(201).json(webhook);
      } catch (error) {
        res.status(400).json({ error: error.message });
      }
    });

    api.put('/webhooks/:id', async (req, res) => {
      try {
        const webhookManager = getWebhookManager();
        const webhook = await webhookManager.updateWebhook(req.params.id, req.body);
        res.json(webhook);
      } catch (error) {
        res.status(400).json({ error: error.message });
      }
    });

    api.delete('/webhooks/:id', async (req, res) => {
      try {
        const webhookManager = getWebhookManager();
        await webhookManager.deleteWebhook(req.params.id);
        res.json({ message: 'Webhook deleted' });
      } catch (error) {
        res.status(400).json({ error: error.message });
      }
    });

    api.post('/webhooks/:id/test', async (req, res) => {
      try {
        const webhookManager = getWebhookManager();
        const testEvent = await webhookManager.testWebhook(req.params.id);
        res.json({ message: 'Test webhook sent', event: testEvent });
      } catch (error) {
        res.status(400).json({ error: error.message });
      }
    });

    api.get('/webhooks/events', async (req, res) => {
      try {
        const webhookManager = getWebhookManager();
        const limit = parseInt(req.query.limit) || 100;
        const events = webhookManager.getEventHistory(limit);
        res.json(events);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Cache endpoints
    api.get('/cache/stats', async (req, res) => {
      try {
        // Implementar quando cache estiver disponível
        res.json({
          hits: 0,
          misses: 0,
          size: 0,
          hitRate: 0
        });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    api.post('/cache/clear', async (req, res) => {
      try {
        // Implementar limpeza de cache
        res.json({ message: 'Cache cleared' });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Config endpoints
    api.get('/config', async (req, res) => {
      try {
        // Retornar configuração não-sensível
        const config = {
          environment: process.env.NODE_ENV || 'development',
          features: {
            auth: this.options.enableAuth,
            cors: this.options.enableCORS,
            webhooks: true,
            plugins: true,
            metrics: true
          }
        };
        res.json(config);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    this.app.use('/api', api);
  }

  start() {
    return new Promise((resolve) => {
      const server = this.app.listen(this.options.port, () => {
        logger.info('Dashboard started', {
          port: this.options.port,
          url: `http://localhost:${this.options.port}`,
          enableAuth: this.options.enableAuth
        });
        resolve(server);
      });
    });
  }
}

// Singleton instance
let dashboardInstance = null;

export function getDashboard(options = {}) {
  if (!dashboardInstance) {
    dashboardInstance = new Dashboard(options);
  }
  return dashboardInstance;
}

export { Dashboard };

// CLI para iniciar o dashboard
if (import.meta.url === `file://${process.argv[1]}`) {
  const port = process.argv[2] || 3000;
  const enableAuth = process.argv.includes('--auth');

  const dashboard = getDashboard({ port, enableAuth });

  dashboard.start().then(() => {
    console.log(`🌐 Dashboard disponível em: http://localhost:${port}`);
    console.log(`🔐 Autenticação: ${enableAuth ? 'Habilitada' : 'Desabilitada'}`);
    console.log('📊 Endpoints disponíveis:');
    console.log('  - /           - Dashboard web');
    console.log('  - /health     - Health checks');
    console.log('  - /metrics    - Métricas');
    console.log('  - /api/*      - API REST');
  }).catch(error => {
    console.error('❌ Erro ao iniciar dashboard:', error.message);
    process.exit(1);
  });
}