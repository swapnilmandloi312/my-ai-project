-- Hosted live GitHub mode must skip jobs that require offline export adapters.
BEGIN;
CREATE FUNCTION sal_ops.claim_evidence_job_for_tool(p_tool text) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; lim sal_ops.job_limits%ROWTYPE; j sal_ops.jobs%ROWTYPE;
BEGIN
 SELECT id INTO STRICT w FROM sal_ops.workspaces WHERE slug=sal_ops.bound_worker_slug();
 SELECT * INTO STRICT lim FROM sal_ops.job_limits WHERE workspace_id=w FOR UPDATE;
 IF lim.stopped THEN RETURN NULL; END IF;
 UPDATE sal_ops.jobs SET state=CASE WHEN attempts>=3 THEN 'failed' ELSE 'queued' END,
   lease_id=NULL,lease_until=NULL,available_at=clock_timestamp()+make_interval(secs=>power(2,attempts)::int),updated_at=clock_timestamp()
   WHERE workspace_id=w AND state='running' AND delivery_tool IS NOT NULL AND (p_tool IS NULL OR delivery_tool=p_tool) AND lease_until<=clock_timestamp();
 IF lim.attempts_used>=lim.attempt_limit THEN RETURN NULL; END IF;
 SELECT q.* INTO j FROM sal_ops.jobs q JOIN sal_ops.agent_controls a ON a.workspace_id=q.workspace_id AND a.category=q.category
 WHERE q.workspace_id=w AND q.delivery_tool IS NOT NULL AND (p_tool IS NULL OR q.delivery_tool=p_tool) AND q.state='queued' AND q.approved_by IS NOT NULL AND NOT a.paused
 AND q.available_at<=clock_timestamp() AND q.attempts<3 ORDER BY q.created_at,q.id LIMIT 1 FOR UPDATE OF q SKIP LOCKED;
 IF NOT FOUND THEN RETURN NULL; END IF;
 UPDATE sal_ops.job_limits SET attempts_used=attempts_used+1 WHERE workspace_id=w;
 UPDATE sal_ops.jobs SET state='running',attempts=attempts+1,lease_id=gen_random_uuid(),lease_until=clock_timestamp()+interval '60 seconds',updated_at=clock_timestamp()
 WHERE id=j.id RETURNING * INTO j;
 RETURN jsonb_build_object('id',j.id,'lease_id',j.lease_id,'category',j.category,'evidence',j.evidence,'tool',j.delivery_tool);
END $$;
CREATE OR REPLACE FUNCTION sal_ops.claim_evidence_job() RETURNS jsonb
LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$
 SELECT sal_ops.claim_evidence_job_for_tool(NULL);
$$;
CREATE FUNCTION sal_ops.claim_github_evidence_job() RETURNS jsonb
LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$
 SELECT sal_ops.claim_evidence_job_for_tool('git_revision');
$$;
REVOKE ALL ON FUNCTION sal_ops.claim_evidence_job_for_tool(text),sal_ops.claim_github_evidence_job()
 FROM PUBLIC,anon,authenticated,service_role,sal_job_worker,sal_hourly_worker;
GRANT EXECUTE ON FUNCTION sal_ops.claim_github_evidence_job() TO sal_hourly_worker;
COMMIT;
