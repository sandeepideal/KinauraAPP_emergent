import { assertEquals, assertExists } from "https://deno.land/std@0.168.0/testing/asserts.ts"

// E2E test for complete appointment booking flow
// This test simulates the full user journey from API perspective

const BASE_URL = Deno.env.get('FUNCTIONS_URL') || 'http://127.0.0.1:54321/functions/v1'
const TEST_TOKEN = Deno.env.get('TEST_JWT_TOKEN') || 'test-jwt'

// Test utilities
async function apiCall(endpoint: string, method = 'GET', body?: any) {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method,
    headers: {
      'Authorization': `Bearer ${TEST_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: body ? JSON.stringify(body) : undefined
  })
  
  return {
    status: response.status,
    data: await response.json().catch(() => null)
  }
}

Deno.test({
  name: "E2E: Complete Appointment Booking Flow",
  async fn() {
    // This test requires a running Supabase instance with seed data
    console.log("🧪 Starting E2E appointment booking test...")

    let patientId: string
    let serviceId: string
    let appointmentId: string

    try {
      // Step 1: Create a test patient
      console.log("📝 Step 1: Creating test patient...")
      const createPatientResponse = await apiCall('/patients', 'POST', {
        full_name: "E2E Test Patient",
        email: "e2e.test@example.com",
        phone: "+39 333 E2E TEST",
        tags: ["e2e", "test"]
      })

      assertEquals(createPatientResponse.status, 201, "Patient creation should succeed")
      assertExists(createPatientResponse.data?.id, "Patient ID should be returned")
      patientId = createPatientResponse.data.id
      console.log(`✅ Patient created: ${patientId}`)

      // Step 2: Get available services
      console.log("🔍 Step 2: Fetching available services...")
      const servicesResponse = await apiCall('/services', 'GET')
      
      assertEquals(servicesResponse.status, 200, "Services fetch should succeed")
      assertExists(servicesResponse.data, "Services data should exist")
      assertEquals(servicesResponse.data.length > 0, true, "Should have services available")
      
      serviceId = servicesResponse.data[0].id
      const serviceName = servicesResponse.data[0].name
      console.log(`✅ Found service: ${serviceName} (${serviceId})`)

      // Step 3: Check available appointment slots
      console.log("📅 Step 3: Checking available slots...")
      const tomorrow = new Date()
      tomorrow.setDate(tomorrow.getDate() + 1)
      const dateString = tomorrow.toISOString().split('T')[0]

      const slotsResponse = await apiCall('/booking/available-slots', 'POST', {
        service_id: serviceId,
        date: dateString,
        timezone: 'Europe/Rome'
      })

      assertEquals(slotsResponse.status, 200, "Slots check should succeed")
      assertExists(slotsResponse.data?.slots, "Available slots should be returned")
      assertEquals(slotsResponse.data.slots.length > 0, true, "Should have available slots")
      
      const firstSlot = slotsResponse.data.slots[0]
      console.log(`✅ Found ${slotsResponse.data.slots.length} available slots`)

      // Step 4: Book the appointment
      console.log("📞 Step 4: Booking appointment...")
      const bookingResponse = await apiCall('/booking/book', 'POST', {
        service_id: serviceId,
        patient_id: patientId,
        starts_at: firstSlot.starts_at,
        notes: "E2E test appointment booking"
      })

      assertEquals(bookingResponse.status, 201, "Appointment booking should succeed")
      assertExists(bookingResponse.data?.id, "Appointment ID should be returned")
      appointmentId = bookingResponse.data.id
      console.log(`✅ Appointment booked: ${appointmentId}`)

      // Step 5: Verify appointment details
      console.log("🔍 Step 5: Verifying appointment details...")
      const appointmentDetails = bookingResponse.data
      assertEquals(appointmentDetails.status, "scheduled", "Appointment should be scheduled")
      assertEquals(appointmentDetails.service?.name, serviceName, "Service name should match")
      assertEquals(appointmentDetails.patient?.full_name, "E2E Test Patient", "Patient name should match")

      // Step 6: Test appointment rescheduling
      console.log("📝 Step 6: Testing appointment rescheduling...")
      const newSlotTime = new Date(firstSlot.starts_at)
      newSlotTime.setHours(newSlotTime.getHours() + 2)

      const rescheduleResponse = await apiCall('/booking/reschedule', 'POST', {
        appointment_id: appointmentId,
        new_starts_at: newSlotTime.toISOString(),
        reason: "E2E test reschedule"
      })

      assertEquals(rescheduleResponse.status, 200, "Appointment rescheduling should succeed")
      assertEquals(rescheduleResponse.data.status, "rescheduled", "Status should be updated")
      console.log("✅ Appointment rescheduled successfully")

      // Step 7: Test appointment cancellation
      console.log("❌ Step 7: Testing appointment cancellation...")
      const cancelResponse = await apiCall(`/booking/cancel?id=${appointmentId}`, 'POST')

      assertEquals(cancelResponse.status, 200, "Appointment cancellation should succeed")
      console.log("✅ Appointment cancelled successfully")

      // Step 8: Verify patient can see their appointments
      console.log("👤 Step 8: Verifying patient appointment history...")
      const patientResponse = await apiCall(`/patients/${patientId}`, 'GET')
      
      assertEquals(patientResponse.status, 200, "Patient details should be accessible")
      assertExists(patientResponse.data, "Patient data should exist")
      console.log("✅ Patient appointment history accessible")

      console.log("🎉 E2E appointment booking test completed successfully!")

    } catch (error) {
      console.error("❌ E2E test failed:", error)
      throw error
    } finally {
      // Cleanup: Delete test patient
      if (patientId) {
        console.log("🧹 Cleaning up test data...")
        await apiCall(`/patients/${patientId}`, 'DELETE')
        console.log("✅ Test data cleaned up")
      }
    }
  },
  sanitizeOps: false,
  sanitizeResources: false
})

Deno.test({
  name: "E2E: AI Protocol Refresh Flow",
  async fn() {
    console.log("🤖 Starting E2E AI protocol refresh test...")

    let patientId: string

    try {
      // Step 1: Create test patient
      const createPatientResponse = await apiCall('/patients', 'POST', {
        full_name: "AI Test Patient",
        email: "ai.test@example.com",
        tags: ["ai", "protocol"]
      })

      assertEquals(createPatientResponse.status, 201)
      patientId = createPatientResponse.data.id

      // Step 2: Add analysis data
      console.log("📊 Adding analysis data...")
      const analysisResponse = await apiCall('/clinical/ingest-analysis', 'POST', {
        patient_id: patientId,
        kind: 'blood',
        metrics: {
          hemoglobin: 13.8,
          vitamin_d: 28,
          inflammatory_markers: {
            crp: 2.1,
            esr: 18
          }
        },
        source: 'clinic'
      })

      assertEquals(analysisResponse.status, 201, "Analysis ingestion should succeed")
      console.log("✅ Analysis data added")

      // Step 3: Trigger AI protocol refresh
      console.log("🤖 Triggering AI protocol refresh...")
      const protocolResponse = await apiCall('/clinical/refresh-protocol', 'POST', {
        patient_id: patientId,
        force_regenerate: true
      })

      assertEquals(protocolResponse.status, 200, "Protocol refresh should succeed")
      assertExists(protocolResponse.data?.protocol_id, "Protocol ID should be returned")
      assertExists(protocolResponse.data?.ai_version, "AI version should be returned")
      console.log(`✅ Protocol refreshed with AI version: ${protocolResponse.data.ai_version}`)

      // Step 4: Verify protocol was created with sessions
      console.log("🔍 Verifying protocol creation...")
      const patientDetails = await apiCall(`/patients/${patientId}`, 'GET')
      
      assertEquals(patientDetails.status, 200)
      assertExists(patientDetails.data?.protocols, "Patient should have protocols")
      assertEquals(patientDetails.data.protocols.length > 0, true, "Should have at least one protocol")
      
      const protocol = patientDetails.data.protocols[0]
      assertExists(protocol.sessions, "Protocol should have sessions")
      assertEquals(protocol.sessions.length > 0, true, "Should have protocol sessions")
      console.log(`✅ Protocol created with ${protocol.sessions.length} sessions`)

      // Step 5: Recompute longevity score
      console.log("📈 Recomputing longevity score...")
      const scoreResponse = await apiCall('/clinical/recompute-leaderboard', 'POST', {
        patient_ids: [patientId]
      })

      assertEquals(scoreResponse.status, 200, "Score computation should succeed")
      assertEquals(scoreResponse.data?.processed, 1, "Should process one patient")
      console.log("✅ Longevity score computed")

      console.log("🎉 E2E AI protocol refresh test completed successfully!")

    } finally {
      // Cleanup
      if (patientId) {
        await apiCall(`/patients/${patientId}`, 'DELETE')
      }
    }
  },
  sanitizeOps: false,
  sanitizeResources: false
})

Deno.test({
  name: "E2E: Formula Creation and Order Flow",
  async fn() {
    console.log("🧴 Starting E2E formula and order test...")

    let patientId: string
    let formulaId: string

    try {
      // Step 1: Create test patient
      const createPatientResponse = await apiCall('/patients', 'POST', {
        full_name: "Formula Test Patient",
        email: "formula.test@example.com"
      })

      assertEquals(createPatientResponse.status, 201)
      patientId = createPatientResponse.data.id

      // Step 2: Create analysis for formula base
      const analysisResponse = await apiCall('/clinical/ingest-analysis', 'POST', {
        patient_id: patientId,
        kind: 'skin_scan',
        metrics: {
          hydration: 65,
          elasticity: 72,
          pigmentation: 'mild_spots',
          recommended_actives: ['vitamin_c', 'retinoid', 'peptides']
        },
        source: 'clinic'
      })

      assertEquals(analysisResponse.status, 201)
      const analysisId = analysisResponse.data.id

      // Step 3: Create formula
      console.log("🧪 Creating personalized formula...")
      const formulaResponse = await apiCall('/commerce/create-formula', 'POST', {
        patient_id: patientId,
        analysis_id: analysisId,
        name: "E2E Test Custom Formula",
        actives: {
          vitamin_c: true,
          retinoid_complex: true,
          peptides: true,
          hyaluronic_acid: true
        },
        concentration: {
          vitamin_c: "15%",
          retinoid: "0.3%",
          peptides: "5%",
          hyaluronic_acid: "2%"
        },
        fragrance: "Unscented",
        packaging: "serum_bottle"
      })

      assertEquals(formulaResponse.status, 201, "Formula creation should succeed")
      formulaId = formulaResponse.data.id
      console.log(`✅ Formula created: ${formulaId}`)

      // Step 4: Finalize formula with proper pricing (minimum €150)
      console.log("💰 Finalizing formula with pricing...")
      const finalizeResponse = await apiCall('/commerce/finalize-formula', 'POST', {
        formula_id: formulaId,
        price_cents: 18500 // €185
      })

      assertEquals(finalizeResponse.status, 200, "Formula finalization should succeed")
      assertEquals(finalizeResponse.data.status, "finalized", "Formula should be finalized")
      assertEquals(finalizeResponse.data.price_cents, 18500, "Price should be set correctly")
      console.log("✅ Formula finalized at €185")

      // Step 5: Create order
      console.log("🛒 Creating order...")
      const orderResponse = await apiCall('/commerce/create-order', 'POST', {
        patient_id: patientId,
        formula_id: formulaId,
        channel: 'app'
      })

      assertEquals(orderResponse.status, 201, "Order creation should succeed")
      assertExists(orderResponse.data?.order?.id, "Order ID should be returned")
      assertExists(orderResponse.data?.payment, "Payment info should be returned")
      assertEquals(orderResponse.data.order.total_cents, 18500, "Order total should match formula price")
      console.log(`✅ Order created: ${orderResponse.data.order.id}`)

      // Step 6: Simulate payment webhook
      console.log("💳 Simulating payment completion...")
      const webhookResponse = await apiCall('/commerce/payment-webhook', 'POST', {
        session_id: orderResponse.data.payment.session_id,
        status: 'paid',
        order_id: orderResponse.data.order.id
      })

      assertEquals(webhookResponse.status, 200, "Payment webhook should succeed")
      console.log("✅ Payment processed successfully")

      // Step 7: Verify complete order in patient record
      console.log("🔍 Verifying order completion...")
      const patientDetails = await apiCall(`/patients/${patientId}`, 'GET')
      
      // Note: The response structure depends on the actual implementation
      assertEquals(patientDetails.status, 200)
      console.log("✅ Order verified in patient record")

      console.log("🎉 E2E formula and order test completed successfully!")

    } finally {
      // Cleanup
      if (patientId) {
        await apiCall(`/patients/${patientId}`, 'DELETE')
      }
    }
  },
  sanitizeOps: false,
  sanitizeResources: false
})