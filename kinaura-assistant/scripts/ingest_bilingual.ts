import fs from "fs";
import path from "path";
import OpenAI from "openai";
import { createClient } from "@supabase/supabase-js";
import { MarkdownTextSplitter } from "@langchain/textsplitters";
import { CONCERNS, DEVICES } from "./taxonomies";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY! });
const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!);
const KB_DIR = path.join(process.cwd(), "kb");
const splitter = new MarkdownTextSplitter({ chunkSize: 900, chunkOverlap: 140 });

function inferConcerns(text: string): string[] {
  const map: Record<string, string> = {
    redness: "redness|erythema|rossor|vascul|capillar",
    rosacea: "rosacea",
    pigmentation: "pigment|discrom|melanin|macchie|sun damage|fotodanno",
    sun_damage: "sun damage|photodamage|fotodanno",
    pre_event_glow: "pre[- ]?event|red[- ]?carpet|glow|luminos",
    fine_lines: "fine lines|linee sottili",
    wrinkles: "wrinkl|rughe",
    skin_laxity_face: "laxity|lassità|ptosi|tighten",
    jawline_neck_contour: "jawline|mandibol|neck|collo|contour",
    texture: "texture|pores|pori|resurfac",
    acne: "acne|comedon|congestion",
    acne_scars: "acne scar|cicatrici acne",
    pores: "pores|pori",
    cellulite: "cellulit",
    body_contour: "body contour|rimodellamento|adipo|fat",
    hair_loss: "hair loss|alopec|caduta capelli",
    vaginal_rejuvenation: "vaginal|intim|ultraintimi",
    recovery: "recovery|recupero|post[- ]treatment",
    inflammation: "inflamm|infiammaz",
    detox: "detox|ozone|ozono|endolaser systemic",
    stress_sleep: "stress|sleep|sonno|ansia",
    performance: "performance|athletic|jet[- ]?lag|energia"
  };
  const found: string[] = [];
  const t = text.toLowerCase();
  for (const [k, rx] of Object.entries(map)) if (new RegExp(rx, "i").test(t)) found.push(k);
  return found;
}

function inferDevice(title: string, text: string): string | null {
  const hay = (title + " " + text).toLowerCase();
  const candidates: Record<string, RegExp> = {
    "VISIA-7": /visia[- ]?7/i,
    "Wellness Tower": /wellness\s+tower/i,
    "Sciton mJOULE (BBL HERO / MOXI / SkinTyte)": /mjoule|bbl\s*hero|moxi|skintype?/i,
    "InMode Ignite (Morpheus8 / FaceTite / BodyTite)": /inmode|morpheus8|facet?ite|bodyt?ite/i,
    "MCT (Meta Cell Technology)": /\bmct\b|meta\s+cell/i,
    "Emuage Lab": /emuage/i,
    "Ultraformer MPT (HIFU)": /ultraformer\s*mpt|hifu/i,
    "Weberneedle Endolaser": /weber.*endolaser|endoven(o|a)/i,
    "Fotona DYNAMIS MAX (Er:YAG / Nd:YAG)": /fotona|dynamis|er:?yag|nd:?yag/i,
    "AirPod Revive Hydroxy (mHBOT + H2)": /airpod\s+revive|hydroxy|m(h)?bot|iperbaric/i,
    "Ammortal Chamber (PEMF/PEF + PBM + H2 + Vibro-Acoustic)": /ammortal|pemf|pef|photobiomod/i,
    "HydraFacial Syndeo MD": /hydrafacial|syndeo/i
  };
  for (const [device, rx] of Object.entries(candidates)) if (rx.test(hay)) return device;
  return null;
}

function detectLangSegment(block: string): "en" | "it" | null {
  if (/^##\s*EN\b|^#\s*EN\b|EN\s–/im.test(block)) return "en";
  if (/^##\s*IT\b|^#\s*IT\b|IT\s–/im.test(block)) return "it";
  const itHits = (block.match(/[àèéìòù]| che | per | con | pelle | trattamento/gi) || []).length;
  const enHits = (block.match(/\bthe\b|\band\b|\bskin\b|\btreatment\b/gi) || []).length;
  if (itHits > enHits) return "it";
  if (enHits > itHits) return "en";
  return null;
}

async function embed(input: string) {
  const res = await openai.embeddings.create({ model: "text-embedding-3-small", input });
  return res.data[0].embedding;
}

async function run() {
  const files = fs.readdirSync(KB_DIR).filter(f => f.endsWith(".md"));
  for (const file of files) {
    const source = `kb/${file}`;
    const raw = fs.readFileSync(path.join(KB_DIR, file), "utf8");
    const chunks = await splitter.splitText(raw);

    for (const content of chunks) {
      const lang_segment = detectLangSegment(content) || null;
      const device = inferDevice(file, content);
      const concerns = inferConcerns(content);
      const topic = /how it works|come funziona/i.test(content) ? "mechanism"
                  : /why it works|perch[eé] funziona/i.test(content) ? "rationale"
                  : /treatments|applicazioni|protocol/i.test(content) ? "protocols"
                  : /mapping|mappatura/i.test(content) ? "mapping"
                  : null;

      const titleMatch = raw.match(/title:\s*(.+)/i);
      const title = titleMatch ? titleMatch[1].trim() : file.replace(/\.md$/,"");

      const embedding = await embed(content);

      const { error } = await supabase.from("kb_chunks").insert({
        title,
        source,
        language: "bilingual",
        audience: "public",
        tags: [],
        content,
        embedding,
        device,
        concerns,
        lang_segment,
        section: device ? "Device Profiles" : (topic === "mapping" ? "Mapping" : null),
        topic
      } as any);

      if (error) {
        console.error("Insert error", file, error);
        process.exitCode = 1;
      }
    }

    console.log(`Ingested ${file} -> ${chunks.length} chunks`);
  }
}

run().catch(e => { console.error(e); process.exit(1); });
