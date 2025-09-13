import { assertEquals, assertThrows } from "https://deno.land/std@0.168.0/testing/asserts.ts"
import { z } from "https://deno.land/x/zod@v3.16.1/mod.ts"

// Import validation schemas from Edge Functions
const CreatePatientSchema = z.object({
  full_name: z.string().min(1),
  email: z.string().email().optional(),
  phone: z.string().optional(),
  dob: z.string().optional(),
  gender: z.enum(['male', 'female', 'other', 'prefer_not_to_say']).optional(),
  country: z.string().default('IT'),
  tags: z.array(z.string()).default([])
})

const CreateFormulaSchema = z.object({
  patient_id: z.string().uuid(),
  analysis_id: z.string().uuid().optional(),
  name: z.string().min(1),
  actives: z.record(z.unknown()),
  concentration: z.record(z.unknown()),
  fragrance: z.string().optional(),
  packaging: z.enum(['tube', 'jar', 'bottle', 'serum_bottle']).default('jar')
})

const FinalizeFormulaSchema = z.object({
  formula_id: z.string().uuid(),
  price_cents: z.number().min(15000) // Minimum €150
})

Deno.test("Patient validation - valid data", () => {
  const validPatient = {
    full_name: "Elena Verdi",
    email: "elena.verdi@example.com",
    phone: "+39 347 123 4567",
    gender: "female" as const,
    tags: ["anti-aging", "wellness"]
  }

  const result = CreatePatientSchema.parse(validPatient)
  assertEquals(result.full_name, "Elena Verdi")
  assertEquals(result.country, "IT") // Default value
  assertEquals(result.tags.length, 2)
})

Deno.test("Patient validation - invalid email", () => {
  const invalidPatient = {
    full_name: "Elena Verdi",
    email: "not-an-email",
    tags: []
  }

  assertThrows(
    () => CreatePatientSchema.parse(invalidPatient),
    Error,
    "Invalid email"
  )
})

Deno.test("Patient validation - missing required fields", () => {
  const invalidPatient = {
    email: "elena@example.com"
    // Missing full_name
  }

  assertThrows(
    () => CreatePatientSchema.parse(invalidPatient),
    Error
  )
})

Deno.test("Formula validation - valid data", () => {
  const validFormula = {
    patient_id: "018c5c37-b5a0-7000-8000-000000000009",
    name: "Custom Anti-Aging Serum",
    actives: {
      retinoid_complex: true,
      vitamin_c: true
    },
    concentration: {
      retinoid: "0.5%",
      vitamin_c: "15%"
    }
  }

  const result = CreateFormulaSchema.parse(validFormula)
  assertEquals(result.name, "Custom Anti-Aging Serum")
  assertEquals(result.packaging, "jar") // Default value
})

Deno.test("Formula validation - invalid UUID", () => {
  const invalidFormula = {
    patient_id: "not-a-uuid",
    name: "Custom Serum",
    actives: {},
    concentration: {}
  }

  assertThrows(
    () => CreateFormulaSchema.parse(invalidFormula),
    Error,
    "Invalid uuid"
  )
})

Deno.test("Formula finalization - minimum price validation", () => {
  const validFinalization = {
    formula_id: "018c5c37-b5a0-7000-8000-000000000032",
    price_cents: 15000 // Exactly €150
  }

  const result = FinalizeFormulaSchema.parse(validFinalization)
  assertEquals(result.price_cents, 15000)
})

Deno.test("Formula finalization - price below minimum", () => {
  const invalidFinalization = {
    formula_id: "018c5c37-b5a0-7000-8000-000000000032",
    price_cents: 14999 // Below €150
  }

  assertThrows(
    () => FinalizeFormulaSchema.parse(invalidFinalization),
    Error,
    "Number must be greater than or equal to 15000"
  )
})

Deno.test("Formula finalization - high price accepted", () => {
  const validFinalization = {
    formula_id: "018c5c37-b5a0-7000-8000-000000000032",
    price_cents: 50000 // €500 - should be allowed
  }

  const result = FinalizeFormulaSchema.parse(validFinalization)
  assertEquals(result.price_cents, 50000)
})