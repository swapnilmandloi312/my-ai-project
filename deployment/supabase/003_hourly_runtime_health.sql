-- Bounded, real infrastructure observation; not a queue worker or AI model.
BEGIN;
ALTER TABLE sal_ops.run_reports DROP CONSTRAINT run_reports_source_check;
ALTER TABLE sal_ops.run_reports ADD CONSTRAINT run_reports_source_check CHECK (source IN ('github_ci','chatgpt_automation','local_demo','independent_benchmark','database_cron'));
CREATE FUNCTION sal_ops.collect_runtime_health(p_slug text) RETURNS jsonb
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
DECLARE w uuid; stamp timestamptz:=clock_timestamp(); run_key text; metrics jsonb; lim sal_ops.job_limits%ROWTYPE; inserted int;
BEGIN
 SELECT id INTO STRICT w FROM sal_ops.workspaces WHERE slug=p_slug;
 SELECT * INTO STRICT lim FROM sal_ops.job_limits WHERE workspace_id=w;
 run_key:='runtime-health-'||to_char(stamp AT TIME ZONE 'UTC','YYYYMMDD-HH24');
 SELECT jsonb_build_object(
  'kind','actual_infrastructure_observation','collector','postgres_sql','profile_count',(SELECT count(*) FROM sal_ops.agent_controls WHERE workspace_id=w),
  'paused_profiles',(SELECT count(*) FROM sal_ops.agent_controls WHERE workspace_id=w AND paused),
  'founder_count',(SELECT count(*) FROM sal_ops.members WHERE workspace_id=w AND role='founder'),
  'queue_stopped',lim.stopped,'attempt_limit',lim.attempt_limit,'attempts_used',lim.attempts_used,
  'pending_jobs',(SELECT count(*) FROM sal_ops.jobs WHERE workspace_id=w AND state='pending'),
  'queued_jobs',(SELECT count(*) FROM sal_ops.jobs WHERE workspace_id=w AND state='queued'),
  'running_jobs',(SELECT count(*) FROM sal_ops.jobs WHERE workspace_id=w AND state='running'),
  'expired_leases',(SELECT count(*) FROM sal_ops.jobs WHERE workspace_id=w AND state='running' AND lease_until<=stamp),
  'failed_jobs',(SELECT count(*) FROM sal_ops.jobs WHERE workspace_id=w AND state='failed'),
  'completed_synthetic_jobs',(SELECT count(*) FROM sal_ops.jobs WHERE workspace_id=w AND state='succeeded'),
  'anon_command_granted',has_function_privilege('anon','public.sal_job_command(text,text,jsonb)','EXECUTE'),
  'browser_worker_claim_granted',has_function_privilege('authenticated','sal_ops.claim_job(text)','EXECUTE'),
  'browser_direct_job_read_granted',has_table_privilege('authenticated','sal_ops.jobs','SELECT'),
  'external_calls',0,'model_calls',0,'production_agent_execution',false,
  'observed_at',stamp,'limitations','Read-only state observation plus private report write; does not run or authorize jobs, prove a hosted worker, or measure monetary cloud spend.'
 ) INTO metrics;
 INSERT INTO sal_ops.run_reports(workspace_id,source,run_id,category,status,scope,summary,observed_at,completed_at)
 VALUES(w,'database_cron',run_key,NULL,CASE WHEN (metrics->>'expired_leases')::int>0 OR (metrics->>'anon_command_granted')::boolean OR (metrics->>'browser_worker_claim_granted')::boolean OR (metrics->>'browser_direct_job_read_granted')::boolean THEN 'partial' ELSE 'success' END,'actual_operations',metrics,stamp,stamp)
 ON CONFLICT(workspace_id,source,run_id) DO NOTHING;
 GET DIAGNOSTICS inserted=ROW_COUNT;
 RETURN jsonb_build_object('run_id',run_key,'inserted',inserted=1,'metrics',metrics);
END $$;
REVOKE ALL ON FUNCTION sal_ops.collect_runtime_health(text) FROM PUBLIC,anon,authenticated,service_role,sal_job_worker;
COMMIT;
