import React, { createContext, useContext, useEffect, useState } from 'react';
import { useRealTimeContentSync, useAppContentSync } from '../hooks/useContentSync';

const ContentSyncContext = createContext({});

export const ContentSyncProvider = ({ children }) => {
  const [syncStatus, setSyncStatus] = useState('initializing');
  const [lastSyncTime, setLastSyncTime] = useState(null);
  
  // Initialize app content sync
  const { isInitialSyncComplete, contentVersion } = useAppContentSync();
  
  // Real-time content sync
  const realTimeSync = useRealTimeContentSync();

  // Update sync status based on connection and sync state
  useEffect(() => {
    if (!isInitialSyncComplete) {
      setSyncStatus('initializing');
    } else if (realTimeSync.isConnected) {
      setSyncStatus('connected');
    } else {
      setSyncStatus('polling');
    }
  }, [isInitialSyncComplete, realTimeSync.isConnected]);

  // Update last sync time
  useEffect(() => {
    if (realTimeSync.lastSyncTime) {
      setLastSyncTime(realTimeSync.lastSyncTime);
    }
  }, [realTimeSync.lastSyncTime]);

  const contextValue = {
    // Sync status
    syncStatus,
    isInitialSyncComplete,
    isConnected: realTimeSync.isConnected,
    lastSyncTime,
    contentVersion,
    
    // Manual sync function
    manualSync: realTimeSync.manualSync,
    
    // Sync notifications
    hasChanges: realTimeSync.hasChanges,
  };

  return (
    <ContentSyncContext.Provider value={contextValue}>
      {children}
    </ContentSyncContext.Provider>
  );
};

export const useContentSyncStatus = () => {
  const context = useContext(ContentSyncContext);
  if (!context) {
    throw new Error('useContentSyncStatus must be used within a ContentSyncProvider');
  }
  return context;
};

// Content sync status indicator component
export const ContentSyncIndicator = ({ className = '' }) => {
  const { syncStatus, isConnected, lastSyncTime, hasChanges } = useContentSyncStatus();

  const getStatusIcon = () => {
    switch (syncStatus) {
      case 'initializing':
        return '🔄';
      case 'connected':
        return '🟢';
      case 'polling':
        return '🟡';
      default:
        return '🔴';
    }
  };

  const getStatusText = () => {
    switch (syncStatus) {
      case 'initializing':
        return 'Syncing content...';
      case 'connected':
        return 'Live updates';
      case 'polling':
        return 'Checking for updates';
      default:
        return 'Offline';
    }
  };

  if (process.env.NODE_ENV !== 'development') {
    return null; // Hide in production
  }

  return (
    <div className={`content-sync-indicator ${className}`}>
      <span className="sync-icon">{getStatusIcon()}</span>
      <span className="sync-text">{getStatusText()}</span>
      {lastSyncTime && (
        <span className="sync-time">
          {new Date(lastSyncTime).toLocaleTimeString()}
        </span>
      )}
      {hasChanges && (
        <span className="sync-changes">📢</span>
      )}
    </div>
  );
};