import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'
import { z } from "https://deno.land/x/zod@v3.16.1/mod.ts"

const MetricsQuerySchema = z.object({
  start_date: z.string().optional(),
  end_date: z.string().optional(),
  metrics: z.array(z.enum([
    'new_patients', 'active_members', 'revenue', 'adherence', 
    'campaign_ctr', 'avg_longevity_score', 'appointments'
  ])).default(['new_patients', 'active_members', 'revenue'])
})

const AuditSearchSchema = z.object({
  actor_id: z.string().uuid().optional(),
  table: z.string().optional(),
  action: z.string().optional(),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
  limit: z.number().default(50).max(500)
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
    const path = url.pathname.split('/').pop()

    const { data: { user } } = await supabase.auth.getUser()
    if (!user) {
      return new Response('Unauthorized', { status: 401, headers: corsHeaders })
    }

    const { data: profile } = await supabase
      .from('profiles')
      .select('role, org_id')
      .eq('id', user.id)
      .single()

    if (!profile || profile.role !== 'admin') {
      return new Response('Admin access required', { status: 403, headers: corsHeaders })
    }

    switch (path) {
      case 'metrics': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const body = await req.json()
        const { start_date, end_date, metrics } = MetricsQuerySchema.parse(body)

        const startDate = start_date ? new Date(start_date) : new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
        const endDate = end_date ? new Date(end_date) : new Date()

        const results: Record<string, any> = {}

        for (const metric of metrics) {
          switch (metric) {
            case 'new_patients': {
              const { count } = await supabaseAdmin
                .from('patients')
                .select('*', { count: 'exact', head: true })
                .eq('org_id', profile.org_id)
                .gte('created_at', startDate.toISOString())
                .lte('created_at', endDate.toISOString())
                .is('deleted_at', null)

              results.new_patients = count || 0
              break
            }

            case 'active_members': {
              const { count } = await supabaseAdmin
                .from('memberships')
                .select('*', { count: 'exact', head: true })
                .eq('org_id', profile.org_id)
                .eq('status', 'active')

              results.active_members = count || 0
              break
            }

            case 'revenue': {
              const { data: orders } = await supabaseAdmin
                .from('orders')
                .select('total_cents')
                .eq('status', 'paid')
                .gte('created_at', startDate.toISOString())
                .lte('created_at', endDate.toISOString())

              const totalRevenue = orders?.reduce((sum, order) => sum + order.total_cents, 0) || 0
              results.revenue = {
                total_cents: totalRevenue,
                total_euros: totalRevenue / 100
              }
              break
            }

            case 'adherence': {
              // Calculate average protocol adherence
              const { data: sessions } = await supabaseAdmin
                .from('protocol_sessions')
                .select(`
                  status,
                  protocol:protocols!inner(
                    patient:patients!inner(org_id)
                  )
                `)
                .eq('protocol.patient.org_id', profile.org_id)

              if (sessions && sessions.length > 0) {
                const completedSessions = sessions.filter(s => s.status === 'done').length
                const adherenceRate = (completedSessions / sessions.length) * 100
                results.adherence = Math.round(adherenceRate * 100) / 100
              } else {
                results.adherence = 0
              }
              break
            }

            case 'campaign_ctr': {
              const { data: campaigns } = await supabaseAdmin
                .from('campaigns')
                .select('sent_count, metadata')
                .eq('org_id', profile.org_id)
                .eq('status', 'sent')
                .gte('created_at', startDate.toISOString())
                .lte('created_at', endDate.toISOString())

              // This is a simplified CTR calculation
              // In reality, you'd track clicks in notifications/campaigns
              const totalSent = campaigns?.reduce((sum, c) => sum + (c.sent_count || 0), 0) || 0
              const estimatedClicks = Math.floor(totalSent * 0.15) // Mock 15% CTR
              results.campaign_ctr = totalSent > 0 ? (estimatedClicks / totalSent) * 100 : 0
              break
            }

            case 'avg_longevity_score': {
              const { data: scores } = await supabaseAdmin
                .from('longevity_scores')
                .select(`
                  score_numeric,
                  patient:patients!inner(org_id)
                `)
                .eq('patient.org_id', profile.org_id)
                .gte('computed_at', startDate.toISOString())
                .lte('computed_at', endDate.toISOString())

              if (scores && scores.length > 0) {
                const average = scores.reduce((sum, s) => sum + s.score_numeric, 0) / scores.length
                results.avg_longevity_score = Math.round(average * 100) / 100
              } else {
                results.avg_longevity_score = 0
              }
              break
            }

            case 'appointments': {
              const { count: totalAppointments } = await supabaseAdmin
                .from('appointments')
                .select('*', { count: 'exact', head: true })
                .eq('org_id', profile.org_id)
                .gte('created_at', startDate.toISOString())
                .lte('created_at', endDate.toISOString())

              const { count: completedAppointments } = await supabaseAdmin
                .from('appointments')
                .select('*', { count: 'exact', head: true })
                .eq('org_id', profile.org_id)
                .eq('status', 'completed')
                .gte('created_at', startDate.toISOString())
                .lte('created_at', endDate.toISOString())

              results.appointments = {
                total: totalAppointments || 0,
                completed: completedAppointments || 0,
                completion_rate: totalAppointments > 0 ? ((completedAppointments || 0) / totalAppointments) * 100 : 0
              }
              break
            }
          }
        }

        return new Response(JSON.stringify({
          period: {
            start_date: startDate.toISOString().split('T')[0],
            end_date: endDate.toISOString().split('T')[0]
          },
          metrics: results
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'audit-search': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const body = await req.json()
        const { actor_id, table, action, start_date, end_date, limit } = AuditSearchSchema.parse(body)

        let query = supabaseAdmin
          .from('audit_logs')
          .select(`
            *,
            actor:profiles(full_name, role)
          `)
          .eq('org_id', profile.org_id)
          .order('created_at', { ascending: false })
          .limit(limit)

        if (actor_id) {
          query = query.eq('actor_id', actor_id)
        }

        if (table) {
          query = query.eq('entity_table', table)
        }

        if (action) {
          query = query.ilike('action', `%${action}%`)
        }

        if (start_date) {
          query = query.gte('created_at', new Date(start_date).toISOString())
        }

        if (end_date) {
          query = query.lte('created_at', new Date(end_date).toISOString())
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

      case 'dashboard-overview': {
        if (req.method !== 'GET') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        // Get key metrics for admin dashboard
        const today = new Date()
        const thisMonth = new Date(today.getFullYear(), today.getMonth(), 1)
        const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1)

        // Patients this month vs last month
        const { count: patientsThisMonth } = await supabaseAdmin
          .from('patients')
          .select('*', { count: 'exact', head: true })
          .eq('org_id', profile.org_id)
          .gte('created_at', thisMonth.toISOString())
          .is('deleted_at', null)

        const { count: patientsLastMonth } = await supabaseAdmin
          .from('patients')
          .select('*', { count: 'exact', head: true })
          .eq('org_id', profile.org_id)
          .gte('created_at', lastMonth.toISOString())
          .lt('created_at', thisMonth.toISOString())
          .is('deleted_at', null)

        // Active memberships
        const { count: activeMemberships } = await supabaseAdmin
          .from('memberships')
          .select('*', { count: 'exact', head: true })
          .eq('org_id', profile.org_id)
          .eq('status', 'active')

        // Revenue this month
        const { data: ordersThisMonth } = await supabaseAdmin
          .from('orders')
          .select('total_cents')
          .eq('status', 'paid')
          .gte('created_at', thisMonth.toISOString())

        const revenueThisMonth = ordersThisMonth?.reduce((sum, order) => sum + order.total_cents, 0) || 0

        // Recent activities
        const { data: recentActivities } = await supabaseAdmin
          .from('audit_logs')
          .select(`
            *,
            actor:profiles(full_name)
          `)
          .eq('org_id', profile.org_id)
          .order('created_at', { ascending: false })
          .limit(10)

        return new Response(JSON.stringify({
          patients: {
            this_month: patientsThisMonth || 0,
            last_month: patientsLastMonth || 0,
            growth: patientsLastMonth > 0 ? ((patientsThisMonth || 0) - patientsLastMonth) / patientsLastMonth * 100 : 0
          },
          memberships: {
            active: activeMemberships || 0
          },
          revenue: {
            this_month_cents: revenueThisMonth,
            this_month_euros: revenueThisMonth / 100
          },
          recent_activities: recentActivities
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'export-data': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const body = await req.json()
        const { table, format = 'json' } = body

        if (!['patients', 'appointments', 'orders', 'protocols'].includes(table)) {
          return new Response('Invalid table', { status: 400, headers: corsHeaders })
        }

        let query = supabaseAdmin.from(table)

        // Add org filtering for multi-tenant tables
        if (['patients', 'appointments', 'orders'].includes(table)) {
          query = query.eq('org_id', profile.org_id)
        } else if (table === 'protocols') {
          // Protocols are linked via patients
          query = query.select(`
            *,
            patient!inner(org_id)
          `).eq('patient.org_id', profile.org_id)
        }

        const { data, error } = await query.select('*')

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Log the export
        await supabaseAdmin
          .from('audit_logs')
          .insert({
            actor_id: user.id,
            org_id: profile.org_id,
            action: 'export_data',
            entity_table: table,
            entity_id: user.id, // Use user ID as entity for exports
            diff: { table, format, record_count: data?.length || 0 }
          })

        if (format === 'csv') {
          // Convert to CSV (simplified)
          if (!data || data.length === 0) {
            return new Response('', {
              headers: { 
                ...corsHeaders, 
                'Content-Type': 'text/csv',
                'Content-Disposition': `attachment; filename="${table}-export.csv"`
              }
            })
          }

          const headers = Object.keys(data[0]).join(',')
          const rows = data.map(row => 
            Object.values(row).map(value => 
              typeof value === 'string' ? `"${value.replace(/"/g, '""')}"` : value
            ).join(',')
          )
          const csv = [headers, ...rows].join('\n')

          return new Response(csv, {
            headers: { 
              ...corsHeaders, 
              'Content-Type': 'text/csv',
              'Content-Disposition': `attachment; filename="${table}-export.csv"`
            }
          })
        }

        return new Response(JSON.stringify(data), {
          headers: { 
            ...corsHeaders, 
            'Content-Type': 'application/json',
            'Content-Disposition': `attachment; filename="${table}-export.json"`
          }
        })
      }

      default:
        return new Response('Not found', { status: 404, headers: corsHeaders })
    }
  } catch (error) {
    console.error('Function error:', error)
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})