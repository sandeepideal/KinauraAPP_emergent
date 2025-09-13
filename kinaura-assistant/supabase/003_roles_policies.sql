-- 003_roles_policies.sql
-- Example: open read access (adjust to your needs; consider RLS policies)
alter table kb_chunks enable row level security;

create policy kb_read_public on kb_chunks
for select
using (true);
