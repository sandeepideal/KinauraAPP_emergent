import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/apiClient';
import { useAppContentSync } from './useContentSync';

// Services query keys
export const servicesKeys = {
  all: ['services'],
  lists: () => [...servicesKeys.all, 'list'],
  list: (filters) => [...servicesKeys.lists(), { filters }],
  details: () => [...servicesKeys.all, 'detail'],
  detail: (id) => [...servicesKeys.details(), id],
  sync: () => [...servicesKeys.all, 'sync'],
};

// Get all services with enhanced caching for native apps
export const useServices = (options = {}) => {
  const { isInitialSyncComplete } = useAppContentSync();
  
  return useQuery({
    queryKey: servicesKeys.lists(),
    queryFn: () => api.get('/services'),
    staleTime: 2 * 60 * 1000, // Reduced from 10 minutes to 2 minutes for faster updates
    cacheTime: 30 * 60 * 1000, // 30 minutes cache time
    enabled: isInitialSyncComplete, // Wait for initial sync to complete
    refetchOnWindowFocus: true, // Refetch when app gains focus (important for mobile)
    refetchOnReconnect: true, // Refetch when connection is restored
    ...options
  });
};

// Get services with sync metadata (for native apps)
export const useServicesWithSync = (options = {}) => {
  const { lastUpdated } = useAppContentSync();
  
  return useQuery({
    queryKey: servicesKeys.sync(),
    queryFn: () => {
      const params = lastUpdated ? `?if_modified_since=${lastUpdated}` : '';
      return api.get(`/services/sync${params}`);
    },
    staleTime: 60 * 1000, // 1 minute
    cacheTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: 5 * 60 * 1000, // Check for updates every 5 minutes
    ...options
  });
};

// Get service by ID
export const useService = (serviceId, options = {}) => {
  const { isInitialSyncComplete } = useAppContentSync();
  
  return useQuery({
    queryKey: servicesKeys.detail(serviceId),
    queryFn: () => api.get(`/services/${serviceId}`),
    enabled: !!serviceId && isInitialSyncComplete,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 15 * 60 * 1000, // 15 minutes
    ...options
  });
};

// Create service mutation (admin only)
export const useCreateService = (options = {}) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (serviceData) => api.post('/admin/services', serviceData),
    onSuccess: () => {
      // Invalidate all service-related queries
      queryClient.invalidateQueries({ queryKey: servicesKeys.all });
      
      // Also invalidate content sync queries to trigger immediate updates
      queryClient.invalidateQueries({ queryKey: ['content-sync'] });
    },
    ...options
  });
};

// Update service mutation (admin only)
export const useUpdateService = (options = {}) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, ...updateData }) => api.put(`/admin/services/${id}`, updateData),
    onSuccess: (data, variables) => {
      // Invalidate all service-related queries
      queryClient.invalidateQueries({ queryKey: servicesKeys.all });
      
      // Update specific service cache
      queryClient.setQueryData(servicesKeys.detail(variables.id), data);
      
      // Invalidate content sync to trigger native app updates
      queryClient.invalidateQueries({ queryKey: ['content-sync'] });
      
      console.log('✅ Service updated, content sync triggered');
    },
    ...options
  });
};

// Delete service mutation (admin only)
export const useDeleteService = (options = {}) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (serviceId) => api.delete(`/admin/services/${serviceId}`),
    onSuccess: (_, serviceId) => {
      // Invalidate all service-related queries
      queryClient.invalidateQueries({ queryKey: servicesKeys.all });
      
      // Remove specific service from cache
      queryClient.removeQueries({ queryKey: servicesKeys.detail(serviceId) });
      
      // Invalidate content sync to trigger native app updates
      queryClient.invalidateQueries({ queryKey: ['content-sync'] });
      
      console.log('✅ Service deleted, content sync triggered');
    },
    ...options
  });
};