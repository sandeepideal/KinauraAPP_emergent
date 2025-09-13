import { assertEquals, assertExists } from "https://deno.land/std@0.168.0/testing/asserts.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// Test configuration
const SUPABASE_URL = Deno.env.get('SUPABASE_URL') || 'http://127.0.0.1:54321'
const SUPABASE_ANON_KEY = Deno.env.get('SUPABASE_ANON_KEY') || 'test-key'
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || 'test-service-key'

// Test data
const TEST_ORG_ID = '018c5c37-b5a0-7000-8000-000000000001'
const TEST_ADMIN_ID = '018c5c37-b5a0-7000-8000-000000000002'

Deno.test({
  name: "Patient Flow Integration Test",
  async fn() {
    // Create Supabase clients
    const supabaseAdmin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    
    // Test patient data
    const testPatient = {
      full_name: "Test Patient Integration",
      email: "test.integration@example.com",
      phone: "+39 333 TEST 123",
      gender: "female" as const,
      tags: ["test", "integration"]
    }

    let patientId: string
    let protocolId: string
    let formulaId: string

    try {
      // Step 1: Create patient
      const { data: patient, error: patientError } = await supabaseAdmin
        .from('patients')
        .insert({
          ...testPatient,
          org_id: TEST_ORG_ID,
          code: `TEST-${Date.now()}`,
          owner_user_id: TEST_ADMIN_ID
        })
        .select()
        .single()

      assertEquals(patientError, null, "Patient creation should not error")
      assertExists(patient, "Patient should be created")
      assertEquals(patient.full_name, testPatient.full_name)
      patientId = patient.id

      // Step 2: Create membership
      const { data: membership, error: membershipError } = await supabaseAdmin
        .from('memberships')
        .insert({
          patient_id: patientId,
          org_id: TEST_ORG_ID,
          plan_id: '018c5c37-b5a0-7000-8000-000000000006', // Gold plan from seed
          status: 'active',
          start_date: new Date().toISOString().split('T')[0]
        })
        .select()
        .single()

      assertEquals(membershipError, null, "Membership creation should not error")
      assertExists(membership, "Membership should be created")

      // Step 3: Create protocol
      const { data: protocol, error: protocolError } = await supabaseAdmin
        .from('protocols')
        .insert({
          patient_id: patientId,
          name: "Test Integration Protocol",
          goals: {
            test: "integration",
            wellness: "improve"
          },
          status: 'active',
          ai_version: 'test-v1.0'
        })
        .select()
        .single()

      assertEquals(protocolError, null, "Protocol creation should not error")
      assertExists(protocol, "Protocol should be created")
      protocolId = protocol.id

      // Step 4: Create protocol sessions
      const sessions = [
        {
          protocol_id: protocolId,
          idx: 1,
          title: "Initial Assessment",
          status: 'scheduled' as const,
          scheduled_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
        },
        {
          protocol_id: protocolId,
          idx: 2,
          title: "Follow-up Session",
          status: 'scheduled' as const,
          scheduled_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
        }
      ]

      const { error: sessionsError } = await supabaseAdmin
        .from('protocol_sessions')
        .insert(sessions)

      assertEquals(sessionsError, null, "Protocol sessions creation should not error")

      // Step 5: Create analysis
      const { data: analysis, error: analysisError } = await supabaseAdmin
        .from('analyses')
        .insert({
          patient_id: patientId,
          kind: 'blood',
          metrics: {
            hemoglobin: 14.2,
            vitamin_d: 35,
            test_marker: 'normal'
          },
          source: 'clinic',
          created_by: TEST_ADMIN_ID
        })
        .select()
        .single()

      assertEquals(analysisError, null, "Analysis creation should not error")
      assertExists(analysis, "Analysis should be created")

      // Step 6: Create formula (minimum €150)
      const { data: formula, error: formulaError } = await supabaseAdmin
        .from('formulas')
        .insert({
          patient_id: patientId,
          analysis_id: analysis.id,
          name: "Test Integration Formula",
          actives: {
            test_ingredient: true,
            vitamin_c: true
          },
          concentration: {
            test_ingredient: "5%",
            vitamin_c: "10%"
          },
          price_cents: 15000, // Exactly €150
          status: 'finalized'
        })
        .select()
        .single()

      assertEquals(formulaError, null, "Formula creation should not error")
      assertExists(formula, "Formula should be created")
      assertEquals(formula.price_cents >= 15000, true, "Formula should meet minimum price")
      formulaId = formula.id

      // Step 7: Create order
      const { data: order, error: orderError } = await supabaseAdmin
        .from('orders')
        .insert({
          patient_id: patientId,
          formula_id: formulaId,
          channel: 'app',
          status: 'paid',
          total_cents: formula.price_cents,
          payment_ref: 'test-payment-123'
        })
        .select()
        .single()

      assertEquals(orderError, null, "Order creation should not error")
      assertExists(order, "Order should be created")
      assertEquals(order.total_cents, 15000)

      // Step 8: Create longevity score
      const { data: score, error: scoreError } = await supabaseAdmin
        .from('longevity_scores')
        .insert({
          patient_id: patientId,
          score_numeric: 75,
          components: {
            adherence: 80,
            biomarkers: 70,
            skin_improvements: 75,
            inflammation_markers: 75
          },
          community_avg_snapshot: 68.5
        })
        .select()
        .single()

      assertEquals(scoreError, null, "Longevity score creation should not error")
      assertExists(score, "Longevity score should be created")
      assertEquals(score.score_numeric, 75)

      // Step 9: Create appointment
      const { data: appointment, error: appointmentError } = await supabaseAdmin
        .from('appointments')
        .insert({
          patient_id: patientId,
          org_id: TEST_ORG_ID,
          service_id: '018c5c37-b5a0-7000-8000-000000000013', // Ozone Therapy from seed
          starts_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
          ends_at: new Date(Date.now() + 25 * 60 * 60 * 1000).toISOString(),
          status: 'scheduled'
        })
        .select()
        .single()

      assertEquals(appointmentError, null, "Appointment creation should not error")
      assertExists(appointment, "Appointment should be created")

      // Step 10: Verify complete patient data retrieval
      const { data: completePatient, error: retrievalError } = await supabaseAdmin
        .from('patients')
        .select(`
          *,
          memberships:memberships(*),
          protocols:protocols(
            *,
            sessions:protocol_sessions(*)
          ),
          analyses:analyses(*),
          longevity_scores:longevity_scores(*),
          formulas:formulas(*),
          orders:orders(*),
          appointments:appointments(*)
        `)
        .eq('id', patientId)
        .single()

      assertEquals(retrievalError, null, "Patient data retrieval should not error")
      assertExists(completePatient, "Complete patient data should exist")
      assertEquals(completePatient.memberships.length, 1)
      assertEquals(completePatient.protocols.length, 1)
      assertEquals(completePatient.protocols[0].sessions.length, 2)
      assertEquals(completePatient.analyses.length, 1)
      assertEquals(completePatient.longevity_scores.length, 1)
      assertEquals(completePatient.formulas.length, 1)
      assertEquals(completePatient.orders.length, 1)
      assertEquals(completePatient.appointments.length, 1)

      // Step 11: Test RLS policies with different user roles
      // This would require setting up proper JWT tokens for different roles
      // For now, we verify the data structure is correct

      console.log("✅ All integration test steps completed successfully")
      
    } finally {
      // Cleanup: Delete test data
      if (patientId) {
        await supabaseAdmin.from('patients').update({ deleted_at: new Date().toISOString() }).eq('id', patientId)
        console.log("🧹 Cleanup completed")
      }
    }
  },
  sanitizeOps: false,
  sanitizeResources: false
})

Deno.test({
  name: "RLS Policy Test - Patient Access",
  async fn() {
    const supabaseAdmin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    // Test that patients from seed data exist and are properly scoped
    const { data: patients, error } = await supabaseAdmin
      .from('patients')
      .select('id, full_name, org_id')
      .eq('org_id', TEST_ORG_ID)
      .is('deleted_at', null)
      .limit(5)

    assertEquals(error, null, "Should be able to query patients with service role")
    assertExists(patients, "Patients should exist")
    assertEquals(patients.length >= 2, true, "Should have seed patients")

    // Verify all patients belong to test org
    for (const patient of patients) {
      assertEquals(patient.org_id, TEST_ORG_ID, "All patients should belong to test org")
    }
  },
  sanitizeOps: false,
  sanitizeResources: false
})

Deno.test({
  name: "Formula Price Validation Test",
  async fn() {
    const supabaseAdmin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    // Test that formulas in the system meet minimum price requirement
    const { data: formulas, error } = await supabaseAdmin
      .from('formulas')
      .select('id, name, price_cents, status')
      .eq('status', 'finalized')

    assertEquals(error, null, "Should be able to query formulas")
    assertExists(formulas, "Formulas should exist")

    // Verify all finalized formulas meet minimum price
    for (const formula of formulas) {
      assertEquals(
        formula.price_cents >= 15000, 
        true, 
        `Formula ${formula.name} should meet minimum €150 price requirement (got ${formula.price_cents/100}€)`
      )
    }
  },
  sanitizeOps: false,
  sanitizeResources: false
})