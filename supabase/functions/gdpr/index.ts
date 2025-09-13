import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'
import { z } from "https://deno.land/x/zod@v3.16.1/mod.ts"

const ConsentUpdateSchema = z.object({
  patient_id: z.string().uuid(),
  kind: z.enum(['privacy', 'marketing', 'data_use']),
  granted: z.boolean(),
  method: z.string().optional()
})

const DataRequestSchema = z.object({
  patient_id: z.string().uuid(),
  request_type: z.enum(['export', 'delete', 'rectify']),
  details: z.string().optional()
})

const AuditLogCreateSchema = z.object({
  action: z.string().min(1),
  entity_table: z.string().min(1),
  entity_id: z.string().uuid(),
  diff: z.record(z.any()).default({})
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
      case 'consents': {
        if (req.method === 'GET') {
          let query = supabase
            .from('consents')
            .select(`
              *,
              patient:patients(id, full_name, code, email)
            `)
            .order('updated_at', { ascending: false })

          // If user is a patient, only show their own consents
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
          } else {
            // Staff can see all consents for patients in their org
            query = query.in('patient_id', 
              supabaseAdmin
                .from('patients')
                .select('id')
                .eq('org_id', profile.org_id)
            )
          }

          const { data: consents, error } = await query

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(consents), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          const body = await req.json()
          const consentData = ConsentUpdateSchema.parse(body)

          // If user is a patient, ensure they can only update their own consents
          if (profile.role === 'member') {
            const { data: patient } = await supabase
              .from('patients')
              .select('id')
              .eq('owner_user_id', user.id)
              .single()

            if (!patient || patient.id !== consentData.patient_id) {
              return new Response('Can only update own consent records', { 
                status: 403, 
                headers: corsHeaders 
              })
            }
          }

          // Upsert consent record
          const { data: consent, error } = await supabase
            .from('consents')
            .upsert({
              ...consentData,
              granted_at: consentData.granted ? new Date().toISOString() : null
            }, {
              onConflict: 'patient_id,kind'
            })
            .select(`
              *,
              patient:patients(id, full_name, code)
            `)
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Create audit log
          await supabaseAdmin
            .from('audit_logs')
            .insert({
              actor_id: user.id,
              org_id: profile.org_id,
              action: `consent_${consentData.granted ? 'granted' : 'revoked'}`,
              entity_table: 'consents',
              entity_id: consent.id,
              diff: {
                kind: consentData.kind,
                granted: consentData.granted,
                method: consentData.method
              }
            })

          return new Response(JSON.stringify(consent), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'data-requests': {
        if (req.method === 'GET') {
          if (profile.role !== 'admin') {
            return new Response('Admin access required', { status: 403, headers: corsHeaders })
          }

          // In a real implementation, you'd have a data_requests table
          // For now, we'll return a mock response
          const mockDataRequests = [
            {
              id: '1',
              patient_id: 'mock-patient-id',
              request_type: 'export',
              status: 'pending',
              created_at: new Date().toISOString(),
              details: 'Patient requested full data export'
            }
          ]

          return new Response(JSON.stringify(mockDataRequests), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          const body = await req.json()
          const requestData = DataRequestSchema.parse(body)

          // If user is a patient, ensure they can only request their own data
          if (profile.role === 'member') {
            const { data: patient } = await supabase
              .from('patients')
              .select('id')
              .eq('owner_user_id', user.id)
              .single()

            if (!patient || patient.id !== requestData.patient_id) {
              return new Response('Can only request own data', { 
                status: 403, 
                headers: corsHeaders 
              })
            }
          }

          // Create audit log for the data request
          await supabaseAdmin
            .from('audit_logs')
            .insert({
              actor_id: user.id,
              org_id: profile.org_id,
              action: `data_request_${requestData.request_type}`,
              entity_table: 'patients',
              entity_id: requestData.patient_id,
              diff: {
                request_type: requestData.request_type,
                details: requestData.details,
                requester_role: profile.role
              }
            })

          // In a real implementation, you would:
          // 1. Create a data request record
          // 2. Trigger a background job to process the request
          // 3. Notify administrators

          return new Response(JSON.stringify({
            message: `Data ${requestData.request_type} request submitted successfully`,
            request_id: `req_${Date.now()}`,
            status: 'pending',
            estimated_completion: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'export-data': {
        if (req.method === 'POST') {
          const body = await req.json()
          const { patient_id } = body

          if (!patient_id) {
            return new Response('patient_id required', { status: 400, headers: corsHeaders })
          }

          // If user is a patient, ensure they can only export their own data
          if (profile.role === 'member') {
            const { data: patient } = await supabase
              .from('patients')
              .select('id')
              .eq('owner_user_id', user.id)
              .single()

            if (!patient || patient.id !== patient_id) {
              return new Response('Can only export own data', { 
                status: 403, 
                headers: corsHeaders 
              })
            }
          }

          // Collect all patient data across tables
          const exportData: any = {}

          // Patient basic info
          const { data: patient } = await supabaseAdmin
            .from('patients')
            .select('*')
            .eq('id', patient_id)
            .single()

          exportData.patient = patient

          // Protocols and sessions
          const { data: protocols } = await supabaseAdmin
            .from('protocols')
            .select(`
              *,
              sessions:protocol_sessions(*)
            `)
            .eq('patient_id', patient_id)

          exportData.protocols = protocols

          // Analyses
          const { data: analyses } = await supabaseAdmin
            .from('analyses')
            .select('*')
            .eq('patient_id', patient_id)

          exportData.analyses = analyses

          // Longevity scores
          const { data: scores } = await supabaseAdmin
            .from('longevity_scores')
            .select('*')
            .eq('patient_id', patient_id)

          exportData.longevity_scores = scores

          // Before/After sets
          const { data: prepostSets } = await supabaseAdmin
            .from('prepost_sets')
            .select('*')
            .eq('patient_id', patient_id)

          exportData.prepost_sets = prepostSets

          // Formulas and orders
          const { data: formulas } = await supabaseAdmin
            .from('formulas')
            .select('*')
            .eq('patient_id', patient_id)

          const { data: orders } = await supabaseAdmin
            .from('orders')
            .select('*')
            .eq('patient_id', patient_id)

          exportData.formulas = formulas
          exportData.orders = orders

          // Appointments
          const { data: appointments } = await supabaseAdmin
            .from('appointments')
            .select('*')
            .eq('patient_id', patient_id)

          exportData.appointments = appointments

          // Messages/Threads
          const { data: threads } = await supabaseAdmin
            .from('threads')
            .select(`
              *,
              messages:messages(*)
            `)
            .eq('patient_id', patient_id)

          exportData.communications = threads

          // Consents
          const { data: consents } = await supabaseAdmin
            .from('consents')
            .select('*')
            .eq('patient_id', patient_id)

          exportData.consents = consents

          // Memberships
          const { data: memberships } = await supabaseAdmin
            .from('memberships')
            .select(`
              *,
              plan:membership_plans(*)
            `)
            .eq('patient_id', patient_id)

          exportData.memberships = memberships

          // Add export metadata
          exportData.export_metadata = {
            exported_at: new Date().toISOString(),
            exported_by: user.id,
            export_type: 'full_patient_data',
            version: '1.0'
          }

          // Create audit log
          await supabaseAdmin
            .from('audit_logs')
            .insert({
              actor_id: user.id,
              org_id: profile.org_id,
              action: 'data_exported',
              entity_table: 'patients',
              entity_id: patient_id,
              diff: {
                export_type: 'full_patient_data',
                tables_included: Object.keys(exportData).filter(k => k !== 'export_metadata')
              }
            })

          return new Response(JSON.stringify(exportData), {
            headers: { 
              ...corsHeaders, 
              'Content-Type': 'application/json',
              'Content-Disposition': `attachment; filename="patient_data_${patient_id}_${Date.now()}.json"`
            }
          })
        }

        break
      }

      case 'delete-data': {
        if (req.method === 'POST') {
          if (profile.role !== 'admin') {
            return new Response('Admin access required', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const { patient_id, confirmation_code } = body

          if (!patient_id || !confirmation_code) {
            return new Response('patient_id and confirmation_code required', { 
              status: 400, 
              headers: corsHeaders 
            })
          }

          // In a real implementation, you would verify the confirmation code
          // For demo purposes, we'll just check if it's "DELETE_CONFIRMED"
          if (confirmation_code !== 'DELETE_CONFIRMED') {
            return new Response('Invalid confirmation code', { 
              status: 400, 
              headers: corsHeaders 
            })
          }

          // Soft delete patient (set deleted_at timestamp)
          const { error: deleteError } = await supabaseAdmin
            .from('patients')
            .update({ deleted_at: new Date().toISOString() })
            .eq('id', patient_id)

          if (deleteError) {
            return new Response(JSON.stringify({ error: deleteError.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Create audit log
          await supabaseAdmin
            .from('audit_logs')
            .insert({
              actor_id: user.id,
              org_id: profile.org_id,
              action: 'patient_deleted',
              entity_table: 'patients',
              entity_id: patient_id,
              diff: {
                deletion_type: 'soft_delete',
                confirmation_code_verified: true,
                initiated_by: 'admin_request'
              }
            })

          return new Response(JSON.stringify({
            message: 'Patient data deleted successfully',
            patient_id,
            deleted_at: new Date().toISOString(),
            note: 'Data has been soft-deleted and can be recovered within 30 days if needed'
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'audit-logs': {
        if (req.method === 'GET') {
          if (profile.role !== 'admin') {
            return new Response('Admin access required', { status: 403, headers: corsHeaders })
          }

          let query = supabaseAdmin
            .from('audit_logs')
            .select(`
              *,
              actor:profiles(full_name, role)
            `)
            .eq('org_id', profile.org_id)
            .order('created_at', { ascending: false })
            .limit(100)

          // Filter by entity_id if provided
          const entityId = url.searchParams.get('entity_id')
          if (entityId) {
            query = query.eq('entity_id', entityId)
          }

          // Filter by action if provided
          const action = url.searchParams.get('action')
          if (action) {
            query = query.ilike('action', `%${action}%`)
          }

          const { data: auditLogs, error } = await query

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(auditLogs), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          const body = await req.json()
          const auditData = AuditLogCreateSchema.parse(body)

          const { data: auditLog, error } = await supabaseAdmin
            .from('audit_logs')
            .insert({
              ...auditData,
              actor_id: user.id,
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

          return new Response(JSON.stringify(auditLog), {
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
    console.error('GDPR function error:', error)
    return new Response(JSON.stringify({ 
      error: error.message || 'Internal server error' 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})