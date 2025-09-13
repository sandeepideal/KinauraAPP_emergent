import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'
import { z } from "https://deno.land/x/zod@v3.16.1/mod.ts"

const FormulaCreateSchema = z.object({
  patient_id: z.string().uuid(),
  analysis_id: z.string().uuid().optional(),
  name: z.string().min(1),
  actives: z.record(z.any()).default({}),
  concentration: z.record(z.any()).default({}),
  fragrance: z.string().optional(),
  packaging: z.enum(['tube', 'jar', 'bottle', 'serum_bottle']).default('jar'),
  price_cents: z.number().min(15000) // Minimum €150
})

const FormulaUpdateSchema = z.object({
  name: z.string().optional(),
  actives: z.record(z.any()).optional(),
  concentration: z.record(z.any()).optional(),
  fragrance: z.string().optional(),
  packaging: z.enum(['tube', 'jar', 'bottle', 'serum_bottle']).optional(),
  price_cents: z.number().min(15000).optional(),
  status: z.enum(['draft', 'finalized']).optional()
})

const OrderCreateSchema = z.object({
  patient_id: z.string().uuid(),
  formula_id: z.string().uuid(),
  channel: z.enum(['in_clinic', 'app']).default('app'),
  total_cents: z.number().min(0)
})

const OrderUpdateSchema = z.object({
  status: z.enum(['pending', 'paid', 'fulfilled', 'canceled']),
  payment_ref: z.string().optional()
})

const MembershipPlanCreateSchema = z.object({
  name: z.string().min(1),
  tier: z.enum(['standard', 'gold', 'platinum', 'elite']),
  price_cents: z.number().min(0),
  perks: z.record(z.any()).default({}),
  billing_period: z.enum(['monthly', 'quarterly', 'yearly']).default('monthly')
})

const MembershipCreateSchema = z.object({
  patient_id: z.string().uuid(),
  plan_id: z.string().uuid(),
  start_date: z.string(), // ISO date
  end_date: z.string().optional(), // ISO date
  auto_renew: z.boolean().default(true)
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
      case 'formulas': {
        if (req.method === 'GET') {
          let query = supabase
            .from('formulas')
            .select(`
              *,
              patient:patients(id, full_name, code),
              analysis:analyses(kind, created_at)
            `)
            .order('created_at', { ascending: false })

          // If user is a patient, only show their own formulas
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
            // Staff can see all formulas in their org
            query = query.in('patient_id', 
              supabaseAdmin
                .from('patients')
                .select('id')
                .eq('org_id', profile.org_id)
            )
          }

          const { data: formulas, error } = await query

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Convert price from cents to euros
          const formulasWithPrice = formulas.map(formula => ({
            ...formula,
            price: formula.price_cents / 100
          }))

          return new Response(JSON.stringify(formulasWithPrice), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          if (profile.role === 'member') {
            return new Response('Insufficient permissions', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const formulaData = FormulaCreateSchema.parse(body)

          const { data: formula, error } = await supabase
            .from('formulas')
            .insert(formulaData)
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

          return new Response(JSON.stringify({
            ...formula,
            price: formula.price_cents / 100
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'formula': {
        if (!id || id === 'formula') {
          return new Response('Formula ID required', { status: 400, headers: corsHeaders })
        }

        if (req.method === 'GET') {
          const { data: formula, error } = await supabase
            .from('formulas')
            .select(`
              *,
              patient:patients(id, full_name, code, email),
              analysis:analyses(kind, metrics, created_at)
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
            ...formula,
            price: formula.price_cents / 100
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'PUT') {
          if (profile.role === 'member') {
            return new Response('Insufficient permissions', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const updateData = FormulaUpdateSchema.parse(body)

          const { data: formula, error } = await supabase
            .from('formulas')
            .update(updateData)
            .eq('id', id)
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

          return new Response(JSON.stringify({
            ...formula,
            price: formula.price_cents / 100
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'orders': {
        if (req.method === 'GET') {
          let query = supabase
            .from('orders')
            .select(`
              *,
              patient:patients(id, full_name, code, email),
              formula:formulas(name, packaging, price_cents)
            `)
            .order('created_at', { ascending: false })

          // If user is a patient, only show their own orders
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
            // Staff can see all orders in their org
            query = query.in('patient_id', 
              supabaseAdmin
                .from('patients')
                .select('id')
                .eq('org_id', profile.org_id)
            )
          }

          const { data: orders, error } = await query

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Convert price from cents to euros
          const ordersWithPrice = orders.map(order => ({
            ...order,
            total: order.total_cents / 100,
            formula_price: order.formula?.price_cents ? order.formula.price_cents / 100 : 0
          }))

          return new Response(JSON.stringify(ordersWithPrice), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          const body = await req.json()
          const orderData = OrderCreateSchema.parse(body)

          // If user is a patient, ensure they can only create orders for themselves
          if (profile.role === 'member') {
            const { data: patient } = await supabase
              .from('patients')
              .select('id')
              .eq('owner_user_id', user.id)
              .single()

            if (!patient || patient.id !== orderData.patient_id) {
              return new Response('Can only create orders for own patient record', { 
                status: 403, 
                headers: corsHeaders 
              })
            }
          }

          const { data: order, error } = await supabase
            .from('orders')
            .insert(orderData)
            .select(`
              *,
              patient:patients(id, full_name, code),
              formula:formulas(name, packaging, price_cents)
            `)
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({
            ...order,
            total: order.total_cents / 100
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'order': {
        if (!id || id === 'order') {
          return new Response('Order ID required', { status: 400, headers: corsHeaders })
        }

        if (req.method === 'GET') {
          const { data: order, error } = await supabase
            .from('orders')
            .select(`
              *,
              patient:patients(id, full_name, code, email),
              formula:formulas(name, packaging, price_cents, actives, concentration)
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
            ...order,
            total: order.total_cents / 100
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'PUT') {
          if (profile.role === 'member') {
            return new Response('Insufficient permissions', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const updateData = OrderUpdateSchema.parse(body)

          const { data: order, error } = await supabase
            .from('orders')
            .update(updateData)
            .eq('id', id)
            .select(`
              *,
              patient:patients(id, full_name, code),
              formula:formulas(name, packaging, price_cents)
            `)
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({
            ...order,
            total: order.total_cents / 100
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'membership-plans': {
        if (req.method === 'GET') {
          const { data: plans, error } = await supabase
            .from('membership_plans')
            .select('*')
            .eq('org_id', profile.org_id)
            .eq('is_active', true)
            .order('price_cents')

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Convert price from cents to euros
          const plansWithPrice = plans.map(plan => ({
            ...plan,
            price: plan.price_cents / 100
          }))

          return new Response(JSON.stringify(plansWithPrice), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          if (profile.role !== 'admin') {
            return new Response('Admin access required', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const planData = MembershipPlanCreateSchema.parse(body)

          const { data: plan, error } = await supabase
            .from('membership_plans')
            .insert({
              ...planData,
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
            ...plan,
            price: plan.price_cents / 100
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'memberships': {
        if (req.method === 'GET') {
          let query = supabase
            .from('memberships')
            .select(`
              *,
              patient:patients(id, full_name, code, email),
              plan:membership_plans(name, tier, price_cents, perks, billing_period)
            `)
            .eq('org_id', profile.org_id)
            .order('created_at', { ascending: false })

          // If user is a patient, only show their own membership
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

          const { data: memberships, error } = await query

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Convert price from cents to euros
          const membershipsWithPrice = memberships.map(membership => ({
            ...membership,
            plan_price: membership.plan?.price_cents ? membership.plan.price_cents / 100 : 0
          }))

          return new Response(JSON.stringify(membershipsWithPrice), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          if (!['admin', 'practitioner'].includes(profile.role)) {
            return new Response('Insufficient permissions', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const membershipData = MembershipCreateSchema.parse(body)

          const { data: membership, error } = await supabase
            .from('memberships')
            .insert({
              ...membershipData,
              org_id: profile.org_id,
              status: 'active'
            })
            .select(`
              *,
              patient:patients(id, full_name, code),
              plan:membership_plans(name, tier, price_cents, perks)
            `)
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Update patient's VIP tier
          if (membership.plan?.tier) {
            await supabase
              .from('patients')
              .update({ vip_tier: membership.plan.tier })
              .eq('id', membershipData.patient_id)
          }

          return new Response(JSON.stringify({
            ...membership,
            plan_price: membership.plan?.price_cents ? membership.plan.price_cents / 100 : 0
          }), {
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
    console.error('Commerce function error:', error)
    return new Response(JSON.stringify({ 
      error: error.message || 'Internal server error' 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})