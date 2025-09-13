import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'
import { z } from "https://deno.land/x/zod@v3.16.1/mod.ts"

// Validation schemas
const CreateQuestionnaireSchema = z.object({
  title: z.string().min(1).max(255),
  description: z.string().optional(),
  category: z.enum(['medical_history', 'privacy_disclosure', 'treatment_consent', 
    'pre_treatment', 'post_treatment', 'wellness_assessment', 'lifestyle', 
    'symptoms', 'preferences', 'other']),
  is_required: z.boolean().default(false),
  instructions: z.string().optional(),
  metadata: z.record(z.any()).default({})
})

const CreateQuestionSchema = z.object({
  questionnaire_id: z.string().uuid(),
  question_text: z.string().min(1),
  question_type: z.enum(['multiple_choice', 'single_choice', 'text', 'long_text', 
    'number', 'date', 'yes_no', 'rating_scale', 'file_upload']),
  is_required: z.boolean().default(false),
  order_index: z.number().int().min(0).default(0),
  options: z.record(z.any()).optional(),
  validation: z.record(z.any()).optional(),
  help_text: z.string().optional()
})

const AssignQuestionnaireSchema = z.object({
  questionnaire_id: z.string().uuid(),
  patient_id: z.string().uuid(),
  due_date: z.string().datetime().optional(),
  context: z.record(z.any()).optional()
})

const UpdateQuestionnaireStatusSchema = z.object({
  patient_questionnaire_id: z.string().uuid(),
  status: z.enum(['assigned', 'in_progress', 'completed', 'cancelled']),
  started_at: z.string().datetime().optional(),
  completed_at: z.string().datetime().optional()
})

const SubmitAnswersSchema = z.object({
  patient_questionnaire_id: z.string().uuid(),
  answers: z.array(z.object({
    question_id: z.string().uuid(),
    answer_text: z.string().optional(),
    answer_number: z.number().optional(),
    answer_date: z.string().date().optional(),
    answer_choices: z.array(z.string()).optional(),
    answer_files: z.array(z.record(z.any())).optional()
  }))
})

const CreateDocumentSchema = z.object({
  title: z.string().min(1).max(255),
  document_type: z.enum(['consent_form', 'privacy_notice', 'treatment_info', 'waiver', 
    'terms_conditions', 'medical_disclosure', 'financial_agreement', 'other']),
  content: z.string().min(1),
  version: z.string().default('1.0'),
  requires_signature: z.boolean().default(true),
  settings: z.record(z.any()).default({})
})

const AssignDocumentSchema = z.object({
  document_id: z.string().uuid(),
  patient_id: z.string().uuid(),
  expires_in_days: z.number().int().min(1).optional(),
  context: z.record(z.any()).optional()
})

const SignDocumentSchema = z.object({
  patient_document_id: z.string().uuid(),
  signature_data: z.string(),
  signature_type: z.enum(['canvas', 'typed', 'uploaded', 'electronic']).default('canvas')
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

    // Helper function to check admin/practitioner role
    const requireStaff = async (user: any) => {
      const { data: profile } = await supabase
        .from('profiles')
        .select('role, org_id')
        .eq('id', user.id)
        .single()

      if (!profile || !['admin', 'practitioner'].includes(profile.role)) {
        throw new Error('Admin or practitioner access required')
      }

      return profile
    }

    switch (endpoint) {
      case 'questionnaires': {
        if (req.method === 'GET') {
          const user = await getAuthUser()
          const profile = await requireStaff(user)

          const { data: questionnaires, error } = await supabase
            .from('questionnaires')
            .select(`
              *,
              questions:questions(count),
              assignments:patient_questionnaires(count)
            `)
            .eq('org_id', profile.org_id)
            .eq('is_active', true)
            .order('created_at', { ascending: false })

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({ questionnaires }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          const user = await getAuthUser()
          const profile = await requireStaff(user)

          const body = await req.json()
          const questionnaireData = CreateQuestionnaireSchema.parse(body)

          const { data: questionnaire, error } = await supabase
            .from('questionnaires')
            .insert({
              ...questionnaireData,
              org_id: profile.org_id,
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

          return new Response(JSON.stringify({ 
            success: true, 
            questionnaire 
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response('Method not allowed', { status: 405, headers: corsHeaders })
      }

      case 'questions': {
        if (req.method === 'POST') {
          const user = await getAuthUser()
          await requireStaff(user)

          const body = await req.json()
          const questionData = CreateQuestionSchema.parse(body)

          const { data: question, error } = await supabase
            .from('questions')
            .insert(questionData)
            .select()
            .single()

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({ 
            success: true, 
            question 
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response('Method not allowed', { status: 405, headers: corsHeaders })
      }

      case 'assign-questionnaire': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()
        await requireStaff(user)

        const body = await req.json()
        const { questionnaire_id, patient_id, due_date, context } = AssignQuestionnaireSchema.parse(body)

        const { data: assignmentId, error } = await supabase.rpc(
          'assign_questionnaire_to_patient',
          {
            questionnaire_id_param: questionnaire_id,
            patient_id_param: patient_id,
            assigned_by_param: user.id,
            due_date_param: due_date || null,
            context_param: context || {}
          }
        )

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({
          success: true,
          assignment_id: assignmentId,
          message: 'Questionnaire assigned successfully'
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'my-questionnaires': {
        if (req.method !== 'GET') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()

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

        const { data: questionnaires, error } = await supabase
          .from('patient_questionnaires')
          .select(`
            id,
            status,
            assigned_at,
            due_date,
            started_at,
            completed_at,
            questionnaire:questionnaires(
              id,
              title,
              description,
              category,
              instructions
            )
          `)
          .eq('patient_id', patient.id)
          .in('status', ['assigned', 'in_progress'])
          .order('assigned_at', { ascending: true })

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({ questionnaires }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'questionnaire-data': {
        if (req.method !== 'GET') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()
        const questionnaireId = url.searchParams.get('id')

        if (!questionnaireId) {
          return new Response(JSON.stringify({ 
            error: 'Questionnaire ID required' 
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        const { data: questionnaireData, error } = await supabase.rpc(
          'get_patient_questionnaire_data',
          { patient_questionnaire_id_param: questionnaireId }
        )

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (!questionnaireData || questionnaireData.length === 0) {
          return new Response(JSON.stringify({ 
            error: 'Questionnaire not found or access denied' 
          }), {
            status: 404,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Group by questionnaire info and questions
        const result = {
          questionnaire: {
            title: questionnaireData[0].questionnaire_title,
            description: questionnaireData[0].questionnaire_description,
            instructions: questionnaireData[0].questionnaire_instructions
          },
          questions: questionnaireData.map((q: any) => ({
            id: q.question_id,
            text: q.question_text,
            type: q.question_type,
            required: q.is_required,
            order: q.order_index,
            options: q.options,
            help_text: q.help_text,
            current_answer: {
              text: q.current_answer_text,
              choices: q.current_answer_choices,
              number: q.current_answer_number,
              date: q.current_answer_date,
              answered_at: q.answered_at
            }
          }))
        }

        return new Response(JSON.stringify(result), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'update-questionnaire-status': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()
        const body = await req.json()
        const { patient_questionnaire_id, status, started_at, completed_at } = UpdateQuestionnaireStatusSchema.parse(body)

        const updateData: any = { status }
        if (started_at) updateData.started_at = started_at
        if (completed_at) updateData.completed_at = completed_at

        const { error } = await supabase
          .from('patient_questionnaires')
          .update(updateData)
          .eq('id', patient_questionnaire_id)

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({
          success: true,
          message: 'Status updated successfully'
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'submit-answers': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()
        const body = await req.json()
        const { patient_questionnaire_id, answers } = SubmitAnswersSchema.parse(body)

        // Insert or update answers
        const answersToUpsert = answers.map(answer => ({
          patient_questionnaire_id,
          question_id: answer.question_id,
          answer_text: answer.answer_text,
          answer_number: answer.answer_number,
          answer_date: answer.answer_date,
          answer_choices: answer.answer_choices,
          answer_files: answer.answer_files,
          answered_at: new Date().toISOString()
        }))

        const { error: answersError } = await supabase
          .from('patient_answers')
          .upsert(answersToUpsert, { 
            onConflict: 'patient_questionnaire_id,question_id'
          })

        if (answersError) {
          return new Response(JSON.stringify({ error: answersError.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({
          success: true,
          message: 'Answers submitted successfully'
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'documents': {
        if (req.method === 'GET') {
          const user = await getAuthUser()
          const profile = await requireStaff(user)

          const { data: documents, error } = await supabase
            .from('documents')
            .select(`
              *,
              assignments:patient_documents(count)
            `)
            .eq('org_id', profile.org_id)
            .eq('is_active', true)
            .order('created_at', { ascending: false })

          if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
              status: 400,
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            })
          }

          return new Response(JSON.stringify({ documents }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        if (req.method === 'POST') {
          const user = await getAuthUser()
          const profile = await requireStaff(user)

          const body = await req.json()
          const documentData = CreateDocumentSchema.parse(body)

          const { data: document, error } = await supabase
            .from('documents')
            .insert({
              ...documentData,
              org_id: profile.org_id,
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

          return new Response(JSON.stringify({ 
            success: true, 
            document 
          }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response('Method not allowed', { status: 405, headers: corsHeaders })
      }

      case 'assign-document': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()
        await requireStaff(user)

        const body = await req.json()
        const { document_id, patient_id, expires_in_days, context } = AssignDocumentSchema.parse(body)

        const { data: assignmentId, error } = await supabase.rpc(
          'assign_document_to_patient',
          {
            document_id_param: document_id,
            patient_id_param: patient_id,
            assigned_by_param: user.id,
            expires_in_days: expires_in_days || null,
            context_param: context || {}
          }
        )

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({
          success: true,
          assignment_id: assignmentId,
          message: 'Document assigned successfully'
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'my-documents': {
        if (req.method !== 'GET') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()

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

        const { data: documents, error } = await supabase
          .from('patient_documents')
          .select(`
            id,
            status,
            assigned_at,
            viewed_at,
            signed_at,
            expires_at,
            document:documents(
              id,
              title,
              document_type,
              content,
              version,
              requires_signature
            )
          `)
          .eq('patient_id', patient.id)
          .in('status', ['assigned', 'viewed'])
          .order('assigned_at', { ascending: true })

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({ documents }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'sign-document': {
        if (req.method !== 'POST') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()
        const body = await req.json()
        const { patient_document_id, signature_data, signature_type } = SignDocumentSchema.parse(body)

        // Get patient ID
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

        // Create signature record
        const { data: signature, error: signatureError } = await supabase
          .from('patient_signatures')
          .insert({
            patient_document_id,
            patient_id: patient.id,
            signature_data,
            signature_type,
            ip_address: req.headers.get('x-forwarded-for') || 'unknown',
            user_agent: req.headers.get('user-agent') || 'unknown',
            verification_data: {
              timestamp: new Date().toISOString(),
              user_id: user.id
            }
          })
          .select()
          .single()

        if (signatureError) {
          return new Response(JSON.stringify({ error: signatureError.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Update document status to signed
        const { error: updateError } = await supabase
          .from('patient_documents')
          .update({
            status: 'signed',
            signed_at: new Date().toISOString()
          })
          .eq('id', patient_document_id)

        if (updateError) {
          return new Response(JSON.stringify({ error: updateError.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({
          success: true,
          signature_id: signature.id,
          message: 'Document signed successfully'
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'patient-responses': {
        if (req.method !== 'GET') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()
        await requireStaff(user)

        const patientId = url.searchParams.get('patient_id')
        const questionnaireId = url.searchParams.get('questionnaire_id')

        if (!patientId) {
          return new Response(JSON.stringify({ 
            error: 'Patient ID required' 
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        const { data: responses, error } = await supabase.rpc(
          'get_patient_questionnaire_responses',
          {
            patient_id_param: patientId,
            questionnaire_id_param: questionnaireId || null
          }
        )

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({ responses }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      case 'pending-tasks': {
        if (req.method !== 'GET') {
          return new Response('Method not allowed', { status: 405, headers: corsHeaders })
        }

        const user = await getAuthUser()

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

        const { data: tasks, error } = await supabase.rpc(
          'get_patient_pending_tasks',
          { patient_id_param: patient.id }
        )

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({ tasks }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      default:
        return new Response('Not found', { status: 404, headers: corsHeaders })
    }
  } catch (error) {
    console.error('Questionnaire function error:', error)
    return new Response(JSON.stringify({ 
      error: error.message || 'Internal server error' 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})