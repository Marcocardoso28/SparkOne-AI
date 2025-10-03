#!/usr/bin/env node
import { readdir, stat, readFile, writeFile, mkdir, copyFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';
import os from 'os';
import { exec } from 'child_process';
import { promisify } from 'util';
import { createWriteStream, createReadStream } from 'fs';
import { pipeline } from 'stream/promises';
import { createGzip, createGunzip } from 'zlib';
import cron from 'node-cron';
import crypto from 'crypto';
import { logger } from './logger.js';

const execAsync = promisify(exec);

/**
 * Enterprise-grade Backup & Recovery System
 * Sistema completo de backup automático com compressão, encriptação e recovery
 */
class BackupManager {
  constructor(options = {}) {
    this.options = {
      backupDir: path.join(os.homedir(), '.qwen-mcp', 'backups'),
      dataDir: path.join(os.homedir(), '.qwen-mcp'),
      enableAutoBackup: options.enableAutoBackup !== false,
      backupSchedule: options.backupSchedule || '0 2 * * *', // Daily at 2 AM
      retentionDays: options.retentionDays || 30,
      enableCompression: options.enableCompression !== false,
      enableEncryption: options.enableEncryption || false,
      encryptionKey: options.encryptionKey,
      maxBackupSize: options.maxBackupSize || 500 * 1024 * 1024, // 500MB
      enableCloudSync: options.enableCloudSync || false,
      cloudProvider: options.cloudProvider, // 's3', 'gcs', 'azure'
      cloudConfig: options.cloudConfig || {},
      ...options
    };

    this.backupHistory = [];
    this.isBackupRunning = false;

    this.init();
  }

  async init() {
    await this.ensureBackupDir();
    await this.loadBackupHistory();

    if (this.options.enableAutoBackup) {
      this.scheduleBackups();
    }

    logger.info('Backup manager initialized', {
      backupDir: this.options.backupDir,
      enableAutoBackup: this.options.enableAutoBackup,
      retentionDays: this.options.retentionDays
    });
  }

  async ensureBackupDir() {
    if (!existsSync(this.options.backupDir)) {
      await mkdir(this.options.backupDir, { recursive: true });
    }
  }

  async loadBackupHistory() {
    try {
      const historyFile = path.join(this.options.backupDir, 'backup-history.json');
      if (existsSync(historyFile)) {
        const data = await readFile(historyFile, 'utf-8');
        this.backupHistory = JSON.parse(data);
        logger.info('Backup history loaded', { backups: this.backupHistory.length });
      }
    } catch (error) {
      logger.warn('Failed to load backup history', { error: error.message });
    }
  }

  async saveBackupHistory() {
    try {
      const historyFile = path.join(this.options.backupDir, 'backup-history.json');
      await writeFile(historyFile, JSON.stringify(this.backupHistory, null, 2));
    } catch (error) {
      logger.error('Failed to save backup history', { error: error.message });
    }
  }

  scheduleBackups() {
    cron.schedule(this.options.backupSchedule, () => {
      this.createBackup().catch(error => {
        logger.error('Scheduled backup failed', { error: error.message });
      });
    });

    logger.info('Automatic backups scheduled', { schedule: this.options.backupSchedule });
  }

  async createBackup(options = {}) {
    if (this.isBackupRunning) {
      throw new Error('Backup already in progress');
    }

    this.isBackupRunning = true;
    const startTime = Date.now();

    try {
      const backupId = crypto.randomUUID();
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const backupName = options.name || `backup-${timestamp}`;

      logger.info('Starting backup', { backupId, backupName });

      // Criar diretório temporário para o backup
      const tempDir = path.join(this.options.backupDir, 'temp', backupId);
      await mkdir(tempDir, { recursive: true });

      // Coletar dados para backup
      const backupData = await this.collectBackupData();

      // Criar manifest do backup
      const manifest = {
        id: backupId,
        name: backupName,
        timestamp: new Date().toISOString(),
        version: '3.0.0',
        type: options.type || 'full',
        source: 'qwen-mcp-server',
        size: 0,
        checksum: '',
        files: [],
        metadata: {
          nodeVersion: process.version,
          platform: process.platform,
          hostname: os.hostname(),
          user: os.userInfo().username,
          ...options.metadata
        }
      };

      // Copiar arquivos para o diretório temporário
      const copiedFiles = await this.copyFilesToBackup(tempDir, backupData);
      manifest.files = copiedFiles;

      // Salvar manifest
      const manifestPath = path.join(tempDir, 'manifest.json');
      await writeFile(manifestPath, JSON.stringify(manifest, null, 2));

      // Criar arquivo de backup final
      const backupFileName = this.options.enableCompression
        ? `${backupName}.tar.gz`
        : `${backupName}.tar`;

      const backupPath = path.join(this.options.backupDir, backupFileName);

      if (this.options.enableCompression) {
        await this.createCompressedBackup(tempDir, backupPath);
      } else {
        await this.createTarBackup(tempDir, backupPath);
      }

      // Encriptar se habilitado
      if (this.options.enableEncryption) {
        const encryptedPath = backupPath + '.enc';
        await this.encryptFile(backupPath, encryptedPath);
        // Remover arquivo não encriptado
        await execAsync(`rm "${backupPath}"`);
        manifest.encrypted = true;
        manifest.encryptionAlgorithm = 'aes-256-gcm';
      }

      // Calcular tamanho e checksum do backup final
      const finalBackupPath = this.options.enableEncryption ? backupPath + '.enc' : backupPath;
      const stats = await stat(finalBackupPath);
      manifest.size = stats.size;
      manifest.checksum = await this.calculateChecksum(finalBackupPath);

      // Verificar tamanho máximo
      if (manifest.size > this.options.maxBackupSize) {
        logger.warn('Backup size exceeds maximum', {
          size: manifest.size,
          maxSize: this.options.maxBackupSize
        });
      }

      // Limpar diretório temporário
      await execAsync(`rm -rf "${tempDir}"`);

      // Atualizar manifest final
      const finalManifestPath = path.join(this.options.backupDir, `${backupName}-manifest.json`);
      await writeFile(finalManifestPath, JSON.stringify(manifest, null, 2));

      // Adicionar ao histórico
      this.backupHistory.push({
        ...manifest,
        path: finalBackupPath,
        duration: Date.now() - startTime,
        success: true
      });

      await this.saveBackupHistory();

      // Sync para cloud se habilitado
      if (this.options.enableCloudSync) {
        await this.syncToCloud(finalBackupPath, manifest);
      }

      logger.info('Backup completed successfully', {
        backupId,
        name: backupName,
        size: manifest.size,
        duration: Date.now() - startTime,
        files: manifest.files.length
      });

      // Limpeza de backups antigos
      await this.cleanupOldBackups();

      return manifest;

    } catch (error) {
      this.backupHistory.push({
        id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
        success: false,
        error: error.message,
        duration: Date.now() - startTime
      });

      await this.saveBackupHistory();

      logger.error('Backup failed', { error: error.message });
      throw error;

    } finally {
      this.isBackupRunning = false;
    }
  }

  async collectBackupData() {
    const dataToBackup = {
      config: [],
      data: [],
      logs: [],
      plugins: []
    };

    try {
      // Configurações
      const configFiles = [
        'auth.json',
        'webhooks.json',
        'settings.json',
        'plugins.json'
      ];

      for (const file of configFiles) {
        const filePath = path.join(this.options.dataDir, file);
        if (existsSync(filePath)) {
          dataToBackup.config.push(filePath);
        }
      }

      // Dados de métricas
      const metricsDir = path.join(this.options.dataDir, 'metrics');
      if (existsSync(metricsDir)) {
        const files = await readdir(metricsDir);
        for (const file of files) {
          const filePath = path.join(metricsDir, file);
          const stats = await stat(filePath);
          if (stats.isFile()) {
            dataToBackup.data.push(filePath);
          }
        }
      }

      // Logs recentes (últimos 7 dias)
      const logsDir = path.join(this.options.dataDir, 'logs');
      if (existsSync(logsDir)) {
        const files = await readdir(logsDir);
        const cutoffDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

        for (const file of files) {
          const filePath = path.join(logsDir, file);
          const stats = await stat(filePath);
          if (stats.isFile() && stats.mtime > cutoffDate) {
            dataToBackup.logs.push(filePath);
          }
        }
      }

      // Plugins
      const pluginsDir = path.join(this.options.dataDir, 'plugins');
      if (existsSync(pluginsDir)) {
        const entries = await readdir(pluginsDir, { withFileTypes: true });
        for (const entry of entries) {
          if (entry.isDirectory()) {
            const pluginPath = path.join(pluginsDir, entry.name);
            dataToBackup.plugins.push(pluginPath);
          }
        }
      }

      return dataToBackup;

    } catch (error) {
      logger.error('Failed to collect backup data', { error: error.message });
      throw error;
    }
  }

  async copyFilesToBackup(tempDir, backupData) {
    const copiedFiles = [];

    try {
      // Criar estrutura de diretórios
      await mkdir(path.join(tempDir, 'config'), { recursive: true });
      await mkdir(path.join(tempDir, 'data'), { recursive: true });
      await mkdir(path.join(tempDir, 'logs'), { recursive: true });
      await mkdir(path.join(tempDir, 'plugins'), { recursive: true });

      // Copiar arquivos de configuração
      for (const filePath of backupData.config) {
        const fileName = path.basename(filePath);
        const destPath = path.join(tempDir, 'config', fileName);
        await copyFile(filePath, destPath);
        copiedFiles.push({ type: 'config', source: filePath, dest: destPath });
      }

      // Copiar dados
      for (const filePath of backupData.data) {
        const fileName = path.basename(filePath);
        const destPath = path.join(tempDir, 'data', fileName);
        await copyFile(filePath, destPath);
        copiedFiles.push({ type: 'data', source: filePath, dest: destPath });
      }

      // Copiar logs
      for (const filePath of backupData.logs) {
        const fileName = path.basename(filePath);
        const destPath = path.join(tempDir, 'logs', fileName);
        await copyFile(filePath, destPath);
        copiedFiles.push({ type: 'logs', source: filePath, dest: destPath });
      }

      // Copiar plugins
      for (const pluginPath of backupData.plugins) {
        const pluginName = path.basename(pluginPath);
        const destPath = path.join(tempDir, 'plugins', pluginName);
        await execAsync(`cp -r "${pluginPath}" "${destPath}"`);
        copiedFiles.push({ type: 'plugins', source: pluginPath, dest: destPath });
      }

      return copiedFiles;

    } catch (error) {
      logger.error('Failed to copy files to backup', { error: error.message });
      throw error;
    }
  }

  async createTarBackup(sourceDir, outputPath) {
    try {
      await execAsync(`tar -cf "${outputPath}" -C "${sourceDir}" .`);
    } catch (error) {
      throw new Error(`Failed to create tar backup: ${error.message}`);
    }
  }

  async createCompressedBackup(sourceDir, outputPath) {
    try {
      await execAsync(`tar -czf "${outputPath}" -C "${sourceDir}" .`);
    } catch (error) {
      throw new Error(`Failed to create compressed backup: ${error.message}`);
    }
  }

  async encryptFile(inputPath, outputPath) {
    try {
      const key = this.options.encryptionKey || this.generateEncryptionKey();
      const algorithm = 'aes-256-gcm';
      const iv = crypto.randomBytes(16);

      const cipher = crypto.createCipher(algorithm, key);
      const input = createReadStream(inputPath);
      const output = createWriteStream(outputPath);

      await pipeline(input, cipher, output);

      // Salvar IV para descriptografia
      const ivPath = outputPath + '.iv';
      await writeFile(ivPath, iv);

    } catch (error) {
      throw new Error(`Failed to encrypt backup: ${error.message}`);
    }
  }

  async decryptFile(inputPath, outputPath) {
    try {
      const key = this.options.encryptionKey;
      if (!key) {
        throw new Error('Encryption key not provided');
      }

      const algorithm = 'aes-256-gcm';
      const ivPath = inputPath + '.iv';
      const iv = await readFile(ivPath);

      const decipher = crypto.createDecipher(algorithm, key);
      const input = createReadStream(inputPath);
      const output = createWriteStream(outputPath);

      await pipeline(input, decipher, output);

    } catch (error) {
      throw new Error(`Failed to decrypt backup: ${error.message}`);
    }
  }

  async calculateChecksum(filePath) {
    return new Promise((resolve, reject) => {
      const hash = crypto.createHash('sha256');
      const stream = createReadStream(filePath);

      stream.on('data', data => hash.update(data));
      stream.on('end', () => resolve(hash.digest('hex')));
      stream.on('error', reject);
    });
  }

  generateEncryptionKey() {
    return crypto.randomBytes(32).toString('hex');
  }

  async restoreBackup(backupId, options = {}) {
    try {
      const backup = this.backupHistory.find(b => b.id === backupId);
      if (!backup) {
        throw new Error(`Backup not found: ${backupId}`);
      }

      logger.info('Starting backup restoration', { backupId, name: backup.name });

      const backupPath = backup.path;
      const restoreDir = path.join(this.options.backupDir, 'restore', backupId);

      await mkdir(restoreDir, { recursive: true });

      // Descriptografar se necessário
      let extractPath = backupPath;
      if (backup.encrypted) {
        const decryptedPath = path.join(restoreDir, 'backup.tar.gz');
        await this.decryptFile(backupPath, decryptedPath);
        extractPath = decryptedPath;
      }

      // Extrair backup
      if (extractPath.endsWith('.tar.gz')) {
        await execAsync(`tar -xzf "${extractPath}" -C "${restoreDir}"`);
      } else {
        await execAsync(`tar -xf "${extractPath}" -C "${restoreDir}"`);
      }

      // Verificar manifest
      const manifestPath = path.join(restoreDir, 'manifest.json');
      if (!existsSync(manifestPath)) {
        throw new Error('Backup manifest not found');
      }

      const manifest = JSON.parse(await readFile(manifestPath, 'utf-8'));

      // Restaurar arquivos se confirmado
      if (options.confirm) {
        await this.performRestore(restoreDir, manifest, options);
      }

      logger.info('Backup restoration completed', { backupId });

      return {
        manifest,
        restoreDir,
        message: options.confirm ? 'Backup restored successfully' : 'Backup extracted for review'
      };

    } catch (error) {
      logger.error('Backup restoration failed', { backupId, error: error.message });
      throw error;
    }
  }

  async performRestore(restoreDir, manifest, options) {
    try {
      // Backup atual antes de restaurar
      if (!options.skipCurrentBackup) {
        await this.createBackup({ name: 'pre-restore-backup', type: 'pre-restore' });
      }

      // Restaurar configurações
      const configDir = path.join(restoreDir, 'config');
      if (existsSync(configDir)) {
        const files = await readdir(configDir);
        for (const file of files) {
          const sourcePath = path.join(configDir, file);
          const destPath = path.join(this.options.dataDir, file);
          await copyFile(sourcePath, destPath);
        }
      }

      // Restaurar dados
      const dataDir = path.join(restoreDir, 'data');
      if (existsSync(dataDir)) {
        const metricsDir = path.join(this.options.dataDir, 'metrics');
        await mkdir(metricsDir, { recursive: true });

        const files = await readdir(dataDir);
        for (const file of files) {
          const sourcePath = path.join(dataDir, file);
          const destPath = path.join(metricsDir, file);
          await copyFile(sourcePath, destPath);
        }
      }

      // Restaurar plugins se solicitado
      if (options.restorePlugins) {
        const pluginsDir = path.join(restoreDir, 'plugins');
        if (existsSync(pluginsDir)) {
          const targetPluginsDir = path.join(this.options.dataDir, 'plugins');
          await mkdir(targetPluginsDir, { recursive: true });
          await execAsync(`cp -r "${pluginsDir}"/* "${targetPluginsDir}"/`);
        }
      }

    } catch (error) {
      throw new Error(`Failed to perform restore: ${error.message}`);
    }
  }

  async cleanupOldBackups() {
    try {
      const cutoffDate = new Date(Date.now() - this.options.retentionDays * 24 * 60 * 60 * 1000);

      const backupsToDelete = this.backupHistory.filter(backup => {
        return new Date(backup.timestamp) < cutoffDate && backup.success;
      });

      for (const backup of backupsToDelete) {
        if (existsSync(backup.path)) {
          await execAsync(`rm -f "${backup.path}"`);

          // Remover manifest associado
          const manifestPath = backup.path.replace(/\.(tar\.gz|tar|enc)$/, '-manifest.json');
          if (existsSync(manifestPath)) {
            await execAsync(`rm -f "${manifestPath}"`);
          }

          logger.info('Old backup deleted', {
            id: backup.id,
            name: backup.name,
            age: Math.floor((Date.now() - new Date(backup.timestamp)) / (24 * 60 * 60 * 1000))
          });
        }
      }

      // Atualizar histórico
      this.backupHistory = this.backupHistory.filter(backup =>
        new Date(backup.timestamp) >= cutoffDate || !backup.success
      );

      await this.saveBackupHistory();

    } catch (error) {
      logger.error('Failed to cleanup old backups', { error: error.message });
    }
  }

  async syncToCloud(backupPath, manifest) {
    try {
      // Implementação futura para sync com cloud providers
      logger.info('Cloud sync skipped (not implemented)', {
        provider: this.options.cloudProvider,
        backup: manifest.name
      });
    } catch (error) {
      logger.error('Cloud sync failed', { error: error.message });
    }
  }

  listBackups() {
    return this.backupHistory
      .filter(backup => backup.success)
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .map(backup => ({
        id: backup.id,
        name: backup.name,
        timestamp: backup.timestamp,
        size: backup.size,
        type: backup.type,
        duration: backup.duration,
        files: backup.files?.length || 0,
        encrypted: backup.encrypted || false
      }));
  }

  getBackupStats() {
    const backups = this.backupHistory.filter(b => b.success);
    const totalSize = backups.reduce((sum, b) => sum + (b.size || 0), 0);
    const avgSize = backups.length > 0 ? totalSize / backups.length : 0;

    return {
      total: this.backupHistory.length,
      successful: backups.length,
      failed: this.backupHistory.filter(b => !b.success).length,
      totalSize,
      averageSize: avgSize,
      oldestBackup: backups.length > 0 ? backups[backups.length - 1].timestamp : null,
      newestBackup: backups.length > 0 ? backups[0].timestamp : null,
      isRunning: this.isBackupRunning
    };
  }
}

// Singleton instance
let backupManagerInstance = null;

export function getBackupManager(options = {}) {
  if (!backupManagerInstance) {
    backupManagerInstance = new BackupManager(options);
  }
  return backupManagerInstance;
}

export { BackupManager };

// CLI para operações de backup
if (import.meta.url === `file://${process.argv[1]}`) {
  const backupManager = getBackupManager();
  const command = process.argv[2] || 'help';

  switch (command) {
    case 'create':
      console.log('🔄 Creating backup...');
      const backup = await backupManager.createBackup({ name: process.argv[3] });
      console.log('✅ Backup created successfully:', backup.name);
      break;

    case 'list':
      console.log('📋 Available backups:');
      const backups = backupManager.listBackups();
      console.table(backups);
      break;

    case 'restore':
      const backupId = process.argv[3];
      if (!backupId) {
        console.log('❌ Please provide backup ID');
        process.exit(1);
      }
      console.log('🔄 Restoring backup...');
      const result = await backupManager.restoreBackup(backupId, { confirm: process.argv.includes('--confirm') });
      console.log('✅ Restore completed:', result.message);
      break;

    case 'stats':
      console.log('📊 Backup statistics:');
      const stats = backupManager.getBackupStats();
      console.log(JSON.stringify(stats, null, 2));
      break;

    case 'cleanup':
      console.log('🧹 Cleaning up old backups...');
      await backupManager.cleanupOldBackups();
      console.log('✅ Cleanup completed');
      break;

    default:
      console.log(`
Usage: node backup.js <command> [options]

Commands:
  create [name]     - Create a new backup
  list             - List all backups
  restore <id>     - Restore a backup (add --confirm to actually restore)
  stats            - Show backup statistics
  cleanup          - Remove old backups
  help             - Show this help
      `);
  }
}