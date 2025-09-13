import { assertEquals } from "https://deno.land/std@0.168.0/testing/asserts.ts"

// Longevity score computation logic (extracted from clinical function)
function computeLongevityScore(components: {
  adherence: number
  biomarkers: number
  skinImprovements: number
  inflammationMarkers: number
  membershipTier?: string
}) {
  const { adherence, biomarkers, skinImprovements, inflammationMarkers, membershipTier } = components

  // Validate input ranges (0-100)
  if (adherence < 0 || adherence > 100) throw new Error('Adherence must be 0-100')
  if (biomarkers < 0 || biomarkers > 100) throw new Error('Biomarkers must be 0-100')
  if (skinImprovements < 0 || skinImprovements > 100) throw new Error('Skin improvements must be 0-100')
  if (inflammationMarkers < 0 || inflammationMarkers > 100) throw new Error('Inflammation markers must be 0-100')

  // Weighted calculation
  const adherenceWeight = 0.3  // 30%
  const biomarkersWeight = 0.3 // 30%
  const skinWeight = 0.2       // 20%
  const inflammationWeight = 0.2 // 20%

  const baseScore = (
    adherence * adherenceWeight +
    biomarkers * biomarkersWeight +
    skinImprovements * skinWeight +
    inflammationMarkers * inflammationWeight
  )

  // Membership tier bonus
  let membershipBonus = 0
  switch (membershipTier) {
    case 'gold':
      membershipBonus = 2
      break
    case 'platinum':
      membershipBonus = 3
      break
    case 'elite':
      membershipBonus = 5
      break
  }

  const finalScore = Math.min(Math.round(baseScore + membershipBonus), 100)

  return {
    score_numeric: finalScore,
    components: {
      adherence,
      biomarkers,
      skin_improvements: skinImprovements,
      inflammation_markers: inflammationMarkers
    },
    membership_bonus: membershipBonus,
    base_score: Math.round(baseScore)
  }
}

Deno.test("Longevity Score - Perfect scores", () => {
  const result = computeLongevityScore({
    adherence: 100,
    biomarkers: 100,
    skinImprovements: 100,
    inflammationMarkers: 100
  })

  assertEquals(result.score_numeric, 100)
  assertEquals(result.base_score, 100)
  assertEquals(result.membership_bonus, 0)
})

Deno.test("Longevity Score - Average performance", () => {
  const result = computeLongevityScore({
    adherence: 75,
    biomarkers: 70,
    skinImprovements: 80,
    inflammationMarkers: 65
  })

  // Expected: 75*0.3 + 70*0.3 + 80*0.2 + 65*0.2 = 22.5 + 21 + 16 + 13 = 72.5 -> 73
  assertEquals(result.score_numeric, 73)
  assertEquals(result.base_score, 73)
})

Deno.test("Longevity Score - Elite membership bonus", () => {
  const result = computeLongevityScore({
    adherence: 85,
    biomarkers: 80,
    skinImprovements: 75,
    inflammationMarkers: 90,
    membershipTier: 'elite'
  })

  // Expected base: 85*0.3 + 80*0.3 + 75*0.2 + 90*0.2 = 25.5 + 24 + 15 + 18 = 82.5 -> 83
  // With elite bonus: 83 + 5 = 88
  assertEquals(result.score_numeric, 88)
  assertEquals(result.membership_bonus, 5)
  assertEquals(result.base_score, 83)
})

Deno.test("Longevity Score - Platinum membership bonus", () => {
  const result = computeLongevityScore({
    adherence: 90,
    biomarkers: 85,
    skinImprovements: 88,
    inflammationMarkers: 92,
    membershipTier: 'platinum'
  })

  // High scores with platinum bonus
  assertEquals(result.membership_bonus, 3)
  assertEquals(result.score_numeric <= 100, true) // Should not exceed 100
})

Deno.test("Longevity Score - Gold membership bonus", () => {
  const result = computeLongevityScore({
    adherence: 70,
    biomarkers: 65,
    skinImprovements: 75,
    inflammationMarkers: 80,
    membershipTier: 'gold'
  })

  assertEquals(result.membership_bonus, 2)
})

Deno.test("Longevity Score - Score capped at 100", () => {
  const result = computeLongevityScore({
    adherence: 98,
    biomarkers: 97,
    skinImprovements: 99,
    inflammationMarkers: 96,
    membershipTier: 'elite'
  })

  // Even with perfect scores + elite bonus, should not exceed 100
  assertEquals(result.score_numeric, 100)
})

Deno.test("Longevity Score - Low scores", () => {
  const result = computeLongevityScore({
    adherence: 20,
    biomarkers: 30,
    skinImprovements: 25,
    inflammationMarkers: 35
  })

  // Expected: 20*0.3 + 30*0.3 + 25*0.2 + 35*0.2 = 6 + 9 + 5 + 7 = 27
  assertEquals(result.score_numeric, 27)
})

Deno.test("Longevity Score - Invalid input ranges", () => {
  // Test negative values
  try {
    computeLongevityScore({
      adherence: -5,
      biomarkers: 80,
      skinImprovements: 75,
      inflammationMarkers: 85
    })
    assertEquals(false, true, "Should have thrown error")
  } catch (error) {
    assertEquals(error.message, "Adherence must be 0-100")
  }

  // Test values over 100
  try {
    computeLongevityScore({
      adherence: 85,
      biomarkers: 105,
      skinImprovements: 75,
      inflammationMarkers: 85
    })
    assertEquals(false, true, "Should have thrown error")
  } catch (error) {
    assertEquals(error.message, "Biomarkers must be 0-100")
  }
})

Deno.test("Longevity Score - Edge cases", () => {
  // Test with zeros
  const zeroResult = computeLongevityScore({
    adherence: 0,
    biomarkers: 0,
    skinImprovements: 0,
    inflammationMarkers: 0
  })
  assertEquals(zeroResult.score_numeric, 0)

  // Test with mixed extreme values
  const mixedResult = computeLongevityScore({
    adherence: 100,
    biomarkers: 0,
    skinImprovements: 100,
    inflammationMarkers: 0
  })
  // Expected: 100*0.3 + 0*0.3 + 100*0.2 + 0*0.2 = 30 + 0 + 20 + 0 = 50
  assertEquals(mixedResult.score_numeric, 50)
})