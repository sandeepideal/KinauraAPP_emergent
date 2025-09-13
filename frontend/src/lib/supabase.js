import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL
const supabaseKey = process.env.REACT_APP_SUPABASE_ANON_KEY

// Create single supabase client
export const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false
  }
})

// Helper functions for API calls
export const supabaseApi = {
  // Auth functions
  auth: {
    register: async (email, password, full_name, phone) => {
      const response = await fetch(`${supabaseUrl}/functions/v1/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${supabaseKey}`
        },
        body: JSON.stringify({ email, password, full_name, phone })
      })
      return response.json()
    },

    login: async (email, password) => {
      const response = await fetch(`${supabaseUrl}/functions/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${supabaseKey}`
        },
        body: JSON.stringify({ email, password })
      })
      return response.json()
    },

    socialLogin: async (provider, id_token, full_name, email) => {
      const response = await fetch(`${supabaseUrl}/functions/v1/auth/social-login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${supabaseKey}`
        },
        body: JSON.stringify({ provider, id_token, full_name, email })
      })
      return response.json()
    },

    getProfile: async (token) => {
      const response = await fetch(`${supabaseUrl}/functions/v1/auth/profile`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })
      return response.json()
    }
  },

  // Services functions
  services: {
    getAll: async () => {
      const response = await fetch(`${supabaseUrl}/functions/v1/booking/services`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${supabaseKey}`
        }
      })
      return response.json()
    }
  },

  // Appointments functions
  appointments: {
    getAll: async (token) => {
      const response = await fetch(`${supabaseUrl}/functions/v1/booking/appointments`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })
      return response.json()
    }
  },

  // Patient resources functions
  patientFiles: {
    getAll: async (token) => {
      const response = await fetch(`${supabaseUrl}/functions/v1/clinical/patient-files`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })
      return response.json()
    }
  },

  // Admin functions
  admin: {
    getDashboard: async (token) => {
      const response = await fetch(`${supabaseUrl}/functions/v1/admin/dashboard-overview`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })
      return response.json()
    },

    getPatients: async (token) => {
      const response = await fetch(`${supabaseUrl}/functions/v1/admin/patients`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })
      return response.json()
    },

    createPatient: async (token, patientData) => {
      const response = await fetch(`${supabaseUrl}/functions/v1/admin/patients`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(patientData)
      })
      return response.json()
    },

    getMetrics: async (token) => {
      const response = await fetch(`${supabaseUrl}/functions/v1/admin/metrics`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })
      return response.json()
    },

    getAuditLogs: async (token) => {
      const response = await fetch(`${supabaseUrl}/functions/v1/admin/audit-search`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })
      return response.json()
    },

    sendNotification: async (token, notificationData) => {
      const response = await fetch(`${supabaseUrl}/functions/v1/messaging/notifications`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(notificationData)
      })
      return response.json()
    },

    getNotificationLogs: async (token) => {
      const response = await fetch(`${supabaseUrl}/functions/v1/messaging/notifications`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })
      return response.json()
    }
  }
}