DO $$ BEGIN
 IF NOT EXISTS (
  SELECT 1 FROM sal_ops.jobs j JOIN sal_ops.agent_deliverables d ON d.job_id=j.id
  WHERE j.request_key='evidence-test' AND j.state='succeeded' AND j.attempts=1
  AND d.commit_lease IS NOT NULL AND d.body->'recorded_evidence'->>'hypothesis'='approved:fixture'
  AND EXISTS (SELECT 1 FROM sal_ops.job_events e WHERE e.job_id=j.id AND e.event='succeeded')
 ) THEN RAISE EXCEPTION 'approved evidence job missing deliverable or event'; END IF;
END $$;

BEGIN;
SELECT set_config('test.evidence_job',job_id::text,true),
 set_config('test.evidence_lease',commit_lease::text,true),
 set_config('test.evidence_body',body::text,true)
FROM sal_ops.agent_deliverables WHERE category='research';
SET SESSION AUTHORIZATION sal_hourly_worker;
DO $$
DECLARE job_id uuid:=current_setting('test.evidence_job')::uuid;
 lease uuid:=current_setting('test.evidence_lease')::uuid;
 body jsonb:=current_setting('test.evidence_body')::jsonb;
BEGIN
 IF NOT sal_ops.finish_evidence_job(job_id,lease,body)
 OR sal_ops.finish_evidence_job(job_id,gen_random_uuid(),body)
 OR sal_ops.finish_evidence_job(job_id,lease,body || '{"extra":true}'::jsonb)
 THEN RAISE EXCEPTION 'completion replay or stale lease handling incorrect'; END IF;
END $$;
RESET SESSION AUTHORIZATION;
ROLLBACK;
