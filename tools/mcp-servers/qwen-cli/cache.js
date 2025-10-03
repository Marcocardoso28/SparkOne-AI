#!/usr/bin/env node

import NodeCache from 'node-cache';
import Redis from 'ioredis';
import crypto from 'crypto';
import { logger } from './logger.js';

/**
 * Enterprise-grade Cache System
 * Suporta tanto cache local (NodeCache) quanto distribuído (Redis)
 */
class CacheManager {
  constructor(options = {}) {
    this.config = {
      enableLocal: options.enableLocal !== false,
      enableRedis: options.enableRedis || false,
      localTtl: options.localTtl || 300, // 5 minutos
      redisTtl: options.redisTtl || 3600, // 1 hora
      redisUrl: options.redisUrl || process.env.REDIS_URL,
      maxLocalSize: options.maxLocalSize || 1000,
      compressionThreshold: options.compressionThreshold || 1024 // 1KB
    };

    this.localCache = null;
    this.redisClient = null;
    this.initialized = false;

    this.init();
  }

  async init() {
    try {
      // Inicializar cache local
      if (this.config.enableLocal) {
        this.localCache = new NodeCache({
          stdTTL: this.config.localTtl,
          maxKeys: this.config.maxLocalSize,
          useClones: false,
          deleteOnExpire: true
        });

        this.localCache.on('expired', (key, value) => {
          logger.debug(`Cache local expirado: ${key}`);
        });

        logger.info('Cache local inicializado');
      }

      // Inicializar Redis se disponível
      if (this.config.enableRedis && this.config.redisUrl) {
        this.redisClient = new Redis(this.config.redisUrl, {
          retryDelayOnFailover: 100,
          maxRetriesPerRequest: 3,
          lazyConnect: true
        });

        await this.redisClient.connect();
        logger.info('Cache Redis conectado');
      }

      this.initialized = true;
    } catch (error) {
      logger.warn(`Erro ao inicializar cache: ${error.message}`);
      // Continuar apenas com cache local
      this.config.enableRedis = false;
    }
  }

  /**
   * Gerar chave hash para cache
   */
  _generateKey(key, params = {}) {
    const keyStr = typeof key === 'string' ? key : JSON.stringify(key);
    const paramsStr = Object.keys(params).length > 0 ? JSON.stringify(params) : '';
    const combined = `${keyStr}:${paramsStr}`;
    return crypto.createHash('sha256').update(combined).digest('hex').substring(0, 16);
  }

  /**
   * Cache para resultados do Qwen CLI
   */
  async cacheQwenResult(prompt, model, result, ttl = null) {
    const key = this._generateKey('qwen', { prompt, model });
    const data = {
      prompt,
      model,
      result,
      timestamp: Date.now(),
      ttl: ttl || this.config.localTtl
    };

    return this.set(key, data, ttl);
  }

  /**
   * Buscar resultado do Qwen CLI em cache
   */
  async getCachedQwenResult(prompt, model) {
    const key = this._generateKey('qwen', { prompt, model });
    const cached = await this.get(key);

    if (cached) {
      logger.debug(`Cache hit para Qwen: ${prompt.substring(0, 50)}...`);
      return cached.result;
    }

    logger.debug(`Cache miss para Qwen: ${prompt.substring(0, 50)}...`);
    return null;
  }

  /**
   * Cache para análise de código
   */
  async cacheCodeAnalysis(code, analysisType, language, result, ttl = null) {
    const codeHash = crypto.createHash('sha256').update(code).digest('hex').substring(0, 12);
    const key = this._generateKey('code_analysis', { codeHash, analysisType, language });

    const data = {
      codeHash,
      analysisType,
      language,
      result,
      timestamp: Date.now()
    };

    return this.set(key, data, ttl);
  }

  /**
   * Buscar análise de código em cache
   */
  async getCachedCodeAnalysis(code, analysisType, language) {
    const codeHash = crypto.createHash('sha256').update(code).digest('hex').substring(0, 12);
    const key = this._generateKey('code_analysis', { codeHash, analysisType, language });

    const cached = await this.get(key);
    if (cached) {
      logger.debug(`Cache hit para análise de código: ${analysisType}/${language}`);
      return cached.result;
    }

    return null;
  }

  /**
   * Método genérico GET
   */
  async get(key) {
    try {
      // Tentar cache local primeiro (mais rápido)
      if (this.localCache) {
        const localResult = this.localCache.get(key);
        if (localResult) {
          return localResult;
        }
      }

      // Tentar Redis se disponível
      if (this.redisClient) {
        const redisResult = await this.redisClient.get(key);
        if (redisResult) {
          const parsed = JSON.parse(redisResult);

          // Atualizar cache local
          if (this.localCache) {
            this.localCache.set(key, parsed, this.config.localTtl);
          }

          return parsed;
        }
      }

      return null;
    } catch (error) {
      logger.error(`Erro ao buscar cache ${key}: ${error.message}`);
      return null;
    }
  }

  /**
   * Método genérico SET
   */
  async set(key, value, ttl = null) {
    try {
      const finalTtl = ttl || this.config.localTtl;

      // Salvar no cache local
      if (this.localCache) {
        this.localCache.set(key, value, finalTtl);
      }

      // Salvar no Redis se disponível
      if (this.redisClient) {
        const redisTtl = ttl || this.config.redisTtl;
        await this.redisClient.setex(key, redisTtl, JSON.stringify(value));
      }

      return true;
    } catch (error) {
      logger.error(`Erro ao salvar cache ${key}: ${error.message}`);
      return false;
    }
  }

  /**
   * Invalidar cache por padrão
   */
  async invalidate(pattern) {
    try {
      // Invalidar cache local
      if (this.localCache) {
        const keys = this.localCache.keys();
        const matchingKeys = keys.filter(key => key.includes(pattern));
        this.localCache.del(matchingKeys);
        logger.debug(`Invalidados ${matchingKeys.length} itens do cache local`);
      }

      // Invalidar Redis
      if (this.redisClient) {
        const keys = await this.redisClient.keys(`*${pattern}*`);
        if (keys.length > 0) {
          await this.redisClient.del(...keys);
          logger.debug(`Invalidados ${keys.length} itens do Redis`);
        }
      }

      return true;
    } catch (error) {
      logger.error(`Erro ao invalidar cache ${pattern}: ${error.message}`);
      return false;
    }
  }

  /**
   * Estatísticas do cache
   */
  getStats() {
    const stats = {
      local: null,
      redis: null,
      timestamp: Date.now()
    };

    if (this.localCache) {
      stats.local = {
        keys: this.localCache.keys().length,
        hits: this.localCache.getStats().hits,
        misses: this.localCache.getStats().misses,
        hitRate: this.localCache.getStats().hits / (this.localCache.getStats().hits + this.localCache.getStats().misses)
      };
    }

    return stats;
  }

  /**
   * Limpar todo o cache
   */
  async clear() {
    try {
      if (this.localCache) {
        this.localCache.flushAll();
      }

      if (this.redisClient) {
        await this.redisClient.flushall();
      }

      logger.info('Cache limpo completamente');
      return true;
    } catch (error) {
      logger.error(`Erro ao limpar cache: ${error.message}`);
      return false;
    }
  }

  /**
   * Fechar conexões
   */
  async close() {
    try {
      if (this.localCache) {
        this.localCache.close();
      }

      if (this.redisClient) {
        await this.redisClient.quit();
      }

      logger.info('Cache fechado');
    } catch (error) {
      logger.error(`Erro ao fechar cache: ${error.message}`);
    }
  }
}

// Instância singleton
let cacheInstance = null;

export function getCache(options = {}) {
  if (!cacheInstance) {
    cacheInstance = new CacheManager(options);
  }
  return cacheInstance;
}

export { CacheManager };