-- Private, single-workspace Python worker capability. No login secret in migration.
BEGIN;
ALTER TABLE sal_ops.run_reports DROP CONSTRAINT run_reports_source_check;
ALTER TABLE sal_ops.run_reports ADD CONSTRAINT run_reports_source_check CHECK (source IN ('github_ci','chatgpt_automation','local_demo','independent_benchmark','database_cron','github_worker'));
CREATE ROLE sal_hourly_worker NOLOGIN NOINHERIT NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE TABLE sal_ops.worker_bindings(
 role_name name PRIMARY KEY, workspace_id uuid NOT NULL REFERENCES sal_ops.workspaces(id),
 enabled boolean NOT NULL DEFAULT true
);
ALTER TABLE sal_ops.worker_bindings ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON sal_ops.worker_bindings FROM PUBLIC,anon,authenticated,service_role,sal_job_worker,sal_hourly_worker;
INSERT INTO sal_ops.worker_bindings(role_name,workspace_id) SELECT 'sal_hourly_worker',id FROM sal_ops.workspaces WHERE slug='swapnil-ai-labs';
CREATE FUNCTION sal_ops.bound_worker_slug() RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE slug_value text;
BEGIN
 SELECT w.slug INTO slug_value FROM sal_ops.worker_bindings b JOIN sal_ops.workspaces w ON w.id=b.workspace_id
 WHERE b.role_name=session_user::name AND b.enabled;
 IF slug_value IS NULL THEN RAISE EXCEPTION 'worker identity not bound' USING ERRCODE='42501'; END IF;
 RETURN slug_value;
END $$;
CREATE FUNCTION sal_ops.hourly_claim() RETURNS jsonb LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$
 SELECT sal_ops.claim_job(sal_ops.bound_worker_slug());
$$;
CREATE FUNCTION sal_ops.hourly_finish(p_id uuid,p_lease uuid,p_result jsonb) RETURNS boolean LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$
 SELECT sal_ops.finish_job(sal_ops.bound_worker_slug(),p_id,p_lease,p_result);
$$;
CREATE FUNCTION sal_ops.hourly_worker_report(p_run_id text,p_counts jsonb) RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; lim sal_ops.job_limits%ROWTYPE; claimed int; accepted int; rejected int; invalid int; max_jobs int; inserted int;
BEGIN
 SELECT id INTO STRICT w FROM sal_ops.workspaces WHERE slug=sal_ops.bound_worker_slug();
 IF p_run_id IS NULL OR p_run_id !~ '^[0-9]{1,20}:[0-9]{1,6}$' OR p_counts IS NULL OR jsonb_typeof(p_counts)<>'object'
  OR octet_length(p_counts::text)>500 OR NOT (p_counts ?& ARRAY['claimed','accepted','rejected','evaluation_failed','max_jobs'])
  OR (SELECT count(*) FROM jsonb_object_keys(p_counts))<>5
  OR EXISTS(SELECT 1 FROM jsonb_each(p_counts) x WHERE jsonb_typeof(x.value)<>'number' OR x.value::text !~ '^[0-9]{1,2}$')
 THEN RAISE EXCEPTION 'invalid worker report'; END IF;
 claimed:=(p_counts->>'claimed')::int; accepted:=(p_counts->>'accepted')::int; rejected:=(p_counts->>'rejected')::int;
 invalid:=(p_counts->>'evaluation_failed')::int; max_jobs:=(p_counts->>'max_jobs')::int;
 IF max_jobs NOT BETWEEN 1 AND 40 OR claimed>max_jobs OR accepted+rejected<>claimed OR invalid>claimed THEN RAISE EXCEPTION 'invalid worker counters'; END IF;
 SELECT * INTO STRICT lim FROM sal_ops.job_limits WHERE workspace_id=w;
 INSERT INTO sal_ops.run_reports(workspace_id,source,run_id,category,status,scope,summary,observed_at,completed_at)
 VALUES(w,'github_worker',p_run_id,NULL,CASE WHEN rejected>0 OR invalid>0 THEN 'partial' WHEN lim.stopped THEN 'blocked' WHEN claimed=0 THEN 'no_update' ELSE 'success' END,
 'actual_operations',jsonb_build_object('kind','hosted_worker_heartbeat','synthetic_only',true,'production_agent_execution',false,'worker_reported_counts',p_counts,
 'queue_stopped',lim.stopped,'attempts_used',lim.attempts_used,'model_calls',0,'external_calls',0,
 'limitations','Counters are worker-reported; cross-check queue job records. No business tool/model execution.'),clock_timestamp(),clock_timestamp())
 ON CONFLICT(workspace_id,source,run_id) DO NOTHING;
 GET DIAGNOSTICS inserted=ROW_COUNT; RETURN inserted=1;
END $$;
REVOKE ALL ON FUNCTION sal_ops.bound_worker_slug(),sal_ops.hourly_claim(),sal_ops.hourly_finish(uuid,uuid,jsonb),sal_ops.hourly_worker_report(text,jsonb) FROM PUBLIC,anon,authenticated,service_role,sal_job_worker,sal_hourly_worker;
GRANT USAGE ON SCHEMA sal_ops TO sal_hourly_worker;
GRANT EXECUTE ON FUNCTION sal_ops.hourly_claim(),sal_ops.hourly_finish(uuid,uuid,jsonb),sal_ops.hourly_worker_report(text,jsonb) TO sal_hourly_worker;
COMMIT;
