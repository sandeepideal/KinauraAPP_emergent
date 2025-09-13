# KinAura Assistant – Handoff Bundle

**Updated:** 2025-08-15T10:08:12.431238Z

## What this is
A ready-to-run package for Emergent to build the KinAura bilingual, retrieval‑augmented chatbot:
- KB in Markdown (EN/IT, devices + treatments + mappings)
- Ingestion script with **device** and **concern** tagging
- Supabase schema + RPC
- Minimal Next.js API route

## Quick start
1. Create a Supabase project. In SQL editor, run:
   - `supabase/001_schema.sql`
   - `supabase/002_match_kb_filtered.sql`
   - (optional) `supabase/003_roles_policies.sql`
2. Set env:
   ```
   OPENAI_API_KEY=sk-...
   NEXT_PUBLIC_SUPABASE_URL=...
   NEXT_PUBLIC_SUPABASE_ANON_KEY=...
   SUPABASE_SERVICE_ROLE_KEY=...   # server-side only for ingestion
   ```
3. Install deps & ingest:
   ```
   npm i openai @supabase/supabase-js @langchain/textsplitters
   npx ts-node scripts/ingest_bilingual.ts
   ```
4. Implement `/src/pages_or_app/api/chat.ts` in your Next app, or adapt to your stack.
5. Test with Postman collection in `/postman`.

## Notes
- All clinical info is **general**; add your clinic's safety/legal footers in UI.
- The bot must always cite KB titles and avoid diagnosis/prescription.

