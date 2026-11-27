-- CI-only: real unprivileged login, fixture binding, no production credentials.
ALTER ROLE sal_hourly_worker LOGIN PASSWORD 'synthetic-ci-worker-only';
INSERT INTO sal_ops.worker_bindings(role_name,workspace_id) VALUES('sal_hourly_worker','11111111-1111-1111-1111-111111111111');
UPDATE sal_ops.job_limits SET stopped=false,attempt_limit=50 WHERE workspace_id='11111111-1111-1111-1111-111111111111';
UPDATE sal_ops.agent_controls SET paused=false WHERE workspace_id='11111111-1111-1111-1111-111111111111' AND category='ceo';
INSERT INTO sal_ops.jobs(workspace_id,category,request_key,requested_by,approved_by,evidence,state)
VALUES('11111111-1111-1111-1111-111111111111','ceo','scoped-worker-acceptance','aaaaaaaa-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000001','{}','queued');
DO $$ BEGIN
 IF has_function_privilege('authenticated','sal_ops.hourly_claim()','EXECUTE') OR has_function_privilege('sal_hourly_worker','sal_ops.claim_job(text)','EXECUTE') OR has_table_privilege('sal_hourly_worker','sal_ops.jobs','SELECT') OR has_table_privilege('sal_hourly_worker','sal_ops.worker_bindings','SELECT') THEN RAISE EXCEPTION 'worker access too broad'; END IF;
END $$;
