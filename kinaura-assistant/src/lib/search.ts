import { createClient } from "@supabase/supabase-js";
import OpenAI from "openai";

const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!);
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY! });

async function getEmbedding(q: string) {
  const r = await openai.embeddings.create({ model: "text-embedding-3-small", input: q });
  return r.data[0].embedding;
}

export async function kbSearchFiltered(query: string, opts: {
  language: "en" | "it",
  audience?: "public" | "staff",
  device?: string | null,
  concerns?: string[] | null,
  k?: number
}) {
  const { language, audience = "public", device = null, concerns = null, k = 12 } = opts;
  const qEmbed = await getEmbedding(query);
  const { data, error } = await supabase.rpc("match_kb_filtered", {
    query_embedding: qEmbed,
    match_count: k,
    filter_language: language,
    filter_audience: audience,
    filter_device: device,
    filter_concerns: concerns
  });
  if (error) throw error;
  return data || [];
}
