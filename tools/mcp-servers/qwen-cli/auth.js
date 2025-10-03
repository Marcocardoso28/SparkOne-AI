#!/usr/bin/env node
import jwt from 'jwt-simple';
import crypto from 'crypto';
import { readFile, writeFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';
import os from 'os';
import { logger } from './logger.js';

/**
 * Enterprise-grade Authentication & Authorization System
 * Suporta JWT, API Keys, OAuth flows e rate limiting
 */
class AuthManager {
  constructor(options = {}) {
    this.options = {
      jwtSecret: options.jwtSecret || this.generateSecret(),
      jwtExpiry: options.jwtExpiry || '24h',
      enableApiKeys: options.enableApiKeys || true,
      enableRateLimit: options.enableRateLimit || true,
      defaultRateLimit: options.defaultRateLimit || { requests: 100, window: 3600000 }, // 100 req/hora
      authFile: path.join(os.homedir(), '.qwen-mcp', 'auth.json'),
      ...options
    };

    this.users = new Map();
    this.apiKeys = new Map();
    this.rateLimits = new Map();
    this.blacklistedTokens = new Set();

    this.init();
  }

  async init() {
    await this.loadAuthData();
    this.startCleanupTimer();
    logger.info('Auth manager initialized', {
      enableApiKeys: this.options.enableApiKeys,
      enableRateLimit: this.options.enableRateLimit
    });
  }

  generateSecret() {
    return crypto.randomBytes(64).toString('hex');
  }

  async loadAuthData() {
    try {
      if (existsSync(this.options.authFile)) {
        const data = await readFile(this.options.authFile, 'utf-8');
        const authData = JSON.parse(data);

        // Carregar usuários
        if (authData.users) {
          for (const [id, user] of Object.entries(authData.users)) {
            this.users.set(id, user);
          }
        }

        // Carregar API keys
        if (authData.apiKeys) {
          for (const [key, data] of Object.entries(authData.apiKeys)) {
            this.apiKeys.set(key, data);
          }
        }

        logger.info('Auth data loaded', {
          users: this.users.size,
          apiKeys: this.apiKeys.size
        });
      }
    } catch (error) {
      logger.warn('Failed to load auth data', { error: error.message });
    }
  }

  async saveAuthData() {
    try {
      const authData = {
        users: Object.fromEntries(this.users),
        apiKeys: Object.fromEntries(this.apiKeys),
        lastUpdated: new Date().toISOString()
      };

      await writeFile(this.options.authFile, JSON.stringify(authData, null, 2));
      logger.debug('Auth data saved');
    } catch (error) {
      logger.error('Failed to save auth data', { error: error.message });
    }
  }

  // Criação de usuários
  async createUser(userData) {
    const userId = crypto.randomUUID();
    const user = {
      id: userId,
      email: userData.email,
      name: userData.name,
      role: userData.role || 'user',
      permissions: userData.permissions || ['qwen:read'],
      createdAt: new Date().toISOString(),
      lastLogin: null,
      isActive: true,
      metadata: userData.metadata || {}
    };

    this.users.set(userId, user);
    await this.saveAuthData();

    logger.info('User created', { userId, email: user.email, role: user.role });
    return user;
  }

  // Geração de JWT tokens
  generateToken(userId, options = {}) {
    const user = this.users.get(userId);
    if (!user || !user.isActive) {
      throw new Error('User not found or inactive');
    }

    const payload = {
      userId,
      email: user.email,
      role: user.role,
      permissions: user.permissions,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + this.parseExpiry(this.options.jwtExpiry),
      ...options
    };

    const token = jwt.encode(payload, this.options.jwtSecret);
    logger.info('JWT token generated', { userId, email: user.email });
    return token;
  }

  // Validação de JWT tokens
  validateToken(token) {
    try {
      if (this.blacklistedTokens.has(token)) {
        throw new Error('Token is blacklisted');
      }

      const payload = jwt.decode(token, this.options.jwtSecret);

      // Verificar expiração
      if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) {
        throw new Error('Token expired');
      }

      // Verificar se usuário ainda existe e está ativo
      const user = this.users.get(payload.userId);
      if (!user || !user.isActive) {
        throw new Error('User not found or inactive');
      }

      return { valid: true, payload, user };
    } catch (error) {
      logger.warn('Invalid token', { error: error.message });
      return { valid: false, error: error.message };
    }
  }

  // Geração de API Keys
  async generateApiKey(userId, options = {}) {
    const user = this.users.get(userId);
    if (!user) {
      throw new Error('User not found');
    }

    const apiKey = `qwen_${crypto.randomBytes(32).toString('hex')}`;
    const keyData = {
      key: apiKey,
      userId,
      name: options.name || 'Default API Key',
      permissions: options.permissions || user.permissions,
      rateLimit: options.rateLimit || this.options.defaultRateLimit,
      createdAt: new Date().toISOString(),
      lastUsed: null,
      isActive: true,
      metadata: options.metadata || {}
    };

    this.apiKeys.set(apiKey, keyData);
    await this.saveAuthData();

    logger.info('API key generated', { userId, keyName: keyData.name });
    return apiKey;
  }

  // Validação de API Keys
  validateApiKey(apiKey) {
    const keyData = this.apiKeys.get(apiKey);
    if (!keyData || !keyData.isActive) {
      return { valid: false, error: 'Invalid or inactive API key' };
    }

    const user = this.users.get(keyData.userId);
    if (!user || !user.isActive) {
      return { valid: false, error: 'User not found or inactive' };
    }

    // Atualizar último uso
    keyData.lastUsed = new Date().toISOString();

    return { valid: true, keyData, user };
  }

  // Rate Limiting
  checkRateLimit(identifier, rateLimit = null) {
    if (!this.options.enableRateLimit) {
      return { allowed: true };
    }

    const limit = rateLimit || this.options.defaultRateLimit;
    const now = Date.now();
    const windowStart = now - limit.window;

    if (!this.rateLimits.has(identifier)) {
      this.rateLimits.set(identifier, []);
    }

    const requests = this.rateLimits.get(identifier);

    // Remover requests fora da janela
    const validRequests = requests.filter(timestamp => timestamp > windowStart);
    this.rateLimits.set(identifier, validRequests);

    if (validRequests.length >= limit.requests) {
      const resetTime = Math.min(...validRequests) + limit.window;
      logger.warn('Rate limit exceeded', { identifier, requests: validRequests.length, limit: limit.requests });

      return {
        allowed: false,
        remaining: 0,
        resetTime,
        retryAfter: Math.ceil((resetTime - now) / 1000)
      };
    }

    // Adicionar request atual
    validRequests.push(now);
    this.rateLimits.set(identifier, validRequests);

    return {
      allowed: true,
      remaining: limit.requests - validRequests.length,
      resetTime: windowStart + limit.window
    };
  }

  // Middleware de autenticação
  createAuthMiddleware() {
    return (req, res, next) => {
      const token = this.extractToken(req);
      const apiKey = this.extractApiKey(req);

      let authResult = null;
      let identifier = req.ip;

      // Tentar JWT primeiro
      if (token) {
        authResult = this.validateToken(token);
        if (authResult.valid) {
          identifier = authResult.payload.userId;
          req.user = authResult.user;
          req.auth = { type: 'jwt', payload: authResult.payload };
        }
      }
      // Depois API Key
      else if (apiKey) {
        authResult = this.validateApiKey(apiKey);
        if (authResult.valid) {
          identifier = authResult.keyData.userId;
          req.user = authResult.user;
          req.auth = { type: 'apikey', keyData: authResult.keyData };
        }
      }

      // Rate limiting
      const rateLimit = req.auth?.keyData?.rateLimit || this.options.defaultRateLimit;
      const rateLimitResult = this.checkRateLimit(identifier, rateLimit);

      if (!rateLimitResult.allowed) {
        return res.status(429).json({
          error: 'Rate limit exceeded',
          retryAfter: rateLimitResult.retryAfter
        });
      }

      // Adicionar headers de rate limit
      res.set({
        'X-RateLimit-Limit': rateLimit.requests,
        'X-RateLimit-Remaining': rateLimitResult.remaining,
        'X-RateLimit-Reset': new Date(rateLimitResult.resetTime).toISOString()
      });

      if (!authResult || !authResult.valid) {
        return res.status(401).json({
          error: 'Authentication required',
          message: authResult?.error || 'No valid authentication provided'
        });
      }

      next();
    };
  }

  extractToken(req) {
    const authHeader = req.headers.authorization;
    if (authHeader && authHeader.startsWith('Bearer ')) {
      return authHeader.substring(7);
    }
    return null;
  }

  extractApiKey(req) {
    return req.headers['x-api-key'] || req.query.api_key;
  }

  // Verificar permissões
  hasPermission(user, permission) {
    if (user.role === 'admin') return true;
    return user.permissions.includes(permission) || user.permissions.includes('*');
  }

  // Revogar tokens
  revokeToken(token) {
    this.blacklistedTokens.add(token);
    logger.info('Token revoked');
  }

  // Desativar API key
  async revokeApiKey(apiKey) {
    const keyData = this.apiKeys.get(apiKey);
    if (keyData) {
      keyData.isActive = false;
      await this.saveAuthData();
      logger.info('API key revoked', { userId: keyData.userId });
    }
  }

  parseExpiry(expiry) {
    if (typeof expiry === 'number') return expiry;

    const units = {
      's': 1,
      'm': 60,
      'h': 3600,
      'd': 86400
    };

    const match = expiry.match(/^(\d+)([smhd])$/);
    if (match) {
      return parseInt(match[1]) * units[match[2]];
    }

    return 86400; // Default 24h
  }

  startCleanupTimer() {
    // Limpeza a cada hora
    setInterval(() => {
      this.cleanup();
    }, 3600000);
  }

  cleanup() {
    // Limpar rate limits antigos
    const now = Date.now();
    for (const [identifier, requests] of this.rateLimits.entries()) {
      const validRequests = requests.filter(timestamp => timestamp > now - 3600000);
      if (validRequests.length === 0) {
        this.rateLimits.delete(identifier);
      } else {
        this.rateLimits.set(identifier, validRequests);
      }
    }

    // Limpar tokens blacklisted antigos (manter por 24h)
    // Em produção, isso seria em um banco de dados com TTL

    logger.debug('Auth cleanup completed');
  }

  getStats() {
    return {
      users: this.users.size,
      apiKeys: this.apiKeys.size,
      activeRateLimits: this.rateLimits.size,
      blacklistedTokens: this.blacklistedTokens.size
    };
  }
}

// Singleton instance
let authInstance = null;

export function getAuthManager(options = {}) {
  if (!authInstance) {
    authInstance = new AuthManager(options);
  }
  return authInstance;
}

export { AuthManager };