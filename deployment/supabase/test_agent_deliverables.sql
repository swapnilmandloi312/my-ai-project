BEGIN;
INSERT INTO sal_ops.agent_deliverables (workspace_id, job_id, category, tool, body)
SELECT workspace_id, id, category, 'research_export',
 jsonb_build_object('category',category,'tool','research_export','kind','evidence_review',
 'requires_review',true,'recorded_evidence',jsonb_build_object('source','fixture-private'))
FROM sal_ops.jobs WHERE request_key='scoped-worker-acceptance';
DO $$ BEGIN
 IF has_table_privilege('sal_hourly_worker','sal_ops.agent_deliverables','INSERT')
 OR has_table_privilege('authenticated','sal_ops.agent_deliverables','SELECT')
 OR has_function_privilege('anon','public.sal_agent_deliverable_index(text)','EXECUTE')
 THEN RAISE EXCEPTION 'deliverable access too broad'; END IF;
END $$;
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',true);
DO $$
DECLARE result jsonb;
BEGIN
 result:=public.sal_agent_deliverable_index('test-workspace');
 IF jsonb_array_length(result)<>1 OR result::text LIKE '%fixture-private%'
 OR result->0->>'tool' IS DISTINCT FROM 'research_export'
 THEN RAISE EXCEPTION 'missing or unsafe metadata'; END IF;
 BEGIN
  PERFORM public.sal_agent_deliverable_index('other-workspace');
  RAISE EXCEPTION 'cross-workspace access succeeded';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
END $$;
ROLLBACK;
