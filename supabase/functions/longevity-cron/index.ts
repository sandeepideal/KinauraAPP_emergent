import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'

interface ComputeResult {
  success: number
  failed: number
  errors: string[]
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405, headers: corsHeaders })
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Verify CRON authorization (in production, this would be a secret key)
    const authHeader = req.headers.get('Authorization')
    const cronSecret = Deno.env.get('CRON_SECRET')
    
    if (cronSecret && authHeader !== `Bearer ${cronSecret}`) {
      return new Response('Unauthorized', { status: 401, headers: corsHeaders })
    }

    console.log('Starting nightly longevity score recomputation...')
    
    // Get all patients with biological age measurements
    const { data: patientsWithBioAge, error: patientsError } = await supabase
      .from('patients')
      .select(`
        id,
        full_name,
        org_id,
        biological_ages!inner(
          id,
          measured_at
        )
      `)
      .is('deleted_at', null)

    if (patientsError) {
      throw new Error(`Failed to fetch patients: ${patientsError.message}`)
    }

    if (!patientsWithBioAge || patientsWithBioAge.length === 0) {
      return new Response(JSON.stringify({
        success: true,
        message: 'No patients with biological age measurements found',
        results: { success: 0, failed: 0, errors: [] }
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    console.log(`Found ${patientsWithBioAge.length} patients with biological age data`)

    // Process patients in batches to avoid overwhelming the system
    const BATCH_SIZE = 50
    const results: ComputeResult = { success: 0, failed: 0, errors: [] }
    
    for (let i = 0; i < patientsWithBioAge.length; i += BATCH_SIZE) {
      const batch = patientsWithBioAge.slice(i, i + BATCH_SIZE)
      console.log(`Processing batch ${Math.floor(i / BATCH_SIZE) + 1}/${Math.ceil(patientsWithBioAge.length / BATCH_SIZE)}`)

      // Process batch in parallel
      const batchPromises = batch.map(async (patient) => {
        try {
          // Check if patient needs score update
          const { data: currentScore } = await supabase
            .from('longevity_scores')
            .select('computed_at')
            .eq('patient_id', patient.id)
            .order('computed_at', { ascending: false })
            .limit(1)

          // Get latest biological age measurement
          const { data: latestBioAge } = await supabase
            .from('biological_ages')
            .select('measured_at')
            .eq('patient_id', patient.id)
            .order('measured_at', { ascending: false })
            .limit(1)

          // Skip if score is up to date (computed after latest biological age measurement)
          if (currentScore && latestBioAge && currentScore[0] && latestBioAge[0]) {
            const scoreDate = new Date(currentScore[0].computed_at)
            const bioAgeDate = new Date(latestBioAge[0].measured_at)
            
            if (scoreDate >= bioAgeDate) {
              console.log(`Skipping patient ${patient.id} - score is up to date`)
              return { success: true, patient_id: patient.id, skipped: true }
            }
          }

          // Compute/update score
          const { data: scoreData, error: scoreError } = await supabase.rpc(
            'fn_upsert_patient_score',
            { patient_id_param: patient.id }
          )

          if (scoreError) {
            throw new Error(`Score computation failed: ${scoreError.message}`)
          }

          console.log(`✅ Computed score for patient ${patient.id}: ${scoreData?.score || 'N/A'}`)
          return { success: true, patient_id: patient.id, score: scoreData?.score }

        } catch (error) {
          console.error(`❌ Failed to compute score for patient ${patient.id}:`, error)
          return { 
            success: false, 
            patient_id: patient.id, 
            error: error.message 
          }
        }
      })

      // Wait for batch to complete
      const batchResults = await Promise.allSettled(batchPromises)
      
      // Process results
      batchResults.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          if (result.value.success) {
            results.success++
          } else {
            results.failed++
            results.errors.push(`Patient ${result.value.patient_id}: ${result.value.error}`)
          }
        } else {
          const patient = batch[index]
          results.failed++
          results.errors.push(`Patient ${patient.id}: ${result.reason}`)
        }
      })

      // Small delay between batches
      if (i + BATCH_SIZE < patientsWithBioAge.length) {
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }

    // Log completion statistics
    console.log(`Longevity score recomputation completed:`)
    console.log(`- Success: ${results.success}`)
    console.log(`- Failed: ${results.failed}`)
    console.log(`- Errors: ${results.errors.length}`)

    // Create audit log entry for the batch job
    await supabase
      .from('audit_logs')
      .insert({
        actor_id: null, // System action
        action: 'longevity_scores_batch_recompute',
        entity_table: 'longevity_scores',
        entity_id: null,
        diff: {
          total_patients: patientsWithBioAge.length,
          success_count: results.success,
          failed_count: results.failed,
          batch_size: BATCH_SIZE
        },
        metadata: {
          timestamp: new Date().toISOString(),
          errors: results.errors.slice(0, 10) // Keep first 10 errors
        }
      })

    // Refresh materialized view if it exists (optional optimization)
    try {
      await supabase.rpc('refresh_materialized_view', { 
        view_name: 'mv_cohort_ranking' 
      })
      console.log('Materialized view refreshed successfully')
    } catch (viewError) {
      console.log('No materialized view to refresh (this is normal)')
    }

    // Send realtime updates for major cohorts
    try {
      const { data: cohorts } = await supabase
        .from('longevity_scores')
        .select('cohort_key')
        .gte('computed_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())

      if (cohorts && cohorts.length > 0) {
        const uniqueCohorts = [...new Set(cohorts.map(c => c.cohort_key))]
        
        for (const cohortKey of uniqueCohorts) {
          await supabase
            .channel('longevity-updates')
            .send({
              type: 'broadcast',
              event: 'scores_updated',
              payload: {
                cohort_key: cohortKey,
                timestamp: new Date().toISOString()
              }
            })
        }

        console.log(`Sent realtime updates for ${uniqueCohorts.length} cohorts`)
      }
    } catch (realtimeError) {
      console.warn('Failed to send realtime updates:', realtimeError)
    }

    return new Response(JSON.stringify({
      success: true,
      message: 'Longevity score recomputation completed',
      results: {
        total_patients: patientsWithBioAge.length,
        success_count: results.success,
        failed_count: results.failed,
        error_count: results.errors.length,
        errors: results.errors.slice(0, 5) // Return first 5 errors
      }
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Batch recomputation error:', error)
    
    // Log the error
    try {
      const supabase = createClient(
        Deno.env.get('SUPABASE_URL') ?? '',
        Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
      )
      
      await supabase
        .from('audit_logs')
        .insert({
          actor_id: null,
          action: 'longevity_scores_batch_recompute_failed',
          entity_table: 'longevity_scores',
          entity_id: null,
          diff: {
            error: error.message,
            timestamp: new Date().toISOString()
          }
        })
    } catch (logError) {
      console.error('Failed to log error:', logError)
    }

    return new Response(JSON.stringify({ 
      error: error.message || 'Batch recomputation failed',
      timestamp: new Date().toISOString()
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})