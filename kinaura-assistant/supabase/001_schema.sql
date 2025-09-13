-- 001_schema.sql
create extension if not exists vector;

create table if not exists kb_chunks (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  source text not null,
  language text default 'bilingual',
  audience text default 'public',
  tags text[] default '{}',
  content text not null,
  embedding vector(1536),
  device text,
  concerns text[] default '{}',
  lang_segment text check (lang_segment in ('en','it')),
  section text,
  topic text,
  created_at timestamp with time zone default now()
);

create index if not exists kb_chunks_content_idx on kb_chunks using gin (to_tsvector('simple', content));
create index if not exists kb_chunks_embedding_idx on kb_chunks using ivfflat (embedding vector_l2_ops) with (lists = 100);
create index if not exists kb_chunks_concerns_idx on kb_chunks using gin (concerns);
create index if not exists kb_chunks_device_idx on kb_chunks (device);
create index if not exists kb_chunks_lang_idx on kb_chunks (lang_segment);
