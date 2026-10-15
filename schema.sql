-- 在 Supabase SQL Editor 執行。公開前請先建立管理員帳號，再將其 UID 加入 admin_users。
create table if not exists public.admin_users (user_id uuid primary key references auth.users(id) on delete cascade);
create table if not exists public.questions (
 id uuid primary key default gen_random_uuid(), subject text not null, stem text not null,
 options jsonb not null, answer integer not null check(answer between 0 and 3),
 explanation text not null, source text not null, law text default '', created_at timestamptz not null default now());
create table if not exists public.attempts (
 id uuid primary key, user_id uuid not null references auth.users(id) on delete cascade,
 question_id text not null, subject text not null, correct boolean not null,
 created_at timestamptz not null default now());
create table if not exists public.favorites (
 user_id uuid not null references auth.users(id) on delete cascade,
 question_id text not null, primary key(user_id,question_id));
alter table public.admin_users enable row level security;
alter table public.questions enable row level security;
alter table public.attempts enable row level security;
alter table public.favorites enable row level security;
create policy "read own admin status" on public.admin_users for select to authenticated using (user_id=auth.uid());
create policy "read questions" on public.questions for select to authenticated using (true);
create policy "admins add questions" on public.questions for insert to authenticated with check (exists(select 1 from public.admin_users where user_id=auth.uid()));
create policy "admins update questions" on public.questions for update to authenticated using (exists(select 1 from public.admin_users where user_id=auth.uid())) with check (exists(select 1 from public.admin_users where user_id=auth.uid()));
create policy "admins delete questions" on public.questions for delete to authenticated using (exists(select 1 from public.admin_users where user_id=auth.uid()));
create policy "read own attempts" on public.attempts for select to authenticated using (user_id=auth.uid());
create policy "add own attempts" on public.attempts for insert to authenticated with check (user_id=auth.uid());
create policy "read own favorites" on public.favorites for select to authenticated using (user_id=auth.uid());
create policy "add own favorites" on public.favorites for insert to authenticated with check (user_id=auth.uid());
create policy "remove own favorites" on public.favorites for delete to authenticated using (user_id=auth.uid());
-- 註冊後在 Supabase Authentication > Users 複製自己的 UUID，執行：
-- insert into public.admin_users(user_id) values ('你的-user-uuid');
