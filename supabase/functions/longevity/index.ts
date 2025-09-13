import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'
import { z } from "https://deno.land/x/zod@v3.16.1/mod.ts"

// Validation schemas
const ComputeScoreSchema = z.object({
  patient_id: z.string().uuid(),
})

const MyScoreQuerySchema = z.object({
  neighbor_count: z.coerce.number().int().min(1).max(10).default(3),
})

const LeaderboardQuerySchema = z.object({
  cohort_key: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  page_size: z.coerce.number().int().min(1).max(100).default(25),
  org_id: z.string().uuid().optional(),
})

const PublishSettingsSchema = z.object({
  patient_id: z.string().uuid(),
  opt_in: z.boolean(),
  identity: z.enum(['name', 'avatar', 'anonymous']),
})

const PinPatientSchema = z.object({
  patient_id: z.string().uuid(),
  pinned: z.boolean(),
})

const UpdateConstantsSchema = z.object({
  constants: z.record(z.string(), z.number()),
})

const BiologicalAgeSchema = z.object({
  patient_id: z.string().uuid(),
  method: z.enum(['blood', 'saliva', 'epigenetic', 'device', 'composite']),
  biological_age_years: z.number().min(0).max(150),
  measured_at: z.string().datetime().optional(),
  source: z.record(z.any()).optional(),
})

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const url = new URL(req.url)
    const pathParts = url.pathname.split('/').filter(Boolean)
    const endpoint = pathParts[pathParts.length - 1]

    // Helper function to get authenticated user
    const getAuthUser = async () => {
      const authHeader = req.headers.get('Authorization')
      if (!authHeader) {
        throw new Error('Authorization header required')
      }

      const { data: { user }, error } = await supabase.auth.getUser(
        authHeader.replace('Bearer ', '')
      )
      
      if (error || !user) {
        throw new Error('Invalid authentication token')
      }

      return user
    }

    // Helper function to check admin role
    const requireAdmin = async (user: any) => {
      const { data: profile } = await supabase
        .from('profiles')
        .select('role')
        .eq('id', user.id)
        .single()

      if (!profile || profile.role !== 'admin') {
        throw new Error('Admin access required')
      }
    }

    switch (endpoint) {
      case 'compute-now': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()
        await requireAdmin(user)

        const body = await req.json()
        const { patient_id } = ComputeScoreSchema.parse(body)

        // Call the compute function
        const { data: scoreData, error: computeError } = await supabase.rpc(
          'fn_upsert_patient_score',
          { patient_id_param: patient_id }
        )

        if (computeError) {
          console.error('Score computation error:', computeError)
          return new Response(JSON.stringify({ 
            error: computeError.message 
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({
          success: true,
          data: scoreData
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'my': {
        if (req.method !== 'GET') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()
        const query = MyScoreQuerySchema.parse(Object.fromEntries(url.searchParams))

        // Get patient ID for current user
        const { data: patient } = await supabase
          .from('patients')
          .select('id')
          .eq('email', user.email)
          .single()

        if (!patient) {
          return new Response(JSON.stringify({ 
            error: 'Patient record not found' 
          }), {
            status: 404,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Get patient score data
        const { data: scoreData, error: scoreError } = await supabase.rpc(
          'get_patient_score_data',
          { target_patient_id: patient.id }
        )

        if (scoreError) {
          console.error('Score retrieval error:', scoreError)
          return new Response(JSON.stringify({ 
            error: scoreError.message 
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (!scoreData || scoreData.length === 0) {
          return new Response(JSON.stringify({ 
            error: 'No score data available. Biological age measurement required.' 
          }), {
            status: 404,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        const score = scoreData[0]

        // Get neighbors
        const { data: neighbors, error: neighborsError } = await supabase.rpc(
          'fn_get_patient_neighbors',
          { 
            patient_id_param: patient.id,
            neighbor_count: query.neighbor_count
          }
        )

        if (neighborsError) {
          console.warn('Neighbors retrieval error:', neighborsError)
        }

        return new Response(JSON.stringify({
          patient_id: score.patient_id,
          chronological_age_years: parseFloat(score.chronological_age_years),
          biological_age_years: parseFloat(score.biological_age_years),
          delta_years: parseFloat(score.delta_years),
          score: parseFloat(score.score),
          cohort_key: score.cohort_key,
          rank: parseInt(score.rank),
          total_in_cohort: parseInt(score.total_in_cohort),
          neighbors: neighbors || [],
          computed_at: score.computed_at
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'leaderboard': {
        if (req.method !== 'GET') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const query = LeaderboardQuerySchema.parse(Object.fromEntries(url.searchParams))

        // Get leaderboard data
        const { data: leaderboardData, error: leaderboardError } = await supabase.rpc(
          'get_public_leaderboard_data',
          {
            target_cohort_key: query.cohort_key || null,
            page_num: query.page,
            page_size: query.page_size,
            target_org_id: query.org_id || null
          }
        )

        if (leaderboardError) {
          console.error('Leaderboard retrieval error:', leaderboardError)
          return new Response(JSON.stringify({ 
            error: leaderboardError.message 
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        const entries = leaderboardData?.map((entry: any) => ({
          rank: parseInt(entry.rank),
          score: parseFloat(entry.score),
          display: entry.display,
          pinned: entry.pinned || false
        })) || []

        const totalEntries = leaderboardData?.[0]?.total_entries || 0

        return new Response(JSON.stringify({
          cohort_key: query.cohort_key,
          page: query.page,
          page_size: query.page_size,
          entries,
          total: parseInt(totalEntries),
          updated_at: new Date().toISOString()
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'cohorts': {
        if (req.method !== 'GET') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()
        
        // Get user's org
        const { data: profile } = await supabase
          .from('profiles')
          .select('org_id, role')
          .eq('id', user.id)
          .single()

        if (!profile || !profile.org_id) {
          return new Response(JSON.stringify({ 
            error: 'User organization not found' 
          }), {
            status: 404,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Get cohorts for the organization
        const { data: cohorts, error: cohortsError } = await supabase.rpc(
          'get_org_cohorts',
          { target_org_id: profile.org_id }
        )

        if (cohortsError) {
          console.error('Cohorts retrieval error:', cohortsError)
          return new Response(JSON.stringify({ 
            error: cohortsError.message 
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({
          cohorts: cohorts?.map((cohort: any) => ({
            cohort_key: cohort.cohort_key,
            patient_count: parseInt(cohort.patient_count),
            avg_score: parseFloat(cohort.avg_score),
            description: cohort.description
          })) || []
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'publish': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()
        await requireAdmin(user)

        const body = await req.json()
        const { patient_id, opt_in, identity } = PublishSettingsSchema.parse(body)

        // Update or insert visibility settings
        const { error: visibilityError } = await supabase
          .from('leaderboard_visibility')
          .upsert({
            patient_id,
            org_id: (await supabase.from('patients').select('org_id').eq('id', patient_id).single()).data?.org_id,
            opt_in,
            identity,
            updated_at: new Date().toISOString()
          })

        if (visibilityError) {
          console.error('Visibility update error:', visibilityError)
          return new Response(JSON.stringify({ 
            error: visibilityError.message 
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Log audit event
        await supabase
          .from('audit_logs')
          .insert({
            actor_id: user.id,
            action: 'leaderboard_publish_changed',
            entity_table: 'leaderboard_visibility',
            entity_id: patient_id,
            diff: { opt_in, identity }
          })

        return new Response(JSON.stringify({
          success: true,
          message: 'Leaderboard visibility updated successfully'
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'pin': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()
        await requireAdmin(user)

        const body = await req.json()
        const { patient_id, pinned } = PinPatientSchema.parse(body)

        // Update pin status
        const updateData: any = { 
          pinned,
          updated_at: new Date().toISOString()
        }

        if (pinned) {
          updateData.pinned_by = user.id
          updateData.pinned_at = new Date().toISOString()
        } else {
          updateData.pinned_by = null
          updateData.pinned_at = null
        }

        const { error: pinError } = await supabase
          .from('leaderboard_visibility')
          .upsert({
            patient_id,
            org_id: (await supabase.from('patients').select('org_id').eq('id', patient_id).single()).data?.org_id,
            ...updateData
          })

        if (pinError) {
          console.error('Pin update error:', pinError)
          return new Response(JSON.stringify({ 
            error: pinError.message 
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Log audit event
        await supabase
          .from('audit_logs')
          .insert({
            actor_id: user.id,
            action: pinned ? 'leaderboard_pin_added' : 'leaderboard_pin_removed',
            entity_table: 'leaderboard_visibility',
            entity_id: patient_id,
            diff: { pinned, pinned_by: pinned ? user.id : null }
          })

        return new Response(JSON.stringify({
          success: true,
          message: `Patient ${pinned ? 'pinned to' : 'unpinned from'} leaderboard`
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'constants': {
        const user = await getAuthUser()
        await requireAdmin(user)

        if (req.method === 'GET') {
          const { data: constants, error: constantsError } = await supabase
            .from('score_constants')
            .select('*')
            .order('key')

          if (constantsError) {
            return new Response(JSON.stringify({ 
              error: constantsError.message 
            }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({
            constants: constants?.reduce((acc: any, constant: any) => {
              acc[constant.key] = parseFloat(constant.value)
              return acc
            }, {}) || {}
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          const body = await req.json()
          const { constants } = UpdateConstantsSchema.parse(body)

          // Update each constant
          const updates = Object.entries(constants).map(([key, value]) => 
            supabase
              .from('score_constants')
              .upsert({ 
                key, 
                value: value as number,
                updated_at: new Date().toISOString()
              })
          )

          const results = await Promise.allSettled(updates)
          const errors = results
            .filter(result => result.status === 'rejected')
            .map(result => (result as PromiseRejectedResult).reason)

          if (errors.length > 0) {
            console.error('Constants update errors:', errors)
            return new Response(JSON.stringify({ 
              error: 'Failed to update some constants',
              details: errors
            }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Log audit event
          await supabase
            .from('audit_logs')
            .insert({
              actor_id: user.id,
              action: 'score_constants_updated',
              entity_table: 'score_constants',
              entity_id: user.id,
              diff: constants
            })

          return new Response(JSON.stringify({
            success: true,
            message: 'Score constants updated successfully'
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response('Method not allowed', { status: 405, headers: corsHeaders })
      }

      case 'biological-age': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()
        await requireAdmin(user)

        const body = await req.json()
        const { patient_id, method, biological_age_years, measured_at, source } = BiologicalAgeSchema.parse(body)

        // Insert biological age measurement
        const { error: insertError } = await supabase
          .from('biological_ages')
          .insert({
            patient_id,
            method,
            biological_age_years,
            measured_at: measured_at || new Date().toISOString(),
            source: source || {}
          })

        if (insertError) {
          console.error('Biological age insert error:', insertError)
          return new Response(JSON.stringify({ 
            error: insertError.message 
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Auto-compute longevity score
        try {
          const { data: scoreData } = await supabase.rpc(
            'fn_upsert_patient_score',
            { patient_id_param: patient_id }
          )

          return new Response(JSON.stringify({
            success: true,
            message: 'Biological age recorded and score computed',
            score_data: scoreData
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        } catch (scoreError) {
          console.warn('Score computation failed after biological age insert:', scoreError)
          
          return new Response(JSON.stringify({
            success: true,
            message: 'Biological age recorded (score computation failed)',
            warning: 'Score will be computed in next batch job'
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }
      }

      default:
        return new Response('Not found', { status: 404, headers: corsHeaders })
    }
  } catch (error) {
    console.error('Longevity score function error:', error)
    return new Response(JSON.stringify({ 
      error: error.message || 'Internal server error' 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})