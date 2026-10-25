-- 在 Supabase SQL Editor 執行一次，保留原本資料，不刪除既有表格。
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS year integer;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS level integer;
ALTER TABLE public.questions ADD COLUMN IF NOT EXISTS original_id text;
CREATE UNIQUE INDEX IF NOT EXISTS questions_original_id_unique ON public.questions (original_id) WHERE original_id IS NOT NULL;
-- 如先前尚未設定管理員，將下列 YOUR_UID 換成 Authentication > Users 的 User UID 後執行：
-- INSERT INTO public.admin_users(user_id) VALUES ('YOUR_UID') ON CONFLICT DO NOTHING;
-- 注意：不要在 GitHub Pages 放置 service_role 或 secret key。
