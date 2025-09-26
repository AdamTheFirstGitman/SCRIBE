'use client';

import React, { useState, useEffect } from 'react';
import { OfflineUtils } from '../lib/offline';

interface OfflineStatusProps {
  className?: string;
}

interface OfflineState {
  isOnline: boolean;
  pendingUploads: number;
  pendingMessages: number;
  lastSync: number | null;
  syncing: boolean;
}

export default function OfflineStatus({ className = '' }: OfflineStatusProps) {
  const [state, setState] = useState<OfflineState>({
    isOnline: true, // SSR-safe default
    pendingUploads: 0,
    pendingMessages: 0,
    lastSync: null,
    syncing: false
  });

  useEffect(() => {
    let mounted = true;

    // Set initial navigator value (client-side only)
    setState(prev => ({
      ...prev,
      isOnline: navigator.onLine
    }));

    // Initialize offline utils
    OfflineUtils.init().then(async () => {
      if (!mounted) return;

      // Get initial pending counts
      const pendingUploads = await OfflineUtils.storage.getPendingUploads();
      setState(prev => ({
        ...prev,
        pendingUploads: pendingUploads.length
      }));
    });

    // Handle network status changes
    const handleOnline = () => {
      if (mounted) {
        setState(prev => ({ ...prev, isOnline: true, syncing: true }));
      }
    };

    const handleOffline = () => {
      if (mounted) {
        setState(prev => ({ ...prev, isOnline: false, syncing: false }));
      }
    };

    // Handle service worker messages
    const handleSWMessage = (event: MessageEvent) => {
      if (!mounted) return;

      switch (event.data.type) {
        case 'UPLOAD_SYNCED':
          setState(prev => ({
            ...prev,
            pendingUploads: Math.max(0, prev.pendingUploads - 1)
          }));
          break;

        case 'MESSAGE_SYNCED':
          setState(prev => ({
            ...prev,
            pendingMessages: Math.max(0, prev.pendingMessages - 1)
          }));
          break;

        case 'SYNC_COMPLETE':
          setState(prev => ({
            ...prev,
            syncing: false,
            lastSync: event.data.data.timestamp,
            pendingUploads: 0,
            pendingMessages: 0
          }));
          break;
      }
    };

    // Update pending counts periodically
    const updatePendingCounts = async () => {
      if (!mounted) return;

      try {
        const pendingUploads = await OfflineUtils.storage.getPendingUploads();
        setState(prev => ({
          ...prev,
          pendingUploads: pendingUploads.length
        }));
      } catch (error) {
        console.log('Failed to update pending counts:', error);
      }
    };

    // Event listeners
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    navigator.serviceWorker?.addEventListener('message', handleSWMessage);

    // Update counts every 30 seconds
    const interval = setInterval(updatePendingCounts, 30000);

    return () => {
      mounted = false;
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      navigator.serviceWorker?.removeEventListener('message', handleSWMessage);
      clearInterval(interval);
    };
  }, []);

  // Don't show anything if online and no pending items
  if (state.isOnline && state.pendingUploads === 0 && state.pendingMessages === 0) {
    return null;
  }

  const getStatusIcon = () => {
    if (state.syncing) return '🔄';
    if (!state.isOnline) return '📴';
    if (state.pendingUploads > 0 || state.pendingMessages > 0) return '⏳';
    return '✅';
  };

  const getStatusText = () => {
    if (state.syncing) return 'Synchronisation...';
    if (!state.isOnline) return 'Mode hors ligne';
    if (state.pendingUploads > 0 || state.pendingMessages > 0) {
      const total = state.pendingUploads + state.pendingMessages;
      return `${total} en attente`;
    }
    return 'Synchronisé';
  };

  const getStatusColor = () => {
    if (state.syncing) return 'bg-blue-500';
    if (!state.isOnline) return 'bg-yellow-500';
    if (state.pendingUploads > 0 || state.pendingMessages > 0) return 'bg-orange-500';
    return 'bg-green-500';
  };

  const handleManualSync = async () => {
    if (!state.isOnline || state.syncing) return;

    setState(prev => ({ ...prev, syncing: true }));

    try {
      await OfflineUtils.sync.syncPendingUploads();
      setState(prev => ({
        ...prev,
        syncing: false,
        lastSync: Date.now(),
        pendingUploads: 0,
        pendingMessages: 0
      }));
    } catch (error) {
      console.log('Manual sync failed:', error);
      setState(prev => ({ ...prev, syncing: false }));
    }
  };

  return (
    <div className={`fixed top-4 right-4 z-50 ${className}`}>
      <div className={`
        ${getStatusColor()} text-white px-3 py-2 rounded-lg shadow-lg
        flex items-center space-x-2 text-sm font-medium
        transition-all duration-300 hover:shadow-xl
      `}>
        <span className={`text-lg ${state.syncing ? 'animate-spin' : ''}`}>
          {getStatusIcon()}
        </span>
        <span>{getStatusText()}</span>

        {/* Manual sync button when online and has pending items */}
        {state.isOnline && (state.pendingUploads > 0 || state.pendingMessages > 0) && !state.syncing && (
          <button
            onClick={handleManualSync}
            className="ml-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded px-2 py-1 text-xs transition-colors"
          >
            Sync
          </button>
        )}
      </div>

      {/* Detailed status tooltip */}
      {(state.pendingUploads > 0 || state.pendingMessages > 0) && (
        <div className="mt-2 bg-gray-800 text-white px-3 py-2 rounded-lg text-xs shadow-lg">
          {state.pendingUploads > 0 && (
            <div>📄 {state.pendingUploads} documents en attente</div>
          )}
          {state.pendingMessages > 0 && (
            <div>💬 {state.pendingMessages} messages en attente</div>
          )}
          {state.lastSync && (
            <div className="text-gray-400 mt-1">
              Dernière sync: {new Date(state.lastSync).toLocaleTimeString()}
            </div>
          )}
        </div>
      )}
    </div>
  );
}