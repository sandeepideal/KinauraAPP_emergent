import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/apiClient';

// Appointments query keys
export const appointmentsKeys = {
  all: ['appointments'],
  lists: () => [...appointmentsKeys.all, 'list'],
  list: (filters) => [...appointmentsKeys.lists(), { filters }],
  details: () => [...appointmentsKeys.all, 'detail'],
  detail: (id) => [...appointmentsKeys.details(), id],
  availability: () => [...appointmentsKeys.all, 'availability'],
  availabilityForService: (serviceId, date) => [...appointmentsKeys.availability(), serviceId, date],
};

// Get patient appointments
export const useAppointments = (userId, options = {}) => {
  return useQuery({
    queryKey: appointmentsKeys.list({ userId }),
    queryFn: () => api.get(`/patient/appointments`),
    enabled: !!userId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options
  });
};

// Get appointment availability
export const useAvailability = (serviceId, date, options = {}) => {
  return useQuery({
    queryKey: appointmentsKeys.availabilityForService(serviceId, date),
    queryFn: () => api.get(`/appointments/availability?service_id=${serviceId}&date=${date}`),
    enabled: !!(serviceId && date),
    staleTime: 30 * 1000, // 30 seconds - availability changes frequently
    ...options
  });
};

// Book appointment mutation
export const useBookAppointment = (options = {}) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (appointmentData) => api.post('/patient/appointments', appointmentData),
    onSuccess: (data, variables) => {
      // Invalidate appointments list
      queryClient.invalidateQueries({ queryKey: appointmentsKeys.lists() });
      
      // Invalidate availability for the booked service and date
      queryClient.invalidateQueries({ 
        queryKey: appointmentsKeys.availability()
      });
      
      // Add optimistic update
      const userId = variables.user_id;
      if (userId) {
        queryClient.setQueryData(
          appointmentsKeys.list({ userId }),
          (oldData) => oldData ? [...oldData, data] : [data]
        );
      }
    },
    ...options
  });
};

// Cancel appointment mutation
export const useCancelAppointment = (options = {}) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (appointmentId) => api.delete(`/patient/appointments/${appointmentId}`),
    onSuccess: (_, appointmentId) => {
      queryClient.invalidateQueries({ queryKey: appointmentsKeys.all });
    },
    onMutate: async (appointmentId) => {
      // Optimistic update
      const userId = options.userId;
      if (userId) {
        const queryKey = appointmentsKeys.list({ userId });
        await queryClient.cancelQueries({ queryKey });
        
        const previousAppointments = queryClient.getQueryData(queryKey);
        
        queryClient.setQueryData(queryKey, (old) => 
          old ? old.filter(apt => apt.id !== appointmentId) : []
        );
        
        return { previousAppointments };
      }
    },
    onError: (err, appointmentId, context) => {
      // Rollback on error
      if (context?.previousAppointments && options.userId) {
        queryClient.setQueryData(
          appointmentsKeys.list({ userId: options.userId }),
          context.previousAppointments
        );
      }
    },
    ...options
  });
};

// Reschedule appointment mutation
export const useRescheduleAppointment = (options = {}) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ appointmentId, newDateTime }) => 
      api.put(`/patient/appointments/${appointmentId}`, { appointment_date: newDateTime }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: appointmentsKeys.all });
      queryClient.invalidateQueries({ queryKey: appointmentsKeys.availability() });
    },
    ...options
  });
};