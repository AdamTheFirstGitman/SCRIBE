const CACHE_NAME = 'scribe-cache-v1';
const STATIC_CACHE_NAME = 'scribe-static-v1';
const DYNAMIC_CACHE_NAME = 'scribe-dynamic-v1';

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/chat',
  '/upload',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((cacheName) =>
            cacheName !== STATIC_CACHE_NAME &&
            cacheName !== DYNAMIC_CACHE_NAME
          )
          .map((cacheName) => caches.delete(cacheName))
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip external requests
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        // Return cached version and update in background
        updateCache(request);
        return cachedResponse;
      }

      // Not in cache, fetch from network
      return fetch(request)
        .then((response) => {
          // Don't cache error responses
          if (!response || response.status !== 200) {
            return response;
          }

          // Cache successful responses
          const responseClone = response.clone();
          caches.open(DYNAMIC_CACHE_NAME)
            .then((cache) => cache.put(request, responseClone));

          return response;
        })
        .catch(() => {
          // Network failed, try to serve offline page for navigation
          if (request.mode === 'navigate') {
            return caches.match('/');
          }
        });
    })
  );
});

// Background cache update
async function updateCache(request) {
  try {
    const response = await fetch(request);
    if (response.status === 200) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, response.clone());
    }
  } catch (error) {
    // Ignore network errors in background updates
  }
}

// Handle background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'document-upload') {
    event.waitUntil(syncPendingUploads());
  } else if (event.tag === 'chat-messages') {
    event.waitUntil(syncPendingMessages());
  } else if (event.tag === 'offline-sync') {
    event.waitUntil(syncAllPendingData());
  }
});

// Sync pending uploads when back online
async function syncPendingUploads() {
  const pendingUploads = await getStoredUploads();
  console.log(`Syncing ${pendingUploads.length} pending uploads...`);

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
        await removePendingUpload(upload.id);
        console.log(`Upload synced: ${upload.metadata.title}`);

        // Notify the UI
        self.clients.matchAll().then(clients => {
          clients.forEach(client => {
            client.postMessage({
              type: 'UPLOAD_SYNCED',
              data: { title: upload.metadata.title }
            });
          });
        });
      } else {
        throw new Error(`Upload failed: ${response.status}`);
      }
    } catch (error) {
      console.log('Failed to sync upload:', upload.metadata.title, error);
    }
  }
}

// Sync pending chat messages
async function syncPendingMessages() {
  const pendingMessages = await getStoredMessages();
  console.log(`Syncing ${pendingMessages.length} pending messages...`);

  for (const message of pendingMessages) {
    try {
      const response = await fetch('/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: message.text,
          agent: message.agent
        })
      });

      if (response.ok) {
        await removePendingMessage(message.id);
        console.log(`Message synced: ${message.text.substring(0, 50)}...`);

        // Notify the UI
        self.clients.matchAll().then(clients => {
          clients.forEach(client => {
            client.postMessage({
              type: 'MESSAGE_SYNCED',
              data: { id: message.id, text: message.text }
            });
          });
        });
      } else {
        throw new Error(`Message sync failed: ${response.status}`);
      }
    } catch (error) {
      console.log('Failed to sync message:', error);
    }
  }
}

// Sync all pending data
async function syncAllPendingData() {
  await syncPendingUploads();
  await syncPendingMessages();

  // Notify UI that sync is complete
  self.clients.matchAll().then(clients => {
    clients.forEach(client => {
      client.postMessage({
        type: 'SYNC_COMPLETE',
        data: { timestamp: Date.now() }
      });
    });
  });
}

// Handle push notifications (for future use)
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'SCRIBE notification',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    tag: 'scribe-notification',
    data: {
      url: '/chat'
    }
  };

  event.waitUntil(
    self.registration.showNotification('SCRIBE', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((clientList) => {
      // Focus existing window if available
      for (let client of clientList) {
        if (client.url === event.notification.data.url && 'focus' in client) {
          return client.focus();
        }
      }

      // Open new window
      if (clients.openWindow) {
        return clients.openWindow(event.notification.data.url);
      }
    })
  );
});

// IndexedDB utilities for offline storage
function openOfflineDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('scribe-offline', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      if (!db.objectStoreNames.contains('pendingUploads')) {
        const uploadStore = db.createObjectStore('pendingUploads', { keyPath: 'id' });
        uploadStore.createIndex('timestamp', 'metadata.uploadTime');
      }

      if (!db.objectStoreNames.contains('pendingMessages')) {
        const messageStore = db.createObjectStore('pendingMessages', { keyPath: 'id' });
        messageStore.createIndex('timestamp', 'timestamp');
      }
    };
  });
}

async function getStoredUploads() {
  try {
    const db = await openOfflineDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['pendingUploads'], 'readonly');
      const store = transaction.objectStore('pendingUploads');
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.log('Failed to get stored uploads:', error);
    return [];
  }
}

async function removePendingUpload(id) {
  try {
    const db = await openOfflineDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['pendingUploads'], 'readwrite');
      const store = transaction.objectStore('pendingUploads');
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.log('Failed to remove pending upload:', error);
  }
}

async function getStoredMessages() {
  try {
    const db = await openOfflineDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['pendingMessages'], 'readonly');
      const store = transaction.objectStore('pendingMessages');
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.log('Failed to get stored messages:', error);
    return [];
  }
}

async function removePendingMessage(id) {
  try {
    const db = await openOfflineDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['pendingMessages'], 'readwrite');
      const store = transaction.objectStore('pendingMessages');
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.log('Failed to remove pending message:', error);
  }
}