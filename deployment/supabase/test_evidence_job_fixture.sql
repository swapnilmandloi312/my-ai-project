INSERT INTO sal_ops.agent_profiles VALUES ('research',ARRAY['hypothesis']);
INSERT INTO sal_ops.agent_controls(workspace_id,category,paused)
VALUES('11111111-1111-1111-1111-111111111111','research',false);

SET ROLE authenticated;
SELECT set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',false);
DO $$
DECLARE job_id uuid;
BEGIN
 job_id:=public.sal_submit_evidence_job('test-workspace','research','evidence-test','{"hypothesis":"approved:fixture"}');
 IF job_id IS DISTINCT FROM public.sal_submit_evidence_job('test-workspace','research','evidence-test','{"hypothesis":"approved:fixture"}') THEN
  RAISE EXCEPTION 'request replay returned another job';
 END IF;
 PERFORM public.sal_job_command('test-workspace','approve',jsonb_build_object('id',job_id));
END $$;
RESET ROLE;

-- A legacy worker cannot lease the approved evidence job.
DO $$ BEGIN
 IF sal_ops.claim_job('test-workspace') IS NOT NULL THEN
  RAISE EXCEPTION 'legacy worker claimed evidence job';
 END IF;
END $$;
