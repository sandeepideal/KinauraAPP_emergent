import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'
import { z } from "https://deno.land/x/zod@v3.16.1/mod.ts"

const RegisterSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
  full_name: z.string().min(1),
  phone: z.string().optional(),
})

const LoginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
})

const SocialLoginSchema = z.object({
  provider: z.enum(['google', 'apple', 'facebook']),
  id_token: z.string(),
  full_name: z.string(),
  email: z.string().email(),
})

const ResetPasswordSchema = z.object({
  email: z.string().email(),
})

const UpdateProfileSchema = z.object({
  full_name: z.string().optional(),
  phone: z.string().optional(),
  avatar_url: z.string().optional(),
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
    const path = url.pathname.split('/').pop()

    switch (path) {
      case 'register': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const body = await req.json()
        const { email, password, full_name, phone } = RegisterSchema.parse(body)

        // Create user with Supabase Auth
        const { data: authData, error: authError } = await supabase.auth.admin.createUser({
          email,
          password,
          email_confirm: true,
          user_metadata: {
            full_name,
            phone,
          }
        })

        if (authError) {
          return new Response(JSON.stringify({ error: authError.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Create a default organization for new users (or assign to existing one)
        let orgId = Deno.env.get('DEFAULT_ORG_ID')
        
        if (!orgId) {
          const { data: org, error: orgError } = await supabase
            .from('organizations')
            .insert({
              name: 'KinAura Clinic',
              timezone: 'Europe/Rome',
              billing_email: 'admin@kinaura.com'
            })
            .select()
            .single()

          if (orgError) {
            console.error('Error creating organization:', orgError)
            orgId = null
          } else {
            orgId = org.id
          }
        }

        // Create profile
        const { error: profileError } = await supabase
          .from('profiles')
          .insert({
            id: authData.user.id,
            org_id: orgId,
            role: 'member',
            full_name,
            avatar_url: null,
            marketing_consent: false,
            privacy_consent: true,
            vip_tier: 'standard'
          })

        if (profileError) {
          console.error('Error creating profile:', profileError)
          // Clean up the auth user if profile creation fails
          await supabase.auth.admin.deleteUser(authData.user.id)
          return new Response(JSON.stringify({ error: 'Failed to create user profile' }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Create patient record
        const { error: patientError } = await supabase
          .from('patients')
          .insert({
            org_id: orgId,
            full_name,
            email,
            phone,
            owner_user_id: authData.user.id,
            code: `PAT-${Date.now().toString().slice(-6)}`
          })

        if (patientError) {
          console.error('Error creating patient record:', patientError)
        }

        return new Response(JSON.stringify({
          user: {
            id: authData.user.id,
            email: authData.user.email,
            full_name,
            phone,
            membership_tier: 'standard'
          },
          message: 'User registered successfully'
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'login': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const body = await req.json()
        const { email, password } = LoginSchema.parse(body)

        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password,
        })

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Get user profile
        const { data: profile } = await supabase
          .from('profiles')
          .select('*, org:organizations(name)')
          .eq('id', data.user.id)
          .single()

        return new Response(JSON.stringify({
          access_token: data.session.access_token,
          refresh_token: data.session.refresh_token,
          user: {
            id: data.user.id,
            email: data.user.email,
            full_name: profile?.full_name || data.user.user_metadata?.full_name,
            phone: profile?.full_name || data.user.user_metadata?.phone,
            membership_tier: profile?.vip_tier || 'standard',
            role: profile?.role || 'member',
            org_name: profile?.org?.name
          }
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'social-login': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const body = await req.json()
        const { provider, id_token, full_name, email } = SocialLoginSchema.parse(body)

        // In a real implementation, you would verify the id_token with the provider
        // For now, we'll create/get the user based on email

        // Check if user exists
        const { data: existingUser } = await supabase.auth.admin.getUserByEmail(email)

        if (existingUser?.user) {
          // User exists, sign them in
          const { data: profile } = await supabase
            .from('profiles')
            .select('*, org:organizations(name)')
            .eq('id', existingUser.user.id)
            .single()

          // Generate session for existing user
          const { data: sessionData, error: sessionError } = await supabase.auth.admin.generateLink({
            type: 'magiclink',
            email: email
          })

          if (sessionError) {
            return new Response(JSON.stringify({ error: sessionError.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({
            user: {
              id: existingUser.user.id,
              email: existingUser.user.email,
              full_name: profile?.full_name || full_name,
              phone: profile?.phone,
              membership_tier: profile?.vip_tier || 'standard',
              role: profile?.role || 'member',
              org_name: profile?.org?.name
            },
            message: 'Social login successful'
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        } else {
          // Create new user
          const { data: authData, error: authError } = await supabase.auth.admin.createUser({
            email,
            email_confirm: true,
            user_metadata: {
              full_name,
              provider,
            }
          })

          if (authError) {
            return new Response(JSON.stringify({ error: authError.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Create profile and patient record (similar to register)
          let orgId = Deno.env.get('DEFAULT_ORG_ID')
          
          if (!orgId) {
            const { data: org } = await supabase
              .from('organizations')
              .select('id')
              .limit(1)
              .single()
            orgId = org?.id
          }

          await supabase.from('profiles').insert({
            id: authData.user.id,
            org_id: orgId,
            role: 'member',
            full_name,
            marketing_consent: false,
            privacy_consent: true,
            vip_tier: 'standard'
          })

          await supabase.from('patients').insert({
            org_id: orgId,
            full_name,
            email,
            owner_user_id: authData.user.id,
            code: `PAT-${Date.now().toString().slice(-6)}`
          })

          return new Response(JSON.stringify({
            user: {
              id: authData.user.id,
              email: authData.user.email,
              full_name,
              membership_tier: 'standard'
            },
            message: 'Social registration successful'
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }
      }

      case 'reset-password': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const body = await req.json()
        const { email } = ResetPasswordSchema.parse(body)

        const { error } = await supabase.auth.resetPasswordForEmail(email, {
          redirectTo: `${Deno.env.get('FRONTEND_URL')}/reset-password`,
        })

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({
          message: 'Password reset email sent'
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'profile': {
        const authHeader = req.headers.get('Authorization')
        if (!authHeader) {
          return new Response('Unauthorized', { status: 401, headers: corsHeaders })
        }

        const supabaseUser = createClient(
          Deno.env.get('SUPABASE_URL') ?? '',
          Deno.env.get('SUPABASE_ANON_KEY') ?? '',
          {
            global: {
              headers: { Authorization: authHeader }
            }
          }
        )

        const { data: { user } } = await supabaseUser.auth.getUser()
        if (!user) {
          return new Response('Unauthorized', { status: 401, headers: corsHeaders })
        }

        if (req.method === 'GET') {
          const { data: profile } = await supabase
            .from('profiles')
            .select('*, org:organizations(name)')
            .eq('id', user.id)
            .single()

          return new Response(JSON.stringify({
            id: user.id,
            email: user.email,
            full_name: profile?.full_name,
            phone: profile?.phone,
            avatar_url: profile?.avatar_url,
            membership_tier: profile?.vip_tier || 'standard',
            role: profile?.role || 'member',
            org_name: profile?.org?.name
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'PUT') {
          const body = await req.json()
          const updateData = UpdateProfileSchema.parse(body)

          const { error } = await supabase
            .from('profiles')
            .update(updateData)
            .eq('id', user.id)

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({
            message: 'Profile updated successfully'
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response('Method not allowed', { status: 405, headers: corsHeaders })
      }

      default:
        return new Response('Not found', { status: 404, headers: corsHeaders })
    }
  } catch (error) {
    console.error('Auth function error:', error)
    return new Response(JSON.stringify({ 
      error: error.message || 'Internal server error' 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})