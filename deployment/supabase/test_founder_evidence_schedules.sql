-- Exercise scheduling and scheduler authorization in a disposable database.
INSERT INTO sal_ops.worker_bindings(role_name,workspace_id)
VALUES('sal_hourly_worker','11111111-1111-1111-1111-111111111111');
INSERT INTO sal_ops.agent_profiles VALUES ('engineering',ARRAY['source_revision']);
INSERT INTO sal_ops.agent_controls(workspace_id,category,paused)
VALUES('11111111-1111-1111-1111-111111111111','engineering',false);
INSERT INTO sal_ops.jobs(id,workspace_id,category,request_key,requested_by,approved_by,evidence,delivery_tool,state)
VALUES
('10101010-0000-0000-0000-000000000001','11111111-1111-1111-1111-111111111111','engineering','test-template',
 'aaaaaaaa-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000001',
 '{"source_revision":"42f3324fc53319252c79081243ba54d50893bb15"}','git_revision','succeeded'),
('10101010-0000-0000-0000-000000000002','11111111-1111-1111-1111-111111111111','engineering','test-dependency',
 'aaaaaaaa-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000001',
 '{}','git_revision','queued'),
('10101010-0000-0000-0000-000000000003','22222222-2222-2222-2222-222222222222','engineering','test-other',
 'bbbbbbbb-0000-0000-0000-000000000002','bbbbbbbb-0000-0000-0000-000000000002',
 '{}','git_revision','succeeded');

SET ROLE authenticated;
SELECT set_config('request.jwt.claim.sub','bbbbbbbb-0000-0000-0000-000000000002',false);
DO $$ BEGIN
 BEGIN
  PERFORM public.sal_evidence_schedule('test-workspace','test','10101010-0000-0000-0000-000000000001',NULL,1);
  RAISE EXCEPTION 'viewer scheduled a job';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
END $$;

SELECT set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',false);
DO $$
DECLARE t uuid:='10101010-0000-0000-0000-000000000001';
        d uuid:='10101010-0000-0000-0000-000000000002'; s uuid;
BEGIN
 s:=public.sal_evidence_schedule('test-workspace','test',t,d,1);
 IF public.sal_evidence_schedule('test-workspace','test',t,d,1)<>s THEN
  RAISE EXCEPTION 'schedule key is not idempotent';
 END IF;
 BEGIN
  PERFORM public.sal_evidence_schedule('test-workspace','cross-workspace',t,'10101010-0000-0000-0000-000000000003',1);
  RAISE EXCEPTION 'cross-workspace dependency accepted';
 EXCEPTION WHEN raise_exception THEN
  IF SQLERRM<>'invalid schedule' THEN RAISE; END IF;
 END;
 IF (public.sal_evidence_schedule_index('test-workspace')->0->>'dependency_state') IS DISTINCT FROM 'queued' THEN
  RAISE EXCEPTION 'dependency missing from dashboard index';
 END IF;
END $$;
RESET ROLE;

SET SESSION AUTHORIZATION sal_hourly_worker;
DO $$ BEGIN
 IF sal_ops.materialize_github_evidence_schedules()<>0 THEN RAISE EXCEPTION 'stop bypass'; END IF;
END $$;
RESET SESSION AUTHORIZATION;
UPDATE sal_ops.job_limits SET stopped=false,attempt_limit=5 WHERE workspace_id='11111111-1111-1111-1111-111111111111';

SET SESSION AUTHORIZATION sal_hourly_worker;
DO $$ BEGIN
 IF sal_ops.materialize_github_evidence_schedules()<>0 THEN RAISE EXCEPTION 'dependency bypass'; END IF;
END $$;
RESET SESSION AUTHORIZATION;
UPDATE sal_ops.jobs SET state='succeeded' WHERE request_key='test-dependency';
UPDATE sal_ops.agent_controls SET paused=true WHERE category='engineering';

SET SESSION AUTHORIZATION sal_hourly_worker;
DO $$ BEGIN
 IF sal_ops.materialize_github_evidence_schedules()<>0 THEN RAISE EXCEPTION 'category pause bypass'; END IF;
END $$;
RESET SESSION AUTHORIZATION;
UPDATE sal_ops.agent_controls SET paused=false WHERE category='engineering';
UPDATE sal_ops.job_limits SET attempts_used=5 WHERE workspace_id='11111111-1111-1111-1111-111111111111';

SET SESSION AUTHORIZATION sal_hourly_worker;
DO $$ BEGIN
 IF sal_ops.materialize_github_evidence_schedules()<>0 THEN RAISE EXCEPTION 'attempt cap bypass'; END IF;
END $$;
RESET SESSION AUTHORIZATION;
UPDATE sal_ops.job_limits SET attempts_used=0 WHERE workspace_id='11111111-1111-1111-1111-111111111111';

SET SESSION AUTHORIZATION sal_hourly_worker;
DO $$ BEGIN
 IF sal_ops.materialize_github_evidence_schedules()<>1 THEN RAISE EXCEPTION 'due plan missing'; END IF;
 IF sal_ops.materialize_github_evidence_schedules()<>0 THEN RAISE EXCEPTION 'duplicate occurrence'; END IF;
 IF sal_ops.claim_github_evidence_job() IS NOT NULL THEN RAISE EXCEPTION 'approval bypass'; END IF;
END $$;
RESET SESSION AUTHORIZATION;

UPDATE sal_ops.evidence_schedules SET next_due=clock_timestamp()-interval '1 hour';
SET SESSION AUTHORIZATION sal_hourly_worker;
DO $$ BEGIN
 IF sal_ops.materialize_github_evidence_schedules()<>0 THEN RAISE EXCEPTION 'second outstanding occurrence'; END IF;
END $$;
RESET SESSION AUTHORIZATION;

DO $$ BEGIN
 IF (SELECT count(*) FROM sal_ops.evidence_schedules s JOIN sal_ops.jobs j ON j.id=s.last_job
     WHERE j.state='pending' AND j.approved_by IS NULL AND j.parent_id=s.depends_on_job
     AND j.delivery_tool='git_revision')<>1 THEN RAISE EXCEPTION 'invalid pending job'; END IF;
 IF (SELECT attempts_used FROM sal_ops.job_limits WHERE workspace_id='11111111-1111-1111-1111-111111111111')<>0
 THEN RAISE EXCEPTION 'materialization spent an execution attempt'; END IF;
 IF has_table_privilege('sal_hourly_worker','sal_ops.evidence_schedules','SELECT')
 OR has_function_privilege('authenticated','sal_ops.materialize_github_evidence_schedules()','EXECUTE')
 THEN RAISE EXCEPTION 'schedule grants too broad'; END IF;
END $$;

SET ROLE authenticated;
DO $$ BEGIN
 IF (public.sal_evidence_schedule_index('test-workspace')->0->>'last_job') IS NULL THEN
  RAISE EXCEPTION 'materialized job missing from dashboard index';
 END IF;
 IF NOT public.sal_stop_evidence_schedule('test-workspace','test') THEN
  RAISE EXCEPTION 'could not stop the schedule';
 END IF;
END $$;
RESET ROLE;
