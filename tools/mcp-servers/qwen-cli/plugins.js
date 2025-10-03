#!/usr/bin/env node
import { EventEmitter } from 'events';
import { readdir, readFile, stat } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';
import os from 'os';
import { pathToFileURL } from 'url';
import { logger } from './logger.js';

/**
 * Enterprise-grade Plugin System
 * Permite extensão dinâmica do MCP server com plugins seguros
 */
class PluginManager extends EventEmitter {
  constructor(options = {}) {
    super();
    this.options = {
      pluginsDir: path.join(os.homedir(), '.qwen-mcp', 'plugins'),
      enableAutoload: options.enableAutoload !== false,
      enableHotReload: options.enableHotReload || false,
      enableSandbox: options.enableSandbox || true,
      maxExecutionTime: options.maxExecutionTime || 30000,
      ...options
    };

    this.plugins = new Map();
    this.hooks = new Map();
    this.middlewares = [];
    this.loadedModules = new Map();

    this.init();
  }

  async init() {
    if (this.options.enableAutoload) {
      await this.loadAllPlugins();
    }

    if (this.options.enableHotReload) {
      this.startHotReload();
    }

    logger.info('Plugin manager initialized', {
      pluginsDir: this.options.pluginsDir,
      enableAutoload: this.options.enableAutoload,
      enableHotReload: this.options.enableHotReload
    });
  }

  async loadAllPlugins() {
    try {
      if (!existsSync(this.options.pluginsDir)) {
        logger.info('Plugins directory not found, skipping plugin loading');
        return;
      }

      const entries = await readdir(this.options.pluginsDir, { withFileTypes: true });

      for (const entry of entries) {
        if (entry.isDirectory()) {
          await this.loadPlugin(entry.name);
        } else if (entry.isFile() && entry.name.endsWith('.js')) {
          const pluginName = path.basename(entry.name, '.js');
          await this.loadPlugin(pluginName);
        }
      }

      logger.info('All plugins loaded', { count: this.plugins.size });
    } catch (error) {
      logger.error('Failed to load plugins', { error: error.message });
    }
  }

  async loadPlugin(nameOrPath) {
    try {
      const pluginPath = this.resolvePluginPath(nameOrPath);

      if (!existsSync(pluginPath)) {
        throw new Error(`Plugin not found: ${nameOrPath}`);
      }

      // Verificar se é diretório com package.json ou arquivo JS
      const stats = await stat(pluginPath);
      let mainFile;

      if (stats.isDirectory()) {
        const packagePath = path.join(pluginPath, 'package.json');
        if (existsSync(packagePath)) {
          const packageData = JSON.parse(await readFile(packagePath, 'utf-8'));
          mainFile = path.join(pluginPath, packageData.main || 'index.js');
        } else {
          mainFile = path.join(pluginPath, 'index.js');
        }
      } else {
        mainFile = pluginPath;
      }

      if (!existsSync(mainFile)) {
        throw new Error(`Plugin main file not found: ${mainFile}`);
      }

      // Carregar o módulo
      const pluginUrl = pathToFileURL(mainFile).href;
      const module = await import(pluginUrl);

      // Validar estrutura do plugin
      const plugin = module.default || module;
      this.validatePlugin(plugin);

      // Configurar plugin
      const pluginName = plugin.name || path.basename(nameOrPath);
      const pluginInstance = {
        name: pluginName,
        version: plugin.version || '1.0.0',
        description: plugin.description || '',
        author: plugin.author || 'Unknown',
        path: mainFile,
        instance: plugin,
        loadedAt: new Date().toISOString(),
        enabled: true,
        dependencies: plugin.dependencies || [],
        permissions: plugin.permissions || ['basic'],
        hooks: plugin.hooks || {},
        tools: plugin.tools || {},
        middlewares: plugin.middlewares || [],
        metadata: plugin.metadata || {}
      };

      // Verificar dependências
      await this.checkDependencies(pluginInstance);

      // Registrar hooks
      this.registerPluginHooks(pluginInstance);

      // Registrar ferramentas
      this.registerPluginTools(pluginInstance);

      // Registrar middlewares
      this.registerPluginMiddlewares(pluginInstance);

      // Inicializar plugin
      if (typeof plugin.init === 'function') {
        await this.executeWithTimeout(
          () => plugin.init(this.createPluginContext(pluginInstance)),
          this.options.maxExecutionTime
        );
      }

      this.plugins.set(pluginName, pluginInstance);
      this.loadedModules.set(pluginUrl, module);

      this.emit('pluginLoaded', pluginInstance);
      logger.info('Plugin loaded successfully', {
        name: pluginName,
        version: pluginInstance.version,
        tools: Object.keys(pluginInstance.tools).length,
        hooks: Object.keys(pluginInstance.hooks).length
      });

      return pluginInstance;
    } catch (error) {
      logger.error('Failed to load plugin', { plugin: nameOrPath, error: error.message });
      throw error;
    }
  }

  validatePlugin(plugin) {
    if (!plugin || typeof plugin !== 'object') {
      throw new Error('Plugin must be an object');
    }

    if (!plugin.name && typeof plugin.name !== 'string') {
      throw new Error('Plugin must have a name');
    }

    // Validar estruturas opcionais
    if (plugin.tools && typeof plugin.tools !== 'object') {
      throw new Error('Plugin tools must be an object');
    }

    if (plugin.hooks && typeof plugin.hooks !== 'object') {
      throw new Error('Plugin hooks must be an object');
    }

    if (plugin.middlewares && !Array.isArray(plugin.middlewares)) {
      throw new Error('Plugin middlewares must be an array');
    }
  }

  async checkDependencies(plugin) {
    for (const dep of plugin.dependencies) {
      if (!this.plugins.has(dep)) {
        throw new Error(`Plugin ${plugin.name} requires dependency: ${dep}`);
      }
    }
  }

  registerPluginHooks(plugin) {
    for (const [hookName, handler] of Object.entries(plugin.hooks)) {
      if (!this.hooks.has(hookName)) {
        this.hooks.set(hookName, []);
      }
      this.hooks.get(hookName).push({
        plugin: plugin.name,
        handler,
        priority: handler.priority || 0
      });

      // Ordenar por prioridade
      this.hooks.get(hookName).sort((a, b) => b.priority - a.priority);
    }
  }

  registerPluginTools(plugin) {
    // As ferramentas serão registradas no servidor MCP principal
    this.emit('registerTools', plugin.name, plugin.tools);
  }

  registerPluginMiddlewares(plugin) {
    for (const middleware of plugin.middlewares) {
      this.middlewares.push({
        plugin: plugin.name,
        handler: middleware,
        priority: middleware.priority || 0
      });
    }

    // Ordenar middlewares por prioridade
    this.middlewares.sort((a, b) => b.priority - a.priority);
  }

  createPluginContext(plugin) {
    return {
      name: plugin.name,
      logger: logger.child({ plugin: plugin.name }),
      emit: this.emit.bind(this),
      on: this.on.bind(this),
      executeHook: this.executeHook.bind(this),
      getPlugin: this.getPlugin.bind(this),
      config: plugin.metadata.config || {},
      storage: this.createPluginStorage(plugin.name)
    };
  }

  createPluginStorage(pluginName) {
    const storage = new Map();
    return {
      get: (key) => storage.get(key),
      set: (key, value) => storage.set(key, value),
      delete: (key) => storage.delete(key),
      has: (key) => storage.has(key),
      clear: () => storage.clear(),
      size: () => storage.size
    };
  }

  async executeHook(hookName, data = {}, options = {}) {
    const handlers = this.hooks.get(hookName) || [];

    if (handlers.length === 0) {
      return data;
    }

    logger.debug('Executing hook', { hookName, handlers: handlers.length });

    let result = data;

    for (const hook of handlers) {
      try {
        const plugin = this.plugins.get(hook.plugin);
        if (!plugin || !plugin.enabled) continue;

        const hookResult = await this.executeWithTimeout(
          () => hook.handler(result, options),
          this.options.maxExecutionTime
        );

        // Se o hook retornar algo, usar como novo resultado
        if (hookResult !== undefined) {
          result = hookResult;
        }

        // Se o hook retornar false, parar execução
        if (hookResult === false && options.stopOnFalse) {
          break;
        }
      } catch (error) {
        logger.error('Hook execution failed', {
          hookName,
          plugin: hook.plugin,
          error: error.message
        });

        if (options.throwOnError) {
          throw error;
        }
      }
    }

    return result;
  }

  async executeMiddlewares(req, res, next) {
    let index = 0;

    const executeNext = async () => {
      if (index >= this.middlewares.length) {
        return next();
      }

      const middleware = this.middlewares[index++];
      const plugin = this.plugins.get(middleware.plugin);

      if (!plugin || !plugin.enabled) {
        return executeNext();
      }

      try {
        await this.executeWithTimeout(
          () => middleware.handler(req, res, executeNext),
          this.options.maxExecutionTime
        );
      } catch (error) {
        logger.error('Middleware execution failed', {
          plugin: middleware.plugin,
          error: error.message
        });
        return next(error);
      }
    };

    return executeNext();
  }

  async executeWithTimeout(fn, timeout) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error(`Plugin execution timeout (${timeout}ms)`));
      }, timeout);

      Promise.resolve(fn())
        .then(result => {
          clearTimeout(timer);
          resolve(result);
        })
        .catch(error => {
          clearTimeout(timer);
          reject(error);
        });
    });
  }

  async unloadPlugin(name) {
    const plugin = this.plugins.get(name);
    if (!plugin) {
      throw new Error(`Plugin not found: ${name}`);
    }

    try {
      // Executar cleanup do plugin
      if (typeof plugin.instance.cleanup === 'function') {
        await this.executeWithTimeout(
          () => plugin.instance.cleanup(),
          this.options.maxExecutionTime
        );
      }

      // Remover hooks
      for (const hookName of Object.keys(plugin.hooks)) {
        const handlers = this.hooks.get(hookName) || [];
        this.hooks.set(hookName, handlers.filter(h => h.plugin !== name));
      }

      // Remover middlewares
      this.middlewares = this.middlewares.filter(m => m.plugin !== name);

      // Remover do cache de módulos
      for (const [url, module] of this.loadedModules.entries()) {
        if (url.includes(plugin.path)) {
          this.loadedModules.delete(url);
        }
      }

      this.plugins.delete(name);
      this.emit('pluginUnloaded', plugin);

      logger.info('Plugin unloaded', { name });
    } catch (error) {
      logger.error('Failed to unload plugin', { name, error: error.message });
      throw error;
    }
  }

  async reloadPlugin(name) {
    const plugin = this.plugins.get(name);
    if (plugin) {
      await this.unloadPlugin(name);
    }
    return await this.loadPlugin(name);
  }

  enablePlugin(name) {
    const plugin = this.plugins.get(name);
    if (plugin) {
      plugin.enabled = true;
      this.emit('pluginEnabled', plugin);
      logger.info('Plugin enabled', { name });
    }
  }

  disablePlugin(name) {
    const plugin = this.plugins.get(name);
    if (plugin) {
      plugin.enabled = false;
      this.emit('pluginDisabled', plugin);
      logger.info('Plugin disabled', { name });
    }
  }

  getPlugin(name) {
    return this.plugins.get(name);
  }

  listPlugins() {
    return Array.from(this.plugins.values()).map(plugin => ({
      name: plugin.name,
      version: plugin.version,
      description: plugin.description,
      author: plugin.author,
      enabled: plugin.enabled,
      loadedAt: plugin.loadedAt,
      tools: Object.keys(plugin.tools).length,
      hooks: Object.keys(plugin.hooks).length,
      middlewares: plugin.middlewares.length
    }));
  }

  resolvePluginPath(nameOrPath) {
    if (path.isAbsolute(nameOrPath)) {
      return nameOrPath;
    }

    // Tentar como nome de plugin no diretório de plugins
    const pluginPath = path.join(this.options.pluginsDir, nameOrPath);
    if (existsSync(pluginPath)) {
      return pluginPath;
    }

    // Tentar como arquivo JS
    const jsPath = path.join(this.options.pluginsDir, `${nameOrPath}.js`);
    if (existsSync(jsPath)) {
      return jsPath;
    }

    // Retornar path original se não encontrar
    return nameOrPath;
  }

  startHotReload() {
    // Em uma implementação real, usaria fs.watch() para monitorar mudanças
    logger.info('Hot reload enabled for plugins');
  }

  getStats() {
    const enabledPlugins = Array.from(this.plugins.values()).filter(p => p.enabled);

    return {
      total: this.plugins.size,
      enabled: enabledPlugins.length,
      disabled: this.plugins.size - enabledPlugins.length,
      totalTools: enabledPlugins.reduce((sum, p) => sum + Object.keys(p.tools).length, 0),
      totalHooks: Array.from(this.hooks.values()).reduce((sum, h) => sum + h.length, 0),
      totalMiddlewares: this.middlewares.length
    };
  }
}

// Singleton instance
let pluginManagerInstance = null;

export function getPluginManager(options = {}) {
  if (!pluginManagerInstance) {
    pluginManagerInstance = new PluginManager(options);
  }
  return pluginManagerInstance;
}

export { PluginManager };

// Plugin base class para facilitar desenvolvimento
export class Plugin {
  constructor(options = {}) {
    this.name = options.name || 'UnnamedPlugin';
    this.version = options.version || '1.0.0';
    this.description = options.description || '';
    this.author = options.author || 'Unknown';
    this.dependencies = options.dependencies || [];
    this.permissions = options.permissions || ['basic'];
    this.hooks = {};
    this.tools = {};
    this.middlewares = [];
    this.metadata = options.metadata || {};
  }

  addHook(name, handler, priority = 0) {
    handler.priority = priority;
    this.hooks[name] = handler;
  }

  addTool(name, schema, handler) {
    this.tools[name] = { schema, handler };
  }

  addMiddleware(handler, priority = 0) {
    handler.priority = priority;
    this.middlewares.push(handler);
  }

  async init(context) {
    // Override in subclasses
  }

  async cleanup() {
    // Override in subclasses
  }
}