-- 002_match_kb_filtered.sql
create or replace function match_kb_filtered(
  query_embedding vector(1536),
  match_count int,
  filter_language text,
  filter_audience text,
  filter_device text default null,
  filter_concerns text[] default null
)
returns table (
  id uuid, title text, source text, language text, audience text,
  tags text[], content text, device text, concerns text[], similarity float
)
language sql stable as $$
  select
    id, title, source, language, audience, tags, content, device, concerns,
    1 - (kb_chunks.embedding <-> query_embedding) as similarity
  from kb_chunks
  where language in ('it','en','bilingual')
    and (lang_segment = filter_language or lang_segment is null)
    and audience = filter_audience
    and (filter_device is null or device = filter_device)
    and (filter_concerns is null or concerns && filter_concerns)
  order by kb_chunks.embedding <-> query_embedding
  limit match_count;
$$;
