import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'
import { z } from "https://deno.land/x/zod@v3.16.1/mod.ts"

const CreatePatientSchema = z.object({
  full_name: z.string().min(1),
  email: z.string().email().optional(),
  phone: z.string().optional(),
  dob: z.string().optional(),
  gender: z.enum(['male', 'female', 'other', 'prefer_not_to_say']).optional(),
  country: z.string().default('IT'),
  tags: z.array(z.string()).default([])
})

const UpdatePatientSchema = z.object({
  full_name: z.string().min(1).optional(),
  email: z.string().email().optional(),
  phone: z.string().optional(),
  dob: z.string().optional(),
  gender: z.enum(['male', 'female', 'other', 'prefer_not_to_say']).optional(),
  country: z.string().optional(),
  tags: z.array(z.string()).optional(),
  notes_summary: z.string().optional()
})

const AddNoteSchema = z.object({
  content: z.string().min(1),
  visibility: z.enum(['internal', 'practitioner_only']).default('practitioner_only'),
  attachments: z.array(z.object({
    name: z.string(),
    url: z.string(),
    type: z.string()
  })).default([])
})

const UploadRequestSchema = z.object({
  filename: z.string(),
  content_type: z.string(),
  folder: z.enum(['images', 'docs']).default('docs')
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

    // Service role client for privileged operations
    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const url = new URL(req.url)
    const segments = url.pathname.split('/').filter(Boolean)
    const patientId = segments[1] // /patients/{id}
    const action = segments[2] // /patients/{id}/{action}

    // Get current user
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

    switch (req.method) {
      case 'POST': {
        if (patientId && action === 'notes') {
          // Add note to patient
          const body = await req.json()
          const { content, visibility, attachments } = AddNoteSchema.parse(body)

          const { data: note, error } = await supabase
            .from('patient_notes')
            .insert({
              patient_id: patientId,
              author_id: user.id,
              content,
              visibility,
              attachments
            })
            .select()
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Log the action
          await supabaseAdmin
            .from('audit_logs')
            .insert({
              actor_id: user.id,
              org_id: profile.org_id,
              action: 'create_patient_note',
              entity_table: 'patient_notes',
              entity_id: note.id,
              diff: { patient_id: patientId, visibility }
            })

          return new Response(JSON.stringify(note), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (patientId && action === 'upload') {
          // Generate pre-signed URL for file upload
          const body = await req.json()
          const { filename, content_type, folder } = UploadRequestSchema.parse(body)

          const bucket = folder === 'images' ? 'patient-images' : 'patient-docs'
          const filePath = `${patientId}/${Date.now()}-${filename}`

          const { data, error } = await supabaseAdmin.storage
            .from(bucket)
            .createSignedUploadUrl(filePath, {
              upsert: true
            })

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({
            upload_url: data.signedUrl,
            file_path: filePath,
            bucket
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (!patientId) {
          // Create new patient
          const body = await req.json()
          const patientData = CreatePatientSchema.parse(body)

          // Generate patient code
          const patientCode = `KA-${Date.now().toString().slice(-6)}`

          const { data: patient, error } = await supabase
            .from('patients')
            .insert({
              ...patientData,
              code: patientCode,
              org_id: profile.org_id,
              owner_user_id: user.id
            })
            .select()
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Log the action
          await supabaseAdmin
            .from('audit_logs')
            .insert({
              actor_id: user.id,
              org_id: profile.org_id,
              action: 'create_patient',
              entity_table: 'patients',
              entity_id: patient.id,
              diff: { code: patientCode, email: patientData.email }
            })

          return new Response(JSON.stringify(patient), {
            status: 201,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response('Bad request', { status: 400, headers: corsHeaders })
      }

      case 'GET': {
        if (patientId) {
          // Get specific patient
          const { data: patient, error } = await supabase
            .from('patients')
            .select(`
              *,
              memberships:memberships(
                *,
                plan:membership_plans(*)
              ),
              protocols:protocols(
                *,
                sessions:protocol_sessions(*)
              ),
              longevity_scores:longevity_scores(*)
            `)
            .eq('id', patientId)
            .is('deleted_at', null)
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 404,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(patient), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // List patients with filtering
        const searchParams = url.searchParams
        const page = parseInt(searchParams.get('page') || '1')
        const limit = Math.min(parseInt(searchParams.get('limit') || '20'), 100)
        const search = searchParams.get('search')
        const tags = searchParams.get('tags')?.split(',')

        let query = supabase
          .from('patients')
          .select('*, memberships:memberships!inner(*, plan:membership_plans(*))', { count: 'exact' })
          .is('deleted_at', null)
          .order('created_at', { ascending: false })
          .range((page - 1) * limit, page * limit - 1)

        if (search) {
          query = query.or(`full_name.ilike.%${search}%,email.ilike.%${search}%,code.ilike.%${search}%`)
        }

        if (tags && tags.length > 0) {
          query = query.overlaps('tags', tags)
        }

        const { data: patients, error, count } = await query

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({
          data: patients,
          pagination: {
            page,
            limit,
            total: count,
            pages: Math.ceil((count || 0) / limit)
          }
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'PUT': {
        if (!patientId) {
          return new Response('Patient ID required', { status: 400, headers: corsHeaders })
        }

        const body = await req.json()
        const updates = UpdatePatientSchema.parse(body)

        const { data: patient, error } = await supabase
          .from('patients')
          .update(updates)
          .eq('id', patientId)
          .select()
          .single()

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Log the action
        await supabaseAdmin
          .from('audit_logs')
          .insert({
            actor_id: user.id,
            org_id: profile.org_id,
            action: 'update_patient',
            entity_table: 'patients',
            entity_id: patientId,
            diff: updates
          })

        return new Response(JSON.stringify(patient), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'DELETE': {
        if (!patientId) {
          return new Response('Patient ID required', { status: 400, headers: corsHeaders })
        }

        // Soft delete
        const { error } = await supabase
          .from('patients')
          .update({ deleted_at: new Date().toISOString() })
          .eq('id', patientId)

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Log the action
        await supabaseAdmin
          .from('audit_logs')
          .insert({
            actor_id: user.id,
            org_id: profile.org_id,
            action: 'delete_patient',
            entity_table: 'patients',
            entity_id: patientId,
            diff: { deleted_at: new Date().toISOString() }
          })

        return new Response(JSON.stringify({ success: true }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      default:
        return new Response('Method not allowed', { status: 405, headers: corsHeaders })
    }
  } catch (error) {
    console.error('Function error:', error)
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})