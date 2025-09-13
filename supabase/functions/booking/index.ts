import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'
import { z } from "https://deno.land/x/zod@v3.16.1/mod.ts"

const ServiceCreateSchema = z.object({
  name: z.string().min(1),
  category: z.enum(['aesthetics', 'regenerative', 'iv_therapy', 'skincare', 'other']),
  description: z.string().min(1),
  duration_min: z.number().min(1).default(60),
  base_price_cents: z.number().min(0).default(0),
  is_active: z.boolean().default(true)
})

const ServiceUpdateSchema = z.object({
  name: z.string().optional(),
  category: z.enum(['aesthetics', 'regenerative', 'iv_therapy', 'skincare', 'other']).optional(),
  description: z.string().optional(),
  duration_min: z.number().min(1).optional(),
  base_price_cents: z.number().min(0).optional(),
  is_active: z.boolean().optional()
})

const AppointmentCreateSchema = z.object({
  patient_id: z.string().uuid(),
  service_id: z.string().uuid(),
  starts_at: z.string(), // ISO string
  ends_at: z.string().optional(), // ISO string
  practitioner_id: z.string().uuid().optional(),
  notes: z.string().optional()
})

const AppointmentUpdateSchema = z.object({
  starts_at: z.string().optional(),
  ends_at: z.string().optional(),
  practitioner_id: z.string().uuid().optional(),
  status: z.enum(['scheduled', 'confirmed', 'rescheduled', 'completed', 'no_show', 'canceled']).optional(),
  notes: z.string().optional()
})

const AvailabilityQuerySchema = z.object({
  service_id: z.string().uuid().optional(),
  practitioner_id: z.string().uuid().optional(),
  date_from: z.string(), // ISO date
  date_to: z.string().optional(), // ISO date
})

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const authHeader = req.headers.get('Authorization')!
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      {
        global: {
          headers: { Authorization: authHeader }
        }
      }
    )

    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const url = new URL(req.url)
    const pathParts = url.pathname.split('/')
    const resource = pathParts[pathParts.length - 2] || pathParts[pathParts.length - 1]
    const id = pathParts[pathParts.length - 1]

    const { data: { user } } = await supabase.auth.getUser()
    if (!user) {
      return new Response('Unauthorized', { status: 401, headers: corsHeaders })
    }

    const { data: profile } = await supabase
      .from('profiles')
      .select('role, org_id')
      .eq('id', user.id)
      .single()

    if (!profile) {
      return new Response('Profile not found', { status: 404, headers: corsHeaders })
    }

    switch (resource) {
      case 'services': {
        if (req.method === 'GET') {
          const { data: services, error } = await supabase
            .from('services')
            .select('*')
            .eq('org_id', profile.org_id)
            .eq('is_active', true)
            .order('name')

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Convert price from cents to euros for frontend
          const servicesWithPrice = services.map(service => ({
            ...service,
            price: service.base_price_cents / 100,
            duration: service.duration_min
          }))

          return new Response(JSON.stringify(servicesWithPrice), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          if (!['admin', 'practitioner'].includes(profile.role)) {
            return new Response('Insufficient permissions', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const serviceData = ServiceCreateSchema.parse(body)

          const { data: service, error } = await supabase
            .from('services')
            .insert({
              ...serviceData,
              org_id: profile.org_id
            })
            .select()
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({
            ...service,
            price: service.base_price_cents / 100,
            duration: service.duration_min
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'service': {
        if (!id || id === 'service') {
          return new Response('Service ID required', { status: 400, headers: corsHeaders })
        }

        if (req.method === 'GET') {
          const { data: service, error } = await supabase
            .from('services')
            .select('*')
            .eq('id', id)
            .eq('org_id', profile.org_id)
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({
            ...service,
            price: service.base_price_cents / 100,
            duration: service.duration_min
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'PUT') {
          if (!['admin', 'practitioner'].includes(profile.role)) {
            return new Response('Insufficient permissions', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const updateData = ServiceUpdateSchema.parse(body)

          const { data: service, error } = await supabase
            .from('services')
            .update(updateData)
            .eq('id', id)
            .eq('org_id', profile.org_id)
            .select()
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({
            ...service,
            price: service.base_price_cents / 100,
            duration: service.duration_min
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'appointments': {
        if (req.method === 'GET') {
          let query = supabase
            .from('appointments')
            .select(`
              *,
              service:services(name, duration_min, base_price_cents),
              patient:patients(full_name, code, email),
              practitioner:clinicians(name, specialization)
            `)
            .eq('org_id', profile.org_id)
            .order('starts_at', { ascending: true })

          // If user is a patient, only show their own appointments
          if (profile.role === 'member') {
            const { data: patient } = await supabase
              .from('patients')
              .select('id')
              .eq('owner_user_id', user.id)
              .single()

            if (patient) {
              query = query.eq('patient_id', patient.id)
            } else {
              return new Response(JSON.stringify([]), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
              })
            }
          }

          // Filter by date range if provided
          const dateFrom = url.searchParams.get('date_from')
          const dateTo = url.searchParams.get('date_to')
          
          if (dateFrom) {
            query = query.gte('starts_at', dateFrom)
          }
          if (dateTo) {
            query = query.lte('starts_at', dateTo)
          }

          const { data: appointments, error } = await query

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Format appointments for frontend compatibility
          const formattedAppointments = appointments.map(apt => ({
            ...apt,
            service_name: apt.service?.name,
            patient_name: apt.patient?.full_name,
            practitioner_name: apt.practitioner?.name,
            duration: apt.service?.duration_min,
            price: apt.service?.base_price_cents ? apt.service.base_price_cents / 100 : 0
          }))

          return new Response(JSON.stringify(formattedAppointments), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          const body = await req.json()
          const appointmentData = AppointmentCreateSchema.parse(body)

          // If user is a patient, ensure they can only book for themselves
          if (profile.role === 'member') {
            const { data: patient } = await supabase
              .from('patients')
              .select('id')
              .eq('owner_user_id', user.id)
              .single()

            if (!patient || patient.id !== appointmentData.patient_id) {
              return new Response('Can only book appointments for own patient record', { 
                status: 403, 
                headers: corsHeaders 
              })
            }
          }

          // Get service to calculate end time if not provided
          const { data: service } = await supabase
            .from('services')
            .select('duration_min')
            .eq('id', appointmentData.service_id)
            .single()

          const startTime = new Date(appointmentData.starts_at)
          const endTime = appointmentData.ends_at ? 
            new Date(appointmentData.ends_at) : 
            new Date(startTime.getTime() + (service?.duration_min || 60) * 60000)

          const { data: appointment, error } = await supabase
            .from('appointments')
            .insert({
              ...appointmentData,
              org_id: profile.org_id,
              starts_at: startTime.toISOString(),
              ends_at: endTime.toISOString(),
              status: 'scheduled'
            })
            .select(`
              *,
              service:services(name, duration_min, base_price_cents),
              patient:patients(full_name, code, email)
            `)
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({
            ...appointment,
            service_name: appointment.service?.name,
            patient_name: appointment.patient?.full_name,
            duration: appointment.service?.duration_min,
            price: appointment.service?.base_price_cents ? appointment.service.base_price_cents / 100 : 0
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'appointment': {
        if (!id || id === 'appointment') {
          return new Response('Appointment ID required', { status: 400, headers: corsHeaders })
        }

        if (req.method === 'GET') {
          const { data: appointment, error } = await supabase
            .from('appointments')
            .select(`
              *,
              service:services(name, duration_min, base_price_cents),
              patient:patients(full_name, code, email),
              practitioner:clinicians(name, specialization)
            `)
            .eq('id', id)
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({
            ...appointment,
            service_name: appointment.service?.name,
            patient_name: appointment.patient?.full_name,
            practitioner_name: appointment.practitioner?.name,
            duration: appointment.service?.duration_min,
            price: appointment.service?.base_price_cents ? appointment.service.base_price_cents / 100 : 0
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'PUT') {
          if (profile.role === 'member') {
            return new Response('Insufficient permissions', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const updateData = AppointmentUpdateSchema.parse(body)

          const { data: appointment, error } = await supabase
            .from('appointments')
            .update(updateData)
            .eq('id', id)
            .eq('org_id', profile.org_id)
            .select(`
              *,
              service:services(name, duration_min, base_price_cents),
              patient:patients(full_name, code, email)
            `)
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({
            ...appointment,
            service_name: appointment.service?.name,
            patient_name: appointment.patient?.full_name,
            duration: appointment.service?.duration_min,
            price: appointment.service?.base_price_cents ? appointment.service.base_price_cents / 100 : 0
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'availability': {
        if (req.method === 'GET') {
          const query = AvailabilityQuerySchema.parse({
            service_id: url.searchParams.get('service_id'),
            practitioner_id: url.searchParams.get('practitioner_id'),
            date_from: url.searchParams.get('date_from') || new Date().toISOString().split('T')[0],
            date_to: url.searchParams.get('date_to')
          })

          const dateFrom = new Date(query.date_from)
          const dateTo = query.date_to ? new Date(query.date_to) : new Date(dateFrom.getTime() + 7 * 24 * 60 * 60 * 1000)

          // Get existing appointments in the date range
          let appointmentQuery = supabase
            .from('appointments')
            .select('starts_at, ends_at, practitioner_id')
            .eq('org_id', profile.org_id)
            .in('status', ['scheduled', 'confirmed'])
            .gte('starts_at', dateFrom.toISOString())
            .lte('starts_at', dateTo.toISOString())

          if (query.practitioner_id) {
            appointmentQuery = appointmentQuery.eq('practitioner_id', query.practitioner_id)
          }

          const { data: appointments } = await appointmentQuery || []

          // Get service duration if specified
          let serviceDuration = 60
          if (query.service_id) {
            const { data: service } = await supabase
              .from('services')
              .select('duration_min')
              .eq('id', query.service_id)
              .single()
            
            serviceDuration = service?.duration_min || 60
          }

          // Generate available time slots
          const availableSlots = []
          const businessHours = { start: 9, end: 18 } // 9 AM to 6 PM
          
          for (let d = new Date(dateFrom); d <= dateTo; d.setDate(d.getDate() + 1)) {
            // Skip weekends for simplicity
            if (d.getDay() === 0 || d.getDay() === 6) continue

            for (let hour = businessHours.start; hour < businessHours.end; hour++) {
              const slotStart = new Date(d)
              slotStart.setHours(hour, 0, 0, 0)
              
              const slotEnd = new Date(slotStart.getTime() + serviceDuration * 60000)

              // Check if this slot conflicts with existing appointments
              const hasConflict = appointments?.some(apt => {
                const aptStart = new Date(apt.starts_at)
                const aptEnd = new Date(apt.ends_at)
                return (slotStart < aptEnd && slotEnd > aptStart)
              })

              if (!hasConflict) {
                availableSlots.push({
                  start: slotStart.toISOString(),
                  end: slotEnd.toISOString(),
                  duration: serviceDuration
                })
              }
            }
          }

          return new Response(JSON.stringify(availableSlots), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'clinicians': {
        if (req.method === 'GET') {
          const { data: clinicians, error } = await supabase
            .from('clinicians')
            .select('*')
            .eq('org_id', profile.org_id)
            .eq('is_active', true)
            .order('name')

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(clinicians), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      default:
        return new Response('Not found', { status: 404, headers: corsHeaders })
    }

    return new Response('Method not allowed', { status: 405, headers: corsHeaders })

  } catch (error) {
    console.error('Booking function error:', error)
    return new Response(JSON.stringify({ 
      error: error.message || 'Internal server error' 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})