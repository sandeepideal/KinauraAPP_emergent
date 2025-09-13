import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'
import { z } from "https://deno.land/x/zod@v3.16.1/mod.ts"

const ThreadCreateSchema = z.object({
  patient_id: z.string().uuid()
})

const MessageCreateSchema = z.object({
  thread_id: z.string().uuid(),
  body: z.string().min(1),
  attachments: z.array(z.string()).default([])
})

const NotificationCreateSchema = z.object({
  patient_id: z.string().uuid(),
  channel: z.enum(['push', 'email', 'sms']),
  title: z.string().optional(),
  body: z.string().min(1),
  data: z.record(z.any()).default({})
})

const CampaignCreateSchema = z.object({
  name: z.string().min(1),
  channel: z.enum(['push', 'email', 'sms']),
  template_id: z.string().optional(),
  segment_id: z.string().uuid().optional(),
  metadata: z.record(z.any()).default({})
})

const SegmentCreateSchema = z.object({
  name: z.string().min(1),
  description: z.string().optional(),
  definition: z.record(z.any()) // JSON DSL for filtering criteria
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
      .select('role, org_id, full_name')
      .eq('id', user.id)
      .single()

    if (!profile) {
      return new Response('Profile not found', { status: 404, headers: corsHeaders })
    }

    switch (resource) {
      case 'threads': {
        if (req.method === 'GET') {
          let query = supabase
            .from('threads')
            .select(`
              *,
              patient:patients(id, full_name, code, email),
              messages:messages(*, sender:profiles(full_name, role))
            `)
            .order('last_message_at', { ascending: false })

          // If user is a patient, only show their own threads
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
            // Staff can see all threads for patients in their org
            query = query.in('patient_id', 
              supabaseAdmin
                .from('patients')
                .select('id')
                .eq('org_id', profile.org_id)
            )
          }

          const { data: threads, error } = await query

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Sort messages within each thread by creation time
          const threadsWithSortedMessages = threads.map(thread => ({
            ...thread,
            messages: thread.messages.sort((a, b) => 
              new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
            ),
            unread_count: thread.messages.filter(m => !m.read_at && m.sender_id !== user.id).length
          }))

          return new Response(JSON.stringify(threadsWithSortedMessages), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          const body = await req.json()
          const threadData = ThreadCreateSchema.parse(body)

          // If user is a patient, ensure they can only create threads for themselves
          if (profile.role === 'member') {
            const { data: patient } = await supabase
              .from('patients')
              .select('id')
              .eq('owner_user_id', user.id)
              .single()

            if (!patient || patient.id !== threadData.patient_id) {
              return new Response('Can only create threads for own patient record', { 
                status: 403, 
                headers: corsHeaders 
              })
            }
          }

          const { data: thread, error } = await supabase
            .from('threads')
            .insert({
              ...threadData,
              created_by: user.id
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

          return new Response(JSON.stringify(thread), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'thread': {
        if (!id || id === 'thread') {
          return new Response('Thread ID required', { status: 400, headers: corsHeaders })
        }

        if (req.method === 'GET') {
          const { data: thread, error } = await supabase
            .from('threads')
            .select(`
              *,
              patient:patients(id, full_name, code, email),
              messages:messages(*, sender:profiles(full_name, role))
            `)
            .eq('id', id)
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Sort messages by creation time
          thread.messages = thread.messages.sort((a, b) => 
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          )

          return new Response(JSON.stringify(thread), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'messages': {
        if (req.method === 'POST') {
          const body = await req.json()
          const messageData = MessageCreateSchema.parse(body)

          // Determine sender role
          let senderRole = 'patient'
          if (profile.role === 'admin') {
            senderRole = 'admin'
          } else if (profile.role === 'practitioner') {
            senderRole = 'practitioner'
          }

          const { data: message, error } = await supabase
            .from('messages')
            .insert({
              ...messageData,
              sender_id: user.id,
              sender_role: senderRole
            })
            .select(`
              *,
              sender:profiles(full_name, role)
            `)
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Update thread's last_message_at
          await supabase
            .from('threads')
            .update({ last_message_at: new Date().toISOString() })
            .eq('id', messageData.thread_id)

          return new Response(JSON.stringify(message), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'mark-read': {
        if (req.method === 'POST') {
          const body = await req.json()
          const { message_ids } = body

          if (!Array.isArray(message_ids) || message_ids.length === 0) {
            return new Response('message_ids array required', { 
              status: 400, 
              headers: corsHeaders 
            })
          }

          const { error } = await supabase
            .from('messages')
            .update({ read_at: new Date().toISOString() })
            .in('id', message_ids)
            .neq('sender_id', user.id) // Don't mark own messages as read

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({ 
            message: 'Messages marked as read',
            updated_count: message_ids.length
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'notifications': {
        if (req.method === 'GET') {
          let query = supabase
            .from('notifications')
            .select(`
              *,
              patient:patients(id, full_name, code)
            `)
            .order('created_at', { ascending: false })

          // If user is a patient, only show their own notifications
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
            // Staff can see all notifications for patients in their org
            query = query.in('patient_id', 
              supabaseAdmin
                .from('patients')
                .select('id')
                .eq('org_id', profile.org_id)
            )
          }

          const { data: notifications, error } = await query

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(notifications), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          if (!['admin', 'practitioner'].includes(profile.role)) {
            return new Response('Insufficient permissions', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const notificationData = NotificationCreateSchema.parse(body)

          const { data: notification, error } = await supabase
            .from('notifications')
            .insert({
              ...notificationData,
              status: 'queued'
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

          // In a real implementation, you would trigger the notification service here
          // For now, we'll just mark it as sent
          await supabase
            .from('notifications')
            .update({ 
              status: 'sent',
              sent_at: new Date().toISOString()
            })
            .eq('id', notification.id)

          return new Response(JSON.stringify({
            ...notification,
            status: 'sent'
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'segments': {
        if (req.method === 'GET') {
          if (profile.role !== 'admin') {
            return new Response('Admin access required', { status: 403, headers: corsHeaders })
          }

          const { data: segments, error } = await supabase
            .from('segments')
            .select('*')
            .eq('org_id', profile.org_id)
            .order('name')

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(segments), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          if (profile.role !== 'admin') {
            return new Response('Admin access required', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const segmentData = SegmentCreateSchema.parse(body)

          const { data: segment, error } = await supabase
            .from('segments')
            .insert({
              ...segmentData,
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

          return new Response(JSON.stringify(segment), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'campaigns': {
        if (req.method === 'GET') {
          if (profile.role !== 'admin') {
            return new Response('Admin access required', { status: 403, headers: corsHeaders })
          }

          const { data: campaigns, error } = await supabase
            .from('campaigns')
            .select(`
              *,
              segment:segments(name, definition)
            `)
            .eq('org_id', profile.org_id)
            .order('created_at', { ascending: false })

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(campaigns), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          if (profile.role !== 'admin') {
            return new Response('Admin access required', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const campaignData = CampaignCreateSchema.parse(body)

          const { data: campaign, error } = await supabase
            .from('campaigns')
            .insert({
              ...campaignData,
              org_id: profile.org_id,
              status: 'draft'
            })
            .select(`
              *,
              segment:segments(name, definition)
            `)
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify(campaign), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        break
      }

      case 'send-campaign': {
        if (req.method === 'POST') {
          if (profile.role !== 'admin') {
            return new Response('Admin access required', { status: 403, headers: corsHeaders })
          }

          const body = await req.json()
          const { campaign_id } = body

          if (!campaign_id) {
            return new Response('campaign_id required', { status: 400, headers: corsHeaders })
          }

          // Get campaign details
          const { data: campaign, error: campaignError } = await supabase
            .from('campaigns')
            .select(`
              *,
              segment:segments(definition)
            `)
            .eq('id', campaign_id)
            .eq('org_id', profile.org_id)
            .single()

          if (campaignError || !campaign) {
            return new Response('Campaign not found', { status: 404, headers: corsHeaders })
          }

          // Get patients based on segment (simplified - in reality, you'd evaluate the segment definition)
          let patientsQuery = supabaseAdmin
            .from('patients')
            .select('id, full_name, email')
            .eq('org_id', profile.org_id)
            .is('deleted_at', null)

          const { data: patients } = await patientsQuery

          if (!patients || patients.length === 0) {
            return new Response(JSON.stringify({ 
              message: 'No patients found for campaign',
              sent_count: 0
            }), {
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Create notifications for each patient
          const notifications = patients.map(patient => ({
            patient_id: patient.id,
            channel: campaign.channel,
            title: campaign.metadata?.title || `Message from ${profile.full_name}`,
            body: campaign.metadata?.body || 'You have a new message from your healthcare provider',
            data: { campaign_id: campaign.id }
          }))

          const { error: notificationError } = await supabaseAdmin
            .from('notifications')
            .insert(notifications)

          if (notificationError) {
            return new Response(JSON.stringify({ error: notificationError.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          // Update campaign status
          await supabase
            .from('campaigns')
            .update({ 
              status: 'sent',
              sent_count: patients.length
            })
            .eq('id', campaign_id)

          return new Response(JSON.stringify({
            message: 'Campaign sent successfully',
            sent_count: patients.length,
            campaign_id
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
    console.error('Messaging function error:', error)
    return new Response(JSON.stringify({ 
      error: error.message || 'Internal server error' 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})