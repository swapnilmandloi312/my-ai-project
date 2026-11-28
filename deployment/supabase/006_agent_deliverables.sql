-- Private durable deliverables. Worker write access requires a separate approved integration.
BEGIN;
ALTER TABLE sal_ops.jobs ADD CONSTRAINT jobs_workspace_job_category_key
 UNIQUE (workspace_id, id, category);
CREATE TABLE sal_ops.agent_deliverables (
 workspace_id uuid NOT NULL,
 job_id uuid NOT NULL,
 category text NOT NULL,
 tool text NOT NULL CHECK (tool IN ('git_revision', 'research_export', 'analytics_export', 'document_export')),
 body jsonb NOT NULL CHECK (
  jsonb_typeof(body) = 'object'
  AND octet_length(body::text) <= 16384
  AND body ?& ARRAY['category','tool','kind','requires_review']
  AND body->>'category' IS NOT DISTINCT FROM category
  AND body->>'tool' IS NOT DISTINCT FROM tool
  AND body->>'kind' IS NOT DISTINCT FROM 'evidence_review'
  AND body->'requires_review' IS NOT DISTINCT FROM 'true'::jsonb
 ),
 stored_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (workspace_id, job_id),
 FOREIGN KEY (workspace_id, job_id, category) REFERENCES sal_ops.jobs(workspace_id, id, category)
);
ALTER TABLE sal_ops.agent_deliverables ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON sal_ops.agent_deliverables FROM PUBLIC, anon, authenticated, service_role,
 sal_job_worker, sal_hourly_worker;

-- Return indexed metadata only; evidence contents remain private to the storage owner.
CREATE FUNCTION public.sal_agent_deliverable_index(p_slug text)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid;
BEGIN
 SELECT m.workspace_id INTO w FROM sal_ops.members m
 JOIN sal_ops.workspaces s ON s.id=m.workspace_id
 WHERE s.slug=p_slug AND m.user_id=auth.uid();
 IF w IS NULL THEN
  RAISE EXCEPTION 'membership required' USING ERRCODE='42501';
 END IF;
 RETURN COALESCE((
  SELECT jsonb_agg(to_jsonb(d) ORDER BY d.stored_at DESC, d.job_id)
  FROM (
   SELECT job_id, category, tool, stored_at
   FROM sal_ops.agent_deliverables
   WHERE workspace_id=w
   ORDER BY stored_at DESC, job_id LIMIT 100
  ) AS d
 ), '[]'::jsonb);
END $$;
REVOKE ALL ON FUNCTION public.sal_agent_deliverable_index(text)
 FROM PUBLIC, anon, authenticated, service_role, sal_job_worker, sal_hourly_worker;
GRANT EXECUTE ON FUNCTION public.sal_agent_deliverable_index(text) TO authenticated;
COMMIT;
