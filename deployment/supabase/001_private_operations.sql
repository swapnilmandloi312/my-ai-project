-- Staging migration candidate. Apply only to an authorized, reviewed Supabase project.
BEGIN;
CREATE TABLE public.sal_tenants (
  id uuid PRIMARY KEY,
  label text NOT NULL CHECK (char_length(label) BETWEEN 1 AND 120),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE public.sal_members (
  tenant_id uuid NOT NULL REFERENCES public.sal_tenants(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  PRIMARY KEY (tenant_id,user_id)
);
CREATE INDEX sal_members_user_idx ON public.sal_members(user_id,tenant_id);
CREATE TABLE public.sal_operations_runs (
  tenant_id uuid NOT NULL REFERENCES public.sal_tenants(id) ON DELETE CASCADE,
  source text NOT NULL CHECK (source IN ('coordinator','global_outreach','premium_outreach','startup_outreach','partnerships','local_agent')),
  run_id text NOT NULL CHECK (char_length(run_id) BETWEEN 1 AND 128),
  category text CHECK (category IN ('ceo','research','engineering','model_eval','security','product','growth','partnership','finance','quality','finance_ops','hr_ops','it_ops','support_ops')),
  state text NOT NULL CHECK (state IN ('scheduled','running','completed','failed','no_update','blocked')),
  summary text NOT NULL DEFAULT '' CHECK (char_length(summary)<=2000),
  completed_at timestamptz,
  verified_at timestamptz NOT NULL,
  evidence_url text CHECK (char_length(evidence_url)<=500 AND evidence_url ~ '^https://github[.]com/swapnilmandloi312/my-ai-project/'),
  PRIMARY KEY (tenant_id,source,run_id),
  CHECK (state NOT IN ('completed','failed','no_update') OR completed_at IS NOT NULL),
  CHECK (completed_at IS NULL OR completed_at<=verified_at)
);
CREATE INDEX sal_runs_recent_idx ON public.sal_operations_runs(tenant_id,verified_at DESC);
ALTER TABLE public.sal_tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sal_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sal_operations_runs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.sal_tenants,public.sal_members,public.sal_operations_runs FROM PUBLIC,anon,authenticated;
GRANT SELECT ON public.sal_tenants,public.sal_members,public.sal_operations_runs TO authenticated;
GRANT SELECT,INSERT,UPDATE,DELETE ON public.sal_tenants,public.sal_members,public.sal_operations_runs TO service_role;
CREATE POLICY sal_member_self ON public.sal_members FOR SELECT TO authenticated
  USING (user_id=(SELECT auth.uid()));
CREATE POLICY sal_tenant_read ON public.sal_tenants FOR SELECT TO authenticated
  USING (EXISTS (SELECT 1 FROM public.sal_members m WHERE m.tenant_id=sal_tenants.id AND m.user_id=(SELECT auth.uid())));
CREATE POLICY sal_run_read ON public.sal_operations_runs FOR SELECT TO authenticated
  USING (EXISTS (SELECT 1 FROM public.sal_members m WHERE m.tenant_id=sal_operations_runs.tenant_id AND m.user_id=(SELECT auth.uid())));
COMMIT;
