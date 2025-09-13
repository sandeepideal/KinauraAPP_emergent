import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/apiClient';

// Longevity score query keys
export const longevityKeys = {
  all: ['longevity'],
  score: () => [...longevityKeys.all, 'score'],
  userScore: (userId) => [...longevityKeys.score(), userId],
  history: () => [...longevityKeys.all, 'history'],
  userHistory: (userId) => [...longevityKeys.history(), userId],
  leaderboard: () => [...longevityKeys.all, 'leaderboard'],
};

// Get user's longevity score
export const useLongevityScore = (userId, options = {}) => {
  return useQuery({
    queryKey: longevityKeys.userScore(userId),
    queryFn: () => api.get(`/patient/longevity-score`),
    enabled: !!userId,
    staleTime: 10 * 60 * 1000, // 10 minutes
    ...options
  });
};

// Get user's score history
export const useLongevityHistory = (userId, options = {}) => {
  return useQuery({
    queryKey: longevityKeys.userHistory(userId),
    queryFn: () => api.get(`/patient/longevity-score/history`),
    enabled: !!userId,
    staleTime: 15 * 60 * 1000, // 15 minutes
    ...options
  });
};

// Get leaderboard (if available)
export const useLongevityLeaderboard = (options = {}) => {
  return useQuery({
    queryKey: longevityKeys.leaderboard(),
    queryFn: () => api.get('/longevity/leaderboard'),
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options
  });
};

// Update longevity score mutation (admin only)
export const useUpdateLongevityScore = (options = {}) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userId, score, factors }) => 
      api.put(`/admin/longevity-score/${userId}`, { score, factors }),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: longevityKeys.userScore(variables.userId) });
      queryClient.invalidateQueries({ queryKey: longevityKeys.userHistory(variables.userId) });
      queryClient.invalidateQueries({ queryKey: longevityKeys.leaderboard() });
    },
    ...options
  });
};

// Recalculate longevity score mutation
export const useRecalculateScore = (options = {}) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (userId) => api.post(`/patient/longevity-score/recalculate`),
    onSuccess: (data, userId) => {
      queryClient.invalidateQueries({ queryKey: longevityKeys.userScore(userId) });
      queryClient.invalidateQueries({ queryKey: longevityKeys.userHistory(userId) });
    },
    ...options
  });
};