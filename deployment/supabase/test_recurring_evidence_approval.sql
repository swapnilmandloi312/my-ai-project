SET ROLE authenticated;
SELECT set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',false);
SELECT public.sal_evidence_schedule('test-workspace','bounded','10101010-0000-0000-0000-000000000001',NULL,1);
DO $$ BEGIN
 IF NOT public.sal_set_recurring_evidence_approval('test-workspace','bounded',1,1)
 THEN RAISE EXCEPTION 'founder policy missing'; END IF;
END $$;
SELECT set_config('request.jwt.claim.sub','bbbbbbbb-0000-0000-0000-000000000002',false);
DO $$ BEGIN
 BEGIN
  PERFORM public.sal_set_recurring_evidence_approval('test-workspace','bounded',24,24);
  RAISE EXCEPTION 'viewer changed policy';
 EXCEPTION WHEN insufficient_privilege THEN NULL; END;
END $$;
RESET ROLE;
SET SESSION AUTHORIZATION sal_hourly_worker;
SELECT sal_ops.materialize_github_evidence_schedules();
RESET SESSION AUTHORIZATION;
DO $$ BEGIN
 IF NOT EXISTS (
  SELECT FROM sal_ops.evidence_schedules s JOIN sal_ops.jobs j ON j.id=s.last_job
  JOIN sal_ops.job_events e ON e.job_id=j.id AND e.event='recurring_approval'
  WHERE s.schedule_key='bounded' AND s.approval_remaining=0
  AND j.approved_by=s.created_by AND j.state='queued'
 ) THEN RAISE EXCEPTION 'bounded authorization did not create one audited job'; END IF;
 IF has_function_privilege('sal_hourly_worker','public.sal_set_recurring_evidence_approval(text,text,int,int)','EXECUTE')
 THEN RAISE EXCEPTION 'worker can grant approval'; END IF;
END $$;
UPDATE sal_ops.jobs SET state='succeeded' WHERE id=(SELECT last_job FROM sal_ops.evidence_schedules WHERE schedule_key='bounded');
UPDATE sal_ops.evidence_schedules SET next_due=clock_timestamp() WHERE schedule_key='bounded';
SET SESSION AUTHORIZATION sal_hourly_worker;
SELECT sal_ops.materialize_github_evidence_schedules();
RESET SESSION AUTHORIZATION;
DO $$ BEGIN
 IF NOT EXISTS (SELECT FROM sal_ops.evidence_schedules s JOIN sal_ops.jobs j ON j.id=s.last_job
 WHERE s.schedule_key='bounded' AND j.state='pending' AND j.approved_by IS NULL)
 THEN RAISE EXCEPTION 'exhausted policy bypassed manual approval'; END IF;
END $$;
