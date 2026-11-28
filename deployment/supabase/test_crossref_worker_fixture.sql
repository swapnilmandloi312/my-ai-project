UPDATE sal_ops.job_limits SET attempt_limit=attempts_used+1
WHERE workspace_id='11111111-1111-1111-1111-111111111111';
INSERT INTO sal_ops.agent_profiles VALUES ('research',ARRAY['doi']) ON CONFLICT DO NOTHING;
INSERT INTO sal_ops.agent_controls(workspace_id,category,paused)
VALUES ('11111111-1111-1111-1111-111111111111','research',false)
ON CONFLICT (workspace_id,category) DO UPDATE SET paused=false;
SET ROLE authenticated;
SELECT set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',false);
SELECT public.sal_submit_evidence_job('test-workspace','research','crossref-ci','{"doi":"10.1093/mind/lix.236.433"}');
DO $$ BEGIN
 BEGIN
  PERFORM public.sal_submit_evidence_job('test-workspace','research','crossref-invalid','{"doi":"https://example.com"}');
  RAISE EXCEPTION 'unbounded input accepted';
 EXCEPTION WHEN raise_exception THEN
  IF SQLERRM<>'invalid evidence request' THEN RAISE; END IF;
 END;
END $$;
RESET ROLE;
SET SESSION AUTHORIZATION sal_hourly_worker;
DO $$ BEGIN
 IF sal_ops.claim_crossref_evidence_job() IS NOT NULL THEN RAISE EXCEPTION 'approval bypass'; END IF;
END $$;
RESET SESSION AUTHORIZATION;
SELECT set_config('crossref.fixture_job',(SELECT id::text FROM sal_ops.jobs WHERE request_key='crossref-ci'),false);
SET ROLE authenticated;
SELECT public.sal_job_command('test-workspace','approve',jsonb_build_object('id',current_setting('crossref.fixture_job')));
RESET ROLE;
