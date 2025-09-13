import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'
import { z } from "https://deno.land/x/zod@v3.16.1/mod.ts"

const ProtocolCreateSchema = z.object({
  patient_id: z.string().uuid(),
  name: z.string().min(1),
  goals: z.record(z.string()).optional()
})

const ProtocolUpdateSchema = z.object({
  name: z.string().optional(),
  goals: z.record(z.string()).optional(),
  status: z.enum(['active', 'completed', 'paused']).optional()
})

const SessionUpdateSchema = z.object({
  status: z.enum(['done', 'scheduled', 'skipped']),
  notes: z.string().optional(),
  clinician_id: z.string().uuid().optional(),
  completed_at: z.string().optional()
})

const AnalysisCreateSchema = z.object({
  patient_id: z.string().uuid(),
  kind: z.enum(['blood', 'hormonal', 'oligoscan', 'dna', 'microbiome', 'skin_scan', 'other']),
  metrics: z.record(z.any()).optional(),
  source: z.enum(['upload', 'clinic']).default('upload'),
  document_ids: z.array(z.string()).default([])
})

const LongevityScoreCreateSchema = z.object({
  patient_id: z.string().uuid(),
  score_numeric: z.number().min(0).max(100),
  components: z.record(z.any()).optional(),
  community_avg_snapshot: z.number().optional()
})

const PrePostSetCreateSchema = z.object({
  patient_id: z.string().uuid(),
  treatment_context: z.string().optional(),
  before_image: z.string().optional(),
  after_image: z.string().optional(),
  notes: z.string().optional()
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
      case 'protocols': {
        if (req.method === 'GET') {
          let query = supabase
            .from('protocols')
            .select(`
              *,
              patient:patients(id, full_name, code),
              sessions:protocol_sessions(*)
            `)

          // If user is a patient, only show their own protocols
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
            // Staff can see all protocols in their org
            query = query.in('patient_id', 
              supabaseAdmin
                .from('patients')
                .select('id')
                .eq('org_id', profile.org_id)
            )
          }

          const { data: protocols, error } = await query

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(protocols), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          if (profile.role === 'member') {
            return new Response('Insufficient permissions', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const protocolData = ProtocolCreateSchema.parse(body)

          const { data: protocol, error } = await supabase
            .from('protocols')
            .insert({
              ...protocolData,
              ai_version: 'v1.0',
              last_ai_update_at: new Date().toISOString()
            })
            .select()
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(protocol), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'protocol': {
        if (!id || id === 'protocol') {
          return new Response('Protocol ID required', { status: 400, headers: corsHeaders })
        }

        if (req.method === 'GET') {
          const { data: protocol, error } = await supabase
            .from('protocols')
            .select(`
              *,
              patient:patients(id, full_name, code, email),
              sessions:protocol_sessions(*)
            `)
            .eq('id', id)
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(protocol), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'PUT') {
          if (profile.role === 'member') {
            return new Response('Insufficient permissions', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const updateData = ProtocolUpdateSchema.parse(body)

          const { data: protocol, error } = await supabase
            .from('protocols')
            .update(updateData)
            .eq('id', id)
            .select()
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(protocol), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'sessions': {
        const sessionId = id

        if (req.method === 'PUT') {
          if (profile.role === 'member') {
            return new Response('Insufficient permissions', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const updateData = SessionUpdateSchema.parse(body)

          const { data: session, error } = await supabase
            .from('protocol_sessions')
            .update({
              ...updateData,
              completed_at: updateData.status === 'done' ? 
                (updateData.completed_at || new Date().toISOString()) : null
            })
            .eq('id', sessionId)
            .select()
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(session), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'analyses': {
        if (req.method === 'GET') {
          let query = supabase
            .from('analyses')
            .select(`
              *,
              patient:patients(id, full_name, code)
            `)
            .order('created_at', { ascending: false })

          // If user is a patient, only show their own analyses
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

          const { data: analyses, error } = await query

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(analyses), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          const body = await req.json()
          const analysisData = AnalysisCreateSchema.parse(body)

          // If user is a patient, ensure they can only create analyses for themselves
          if (profile.role === 'member') {
            const { data: patient } = await supabase
              .from('patients')
              .select('id')
              .eq('owner_user_id', user.id)
              .single()

            if (!patient || patient.id !== analysisData.patient_id) {
              return new Response('Can only create analyses for own patient record', { 
                status: 403, 
                headers: corsHeaders 
              })
            }
          }

          const { data: analysis, error } = await supabase
            .from('analyses')
            .insert({
              ...analysisData,
              created_by: user.id
            })
            .select()
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(analysis), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'longevity-scores': {
        if (req.method === 'GET') {
          let query = supabase
            .from('longevity_scores')
            .select(`
              *,
              patient:patients(id, full_name, code)
            `)
            .order('computed_at', { ascending: false })

          // If user is a patient, only show their own scores
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

          const { data: scores, error } = await query

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(scores), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          if (profile.role === 'member') {
            return new Response('Insufficient permissions', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const scoreData = LongevityScoreCreateSchema.parse(body)

          const { data: score, error } = await supabase
            .from('longevity_scores')
            .insert(scoreData)
            .select()
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(score), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'prepost-sets': {
        if (req.method === 'GET') {
          let query = supabase
            .from('prepost_sets')
            .select(`
              *,
              patient:patients(id, full_name, code)
            `)
            .order('created_at', { ascending: false })

          // If user is a patient, only show their own sets
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

          const { data: sets, error } = await query

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(sets), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          if (profile.role === 'member') {
            return new Response('Insufficient permissions', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const setData = PrePostSetCreateSchema.parse(body)

          const { data: prepostSet, error } = await supabase
            .from('prepost_sets')
            .insert(setData)
            .select()
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(prepostSet), {
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
    console.error('Clinical function error:', error)
    return new Response(JSON.stringify({ 
      error: error.message || 'Internal server error' 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})