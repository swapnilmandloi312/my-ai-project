BEGIN;
SELECT set_config('test.batch_job',(SELECT last_job::text FROM sal_ops.evidence_schedules WHERE schedule_key='bounded'),true);
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claim.sub','bbbbbbbb-0000-0000-0000-000000000002',true);
DO $$ BEGIN
 BEGIN
  PERFORM public.sal_approve_readonly_evidence_batch('test-workspace',ARRAY[current_setting('test.batch_job')::uuid]);
  RAISE EXCEPTION 'viewer approval succeeded';
 EXCEPTION WHEN insufficient_privilege THEN NULL; END;
END $$;
SELECT set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',true);
DO $$
DECLARE job_id uuid:=current_setting('test.batch_job')::uuid; result jsonb;
BEGIN
 BEGIN
  PERFORM public.sal_approve_readonly_evidence_batch('test-workspace',ARRAY[job_id,'ffffffff-ffff-ffff-ffff-ffffffffffff'::uuid]);
  RAISE EXCEPTION 'mixed batch passed';
 EXCEPTION WHEN raise_exception THEN
  IF SQLERRM<>'batch contains an ineligible job' THEN RAISE; END IF;
 END;
 result:=public.sal_approve_readonly_evidence_batch('test-workspace',ARRAY[job_id]);
 IF result->0->>'state' IS DISTINCT FROM 'queued' THEN RAISE EXCEPTION 'eligible batch failed'; END IF;
END $$;
RESET ROLE;
DO $$ BEGIN
 IF NOT EXISTS (SELECT FROM sal_ops.jobs WHERE id=current_setting('test.batch_job')::uuid AND state='queued' AND approved_by IS NOT NULL AND attempts=0)
 OR NOT EXISTS (SELECT FROM sal_ops.job_events WHERE job_id=current_setting('test.batch_job')::uuid AND event='batch_approval')
 OR has_function_privilege('sal_hourly_worker','public.sal_approve_readonly_evidence_batch(text,uuid[])','EXECUTE')
 THEN RAISE EXCEPTION 'approval record or privilege incorrect'; END IF;
END $$;
ROLLBACK;
