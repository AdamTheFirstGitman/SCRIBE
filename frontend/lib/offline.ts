/**
 * Offline Storage and Sync Utilities
 * Simple offline support for your personal SCRIBE app
 */

interface PendingUpload {
  id: string;
  file: File;
  metadata: {
    title: string;
    tags: string[];
    uploadTime: string;
  };
}

interface StoredDocument {
  id: string;
  title: string;
  content: string;
  html_content: string;
  tags: string[];
  created_at: string;
  cached_at: string;
}

class OfflineStorage {
  private dbName = 'scribe-offline';
  private dbVersion = 1;
  private db: IDBDatabase | null = null;

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Store for pending uploads
        if (!db.objectStoreNames.contains('pendingUploads')) {
          const uploadsStore = db.createObjectStore('pendingUploads', { keyPath: 'id' });
          uploadsStore.createIndex('uploadTime', 'metadata.uploadTime');
        }

        // Store for cached documents
        if (!db.objectStoreNames.contains('cachedDocuments')) {
          const docsStore = db.createObjectStore('cachedDocuments', { keyPath: 'id' });
          docsStore.createIndex('title', 'title');
          docsStore.createIndex('tags', 'tags', { multiEntry: true });
        }

        // Store for chat messages
        if (!db.objectStoreNames.contains('chatMessages')) {
          const chatStore = db.createObjectStore('chatMessages', { keyPath: 'id' });
          chatStore.createIndex('timestamp', 'timestamp');
          chatStore.createIndex('agent', 'agent');
        }
      };
    });
  }

  // Pending uploads management
  async storePendingUpload(upload: PendingUpload): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['pendingUploads'], 'readwrite');
      const store = transaction.objectStore('pendingUploads');

      const request = store.add(upload);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async getPendingUploads(): Promise<PendingUpload[]> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['pendingUploads'], 'readonly');
      const store = transaction.objectStore('pendingUploads');

      const request = store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async removePendingUpload(id: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['pendingUploads'], 'readwrite');
      const store = transaction.objectStore('pendingUploads');

      const request = store.delete(id);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  // Document caching
  async cacheDocument(doc: StoredDocument): Promise<void> {
    if (!this.db) await this.init();

    const docWithCache = {
      ...doc,
      cached_at: new Date().toISOString()
    };

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['cachedDocuments'], 'readwrite');
      const store = transaction.objectStore('cachedDocuments');

      const request = store.put(docWithCache);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async getCachedDocuments(): Promise<StoredDocument[]> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['cachedDocuments'], 'readonly');
      const store = transaction.objectStore('cachedDocuments');

      const request = store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async searchCachedDocuments(query: string): Promise<StoredDocument[]> {
    const docs = await this.getCachedDocuments();

    return docs.filter(doc =>
      doc.title.toLowerCase().includes(query.toLowerCase()) ||
      doc.content.toLowerCase().includes(query.toLowerCase()) ||
      doc.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
    );
  }

  // Cleanup old cache
  async cleanupCache(daysOld: number = 7): Promise<void> {
    if (!this.db) await this.init();

    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysOld);

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['cachedDocuments'], 'readwrite');
      const store = transaction.objectStore('cachedDocuments');

      const request = store.openCursor();
      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result;
        if (cursor) {
          const doc = cursor.value;
          const cachedAt = new Date(doc.cached_at);

          if (cachedAt < cutoffDate) {
            cursor.delete();
          }
          cursor.continue();
        } else {
          resolve();
        }
      };

      request.onerror = () => reject(request.error);
    });
  }
}

// Network status utilities
export const NetworkUtils = {
  isOnline: () => navigator.onLine,

  onNetworkChange: (callback: (isOnline: boolean) => void) => {
    window.addEventListener('online', () => callback(true));
    window.addEventListener('offline', () => callback(false));
  },

  // Simple connectivity check
  async checkConnectivity(): Promise<boolean> {
    try {
      const response = await fetch('/api/health', {
        method: 'HEAD',
        cache: 'no-cache'
      });
      return response.ok;
    } catch {
      return false;
    }
  }
};

// Background sync utilities
export const BackgroundSync = {
  // Register background sync for uploads
  async registerUploadSync(): Promise<void> {
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      const registration = await navigator.serviceWorker.ready;
      if ('sync' in registration) {
        await (registration as any).sync.register('document-upload');
      }
    }
  },

  // Sync pending uploads when online
  async syncPendingUploads(): Promise<void> {
    const offlineStorage = new OfflineStorage();
    const pendingUploads = await offlineStorage.getPendingUploads();

    for (const upload of pendingUploads) {
      try {
        const formData = new FormData();
        formData.append('file', upload.file);
        formData.append('title', upload.metadata.title);
        formData.append('tags', JSON.stringify(upload.metadata.tags));

        const response = await fetch('/api/documents/upload', {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          await offlineStorage.removePendingUpload(upload.id);
          console.log(`Upload synchronisé: ${upload.metadata.title}`);
        }
      } catch (error) {
        console.log('Échec sync upload:', error);
      }
    }
  }
};

// Offline utilities for your personal app
export const OfflineUtils = {
  storage: new OfflineStorage(),
  network: NetworkUtils,
  sync: BackgroundSync,

  // Handle file upload when offline
  async handleOfflineUpload(file: File, title: string, tags: string[]): Promise<void> {
    const upload: PendingUpload = {
      id: `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      file,
      metadata: {
        title,
        tags,
        uploadTime: new Date().toISOString()
      }
    };

    await this.storage.storePendingUpload(upload);
    await this.sync.registerUploadSync();

    console.log('Fichier mis en queue pour sync:', title);
  },

  // Show offline status
  showOfflineIndicator(): void {
    const indicator = document.createElement('div');
    indicator.id = 'offline-indicator';
    indicator.innerHTML = '📴 Mode hors ligne';
    indicator.style.cssText = `
      position: fixed;
      top: 10px;
      right: 10px;
      background: #f59e0b;
      color: white;
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 14px;
      z-index: 9999;
      font-family: system-ui, -apple-system, sans-serif;
    `;

    document.body.appendChild(indicator);
  },

  hideOfflineIndicator(): void {
    const indicator = document.getElementById('offline-indicator');
    if (indicator) {
      indicator.remove();
    }
  },

  // Initialize offline support
  async init(): Promise<void> {
    await this.storage.init();

    // Handle network changes
    this.network.onNetworkChange((isOnline) => {
      if (isOnline) {
        this.hideOfflineIndicator();
        this.sync.syncPendingUploads();
      } else {
        this.showOfflineIndicator();
      }
    });

    // Initial state
    if (!this.network.isOnline()) {
      this.showOfflineIndicator();
    }

    // Cleanup old cache periodically
    setInterval(() => {
      this.storage.cleanupCache(7);
    }, 24 * 60 * 60 * 1000); // Daily
  }
};

export default OfflineUtils;