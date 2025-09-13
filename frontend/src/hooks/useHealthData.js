import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/apiClient';

// Health data query keys
export const healthKeys = {
  all: ['health'],
  connections: () => [...healthKeys.all, 'connections'],
  dashboard: () => [...healthKeys.all, 'dashboard'],
  dashboardWithDays: (days) => [...healthKeys.dashboard(), { days }],
  metrics: () => [...healthKeys.all, 'metrics'],
  metric: (metric, days) => [...healthKeys.metrics(), metric, { days }],
};

// Get health connections
export const useHealthConnections = (options = {}) => {
  return useQuery({
    queryKey: healthKeys.connections(),
    queryFn: () => api.get('/patient/health/connections'),
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options
  });
};

// Get health dashboard data
export const useHealthDashboard = (days = 30, options = {}) => {
  return useQuery({
    queryKey: healthKeys.dashboardWithDays(days),
    queryFn: () => api.get(`/patient/health/dashboard?days=${days}`),
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options
  });
};

// Get specific metric data
export const useHealthMetric = (metric, days = 30, options = {}) => {
  return useQuery({
    queryKey: healthKeys.metric(metric, days),
    queryFn: () => api.get(`/patient/health/metrics/${metric}?days=${days}`),
    enabled: !!metric,
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options
  });
};

// Connect health provider mutation
export const useConnectProvider = (options = {}) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ provider, permissions, metric_categories }) => 
      api.post('/patient/health/connect', { provider, permissions, metric_categories }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: healthKeys.connections() });
      queryClient.invalidateQueries({ queryKey: healthKeys.dashboard() });
    },
    ...options
  });
};

// Disconnect health provider mutation
export const useDisconnectProvider = (options = {}) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (provider) => api.delete(`/patient/health/connections/${provider}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: healthKeys.all });
    },
    onMutate: async (provider) => {
      // Optimistic update
      await queryClient.cancelQueries({ queryKey: healthKeys.connections() });
      const previousConnections = queryClient.getQueryData(healthKeys.connections());
      
      queryClient.setQueryData(healthKeys.connections(), (old) => ({
        ...old,
        connections: old?.connections?.filter(conn => conn.provider !== provider) || []
      }));
      
      return { previousConnections };
    },
    onError: (err, provider, context) => {
      // Rollback on error
      if (context?.previousConnections) {
        queryClient.setQueryData(healthKeys.connections(), context.previousConnections);
      }
    },
    ...options
  });
};

// Export health data mutation
export const useExportHealthData = (options = {}) => {
  return useMutation({
    mutationFn: ({ format, date_from, date_to }) => 
      api.post('/patient/health/export', { format, date_from, date_to }),
    ...options
  });
};