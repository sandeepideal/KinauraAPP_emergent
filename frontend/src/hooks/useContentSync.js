import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/apiClient';
import { useState, useEffect, useRef } from 'react';

// Content sync query keys
export const contentSyncKeys = {
  all: ['content-sync'],
  version: () => [...contentSyncKeys.all, 'version'],
  changes: (version) => [...contentSyncKeys.all, 'changes', version],
  servicesSync: () => [...contentSyncKeys.all, 'services-sync'],
};

// Global content version hook
export const useContentVersion = (options = {}) => {
  return useQuery({
    queryKey: contentSyncKeys.version(),
    queryFn: () => api.get('/content/version'),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Check every minute
    ...options
  });
};

// Content changes detection hook
export const useContentChanges = (currentVersion, options = {}) => {
  return useQuery({
    queryKey: contentSyncKeys.changes(currentVersion),
    queryFn: () => api.get(`/content/changes?since_version=${currentVersion || ''}`),
    enabled: !!currentVersion,
    staleTime: 0, // Always fresh
    refetchInterval: 30 * 1000, // Check every 30 seconds
    ...options
  });
};

// Enhanced services with sync info
export const useServicesSync = (lastSyncTime, options = {}) => {
  const params = lastSyncTime ? `?if_modified_since=${lastSyncTime.toISOString()}` : '';
  
  return useQuery({
    queryKey: contentSyncKeys.servicesSync(),
    queryFn: () => api.get(`/services/sync${params}`),
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
    ...options
  });
};

// Real-time content sync hook
export const useRealTimeContentSync = () => {
  const queryClient = useQueryClient();
  const [isConnected, setIsConnected] = useState(false);
  const [lastSyncTime, setLastSyncTime] = useState(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // Get current content version
  const { data: contentVersion, refetch: refetchVersion } = useContentVersion();

  // WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        // Build WebSocket URL with enhanced parameters
        const wsBaseUrl = process.env.REACT_APP_WS_URL || 
          process.env.REACT_APP_BACKEND_URL?.replace('http', 'ws');
        
        if (!wsBaseUrl) {
          console.warn('WebSocket URL not configured, falling back to polling');
          return;
        }

        // Generate connection ID
        const connectionId = `web-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        // Build query parameters for enhanced WebSocket
        const params = new URLSearchParams({
          connection_id: connectionId,
          subscribe_to: 'services,products,service_groups,knowledge_base'
        });

        const wsUrl = `${wsBaseUrl}/ws/content-sync?${params}`;
        console.log('🔗 Connecting to enhanced WebSocket:', wsUrl);

        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => {
          console.log('✅ Enhanced WebSocket connected');
          setIsConnected(true);
          
          // Clear reconnection timeout
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
          }
        };

        wsRef.current.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            console.log('📡 WebSocket message received:', message.type, message);
            
            if (message.type === 'welcome') {
              console.log('🎉 WebSocket welcome received:', message.subscriptions);
              console.log(`💓 Heartbeat interval: ${message.heartbeat_interval}s`);
              
            } else if (message.type === 'content_update') {
              console.log('📡 Content update received:', message.content_types);
              
              // Invalidate affected queries based on enhanced message
              const contentTypes = message.content_types || [];
              
              contentTypes.forEach(contentType => {
                switch (contentType) {
                  case 'services':
                    queryClient.invalidateQueries({ queryKey: ['services'] });
                    queryClient.invalidateQueries({ queryKey: contentSyncKeys.servicesSync() });
                    break;
                  case 'products':
                    queryClient.invalidateQueries({ queryKey: ['products'] });
                    queryClient.invalidateQueries({ queryKey: ['shop'] });
                    break;
                  case 'service_groups':
                    queryClient.invalidateQueries({ queryKey: ['service-groups'] });
                    break;
                  case 'knowledge_base':
                    queryClient.invalidateQueries({ queryKey: ['chatbot'] });
                    queryClient.invalidateQueries({ queryKey: ['knowledge-base'] });
                    console.log('🧠 Knowledge base updated - chatbot will use latest information');
                    break;
                }
              });

              // Update content version and sync time
              refetchVersion();
              setLastSyncTime(new Date());
              
            } else if (message.type === 'ping') {
              // Respond to ping with pong
              if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({
                  type: 'pong',
                  timestamp: new Date().toISOString()
                }));
              }
              
            } else if (message.type === 'subscription_updated') {
              console.log('📋 Subscriptions updated:', message.subscriptions);
              
            } else {
              console.log('📨 Unknown WebSocket message type:', message.type);
            }
            
          } catch (error) {
            console.error('❌ Error parsing WebSocket message:', error);
          }
        };

        wsRef.current.onclose = (event) => {
          console.log(`🔌 Enhanced WebSocket disconnected: ${event.code} - ${event.reason}`);
          setIsConnected(false);
          
          // Attempt to reconnect after delay (with exponential backoff)
          const reconnectDelay = Math.min(5000 * Math.pow(2, reconnectAttempts), 30000);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`🔄 Attempting to reconnect WebSocket (attempt ${reconnectAttempts + 1})...`);
            setReconnectAttempts(prev => prev + 1);
            connectWebSocket();
          }, reconnectDelay);
        };

        wsRef.current.onerror = (error) => {
          console.error('❌ Enhanced WebSocket error:', error);
          setIsConnected(false);
        };

      } catch (error) {
        console.error('❌ Error connecting to enhanced WebSocket:', error);
      }
    };

    // Only connect in production or if explicitly enabled
    if (process.env.NODE_ENV === 'production' || process.env.REACT_APP_ENABLE_WEBSOCKET === 'true') {
      connectWebSocket();
    } else {
      console.log('🔧 WebSocket disabled in development (set REACT_APP_ENABLE_WEBSOCKET=true to enable)');
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [queryClient, refetchVersion]);

  // Fallback: Check for changes periodically if WebSocket is not connected
  const { data: contentChanges } = useContentChanges(
    contentVersion?.global_version,
    {
      enabled: !isConnected && !!contentVersion?.global_version,
      refetchInterval: isConnected ? false : 30 * 1000, // Only poll if WebSocket is disconnected
      onSuccess: (data) => {
        if (data?.has_changes) {
          console.log('🔄 Content changes detected via polling:', data.changed_content);
          
          // Invalidate relevant queries
          Object.keys(data.changed_content).forEach(contentType => {
            switch (contentType) {
              case 'services':
                queryClient.invalidateQueries({ queryKey: ['services'] });
                queryClient.invalidateQueries({ queryKey: contentSyncKeys.servicesSync() });
                break;
              case 'products':
                queryClient.invalidateQueries({ queryKey: ['products'] });
                queryClient.invalidateQueries({ queryKey: ['shop'] });
                break;
              case 'service_groups':
                queryClient.invalidateQueries({ queryKey: ['service-groups'] });
                break;
              case 'knowledge_base':
                queryClient.invalidateQueries({ queryKey: ['chatbot'] });
                queryClient.invalidateQueries({ queryKey: ['knowledge-base'] });
                console.log('🧠 Knowledge base updated via polling - chatbot refreshed');
                break;
            }
          });
          
          setLastSyncTime(new Date());
        }
      }
    }
  );

  // Manual sync function
  const manualSync = async () => {
    console.log('🔄 Manual content sync triggered');
    
    // Force refetch content version
    await refetchVersion();
    
    // Invalidate all content-related queries
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['services'] }),
      queryClient.invalidateQueries({ queryKey: ['products'] }),
      queryClient.invalidateQueries({ queryKey: ['shop'] }),
      queryClient.invalidateQueries({ queryKey: ['service-groups'] }),
      queryClient.invalidateQueries({ queryKey: ['chatbot'] }),
      queryClient.invalidateQueries({ queryKey: ['knowledge-base'] }),
      queryClient.invalidateQueries({ queryKey: contentSyncKeys.servicesSync() }),
    ]);
    
    setLastSyncTime(new Date());
  };

  return {
    isConnected,
    lastSyncTime,
    contentVersion: contentVersion?.global_version,
    manualSync,
    hasChanges: contentChanges?.has_changes || false
  };
};

// Hook for app initialization content sync
export const useAppContentSync = () => {
  const queryClient = useQueryClient();
  const [isInitialSyncComplete, setIsInitialSyncComplete] = useState(false);

  // Check if we have cached content version in localStorage
  const getCachedVersion = () => {
    try {
      return localStorage.getItem('kinaura_content_version');
    } catch (error) {
      console.warn('Error reading cached content version:', error);
      return null;
    }
  };

  const setCachedVersion = (version) => {
    try {
      localStorage.setItem('kinaura_content_version', version);
      localStorage.setItem('kinaura_last_sync', new Date().toISOString());
    } catch (error) {
      console.warn('Error caching content version:', error);
    }
  };

  // Get current content version and compare with cached version
  const { data: contentVersion, isLoading } = useContentVersion({
    onSuccess: (data) => {
      const cachedVersion = getCachedVersion();
      const currentVersion = data?.global_version;

      if (cachedVersion && cachedVersion !== currentVersion) {
        console.log('🔄 Content version mismatch, invalidating caches');
        
        // Clear all content-related queries
        queryClient.invalidateQueries({ queryKey: ['services'] });
        queryClient.invalidateQueries({ queryKey: ['products'] });
        queryClient.invalidateQueries({ queryKey: ['shop'] });
        queryClient.invalidateQueries({ queryKey: ['service-groups'] });
        queryClient.invalidateQueries({ queryKey: ['chatbot'] });
        queryClient.invalidateQueries({ queryKey: ['knowledge-base'] });
      }

      if (currentVersion) {
        setCachedVersion(currentVersion);
      }

      setIsInitialSyncComplete(true);
    }
  });

  return {
    isInitialSyncComplete: isInitialSyncComplete && !isLoading,
    contentVersion: contentVersion?.global_version,
    lastUpdated: contentVersion?.last_updated
  };
};