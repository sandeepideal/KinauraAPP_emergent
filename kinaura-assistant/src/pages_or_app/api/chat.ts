import OpenAI from "openai";
import type { NextApiRequest, NextApiResponse } from "next";
import { kbSearchFiltered } from "@/src/lib/search";
import { SYSTEM_PROMPT } from "@/src/lib/systemPrompt";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY! });

const INTENT_SYSTEM = `
Classify the user's query into:
- concerns: array from provided list
- device: one from provided list or null
- language: "en" or "it"
Return strict JSON: {"concerns":["..."],"device":null,"language":"en"}
Concerns: redness,rosacea,pigmentation,sun_damage,pre_event_glow,fine_lines,wrinkles,skin_laxity_face,jawline_neck_contour,texture,acne,acne_scars,pores,cellulite,body_contour,hair_loss,vaginal_rejuvenation,recovery,inflammation,detox,stress_sleep,performance
Devices: VISIA-7,Wellness Tower,Sciton mJOULE (BBL HERO / MOXI / SkinTyte),InMode Ignite (Morpheus8 / FaceTite / BodyTite),MCT (Meta Cell Technology),Emuage Lab,Ultraformer MPT (HIFU),Weberneedle Endolaser,Fotona DYNAMIS MAX (Er:YAG / Nd:YAG),AirPod Revive Hydroxy (mHBOT + H2),Ammortal Chamber (PEMF/PEF + PBM + H2 + Vibro-Acoustic),HydraFacial Syndeo MD
`;

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") return res.status(405).json({ error: "Method not allowed" });
  const { messages, locale = "it" } = req.body || {};
  const userMsg = messages?.[messages.length - 1]?.content || "";

  // Intent classification
  const plan = await openai.chat.completions.create({
    model: "gpt-4.1-mini",
    temperature: 0,
    messages: [{ role: "system", content: INTENT_SYSTEM }, { role: "user", content: userMsg }],
    response_format: { type: "json_object" }
  });
  const intent = JSON.parse(plan.choices[0].message!.content);
  const language = intent.language || (locale === "en" ? "en" : "it");
  const concerns = intent.concerns?.length ? intent.concerns : null;
  const device = intent.device ?? null;

  const results = await kbSearchFiltered(userMsg, { language, concerns, device, k: 12 });
  const context = results.map((r: any) => `Source: ${r.title}\n${r.content}`).join("\n---\n").slice(0, 12000);
  const citations = Array.from(new Set(results.map((r: any) => r.title))).slice(0, 6);

  const completion = await openai.chat.completions.create({
    model: "gpt-4.1",
    temperature: 0.4,
    messages: [
      { role: "system", content: SYSTEM_PROMPT + `\n\nCONTEXT:\n${context}` },
      ...messages,
      { role: "user", content: "Answer using only the CONTEXT above. Include inline citations with the source titles in parentheses. If context is insufficient, say so and propose a consult." }
    ]
  });

  const reply = completion.choices[0].message?.content || (language === "en" ? "Sorry, I could not find enough information." : "Mi dispiace, non ho trovato informazioni sufficienti.");
  return res.status(200).json({ reply, citations, intent });
}
