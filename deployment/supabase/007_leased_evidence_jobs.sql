-- An evidence queue mode, sharing the workspace stop, pause and attempt controls.
BEGIN;
ALTER TABLE sal_ops.jobs ADD COLUMN delivery_tool text CHECK (
 delivery_tool IN ('git_revision','research_export','analytics_export','document_export')
);
ALTER TABLE sal_ops.agent_deliverables ADD COLUMN commit_lease uuid;

CREATE OR REPLACE FUNCTION sal_ops.claim_job(p_slug text) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; lim sal_ops.job_limits%ROWTYPE; j sal_ops.jobs%ROWTYPE;
BEGIN
 SELECT id INTO STRICT w FROM sal_ops.workspaces WHERE slug=p_slug;
 SELECT * INTO STRICT lim FROM sal_ops.job_limits WHERE workspace_id=w FOR UPDATE;
 IF lim.stopped THEN RETURN NULL; END IF;
 UPDATE sal_ops.jobs SET state=CASE WHEN attempts>=3 THEN 'failed' ELSE 'queued' END,
   lease_id=NULL,lease_until=NULL,available_at=clock_timestamp()+make_interval(secs=>power(2,attempts)::int),updated_at=clock_timestamp()
   WHERE workspace_id=w AND state='running' AND delivery_tool IS NULL AND lease_until<=clock_timestamp();
 IF lim.attempts_used>=lim.attempt_limit THEN RETURN NULL; END IF;
 SELECT q.* INTO j FROM sal_ops.jobs q JOIN sal_ops.agent_controls a ON a.workspace_id=q.workspace_id AND a.category=q.category
 WHERE q.workspace_id=w AND q.delivery_tool IS NULL AND q.state='queued' AND q.approved_by IS NOT NULL AND NOT a.paused
 AND q.available_at<=clock_timestamp() AND q.attempts<3 ORDER BY q.created_at,q.id LIMIT 1 FOR UPDATE OF q SKIP LOCKED;
 IF NOT FOUND THEN RETURN NULL; END IF;
 UPDATE sal_ops.job_limits SET attempts_used=attempts_used+1 WHERE workspace_id=w;
 UPDATE sal_ops.jobs SET state='running',attempts=attempts+1,lease_id=gen_random_uuid(),lease_until=clock_timestamp()+interval '60 seconds',updated_at=clock_timestamp()
 WHERE id=j.id RETURNING * INTO j;
 RETURN jsonb_build_object('id',j.id,'lease_id',j.lease_id,'category',j.category,'evidence',j.evidence);
END $$;

CREATE OR REPLACE FUNCTION sal_ops.finish_job(p_slug text,p_id uuid,p_lease uuid,p_result jsonb) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; lim sal_ops.job_limits%ROWTYPE; j sal_ops.jobs%ROWTYPE;
BEGIN
 SELECT id INTO STRICT w FROM sal_ops.workspaces WHERE slug=p_slug;
 SELECT * INTO STRICT lim FROM sal_ops.job_limits WHERE workspace_id=w FOR UPDATE;
 IF lim.stopped THEN RETURN false; END IF;
 SELECT * INTO j FROM sal_ops.jobs WHERE workspace_id=w AND delivery_tool IS NULL AND id=p_id AND state='running' AND lease_id=p_lease AND lease_until>clock_timestamp() FOR UPDATE;
 IF NOT FOUND OR NOT EXISTS(SELECT 1 FROM sal_ops.agent_controls WHERE workspace_id=w AND category=j.category AND NOT paused) THEN RETURN false; END IF;
 IF p_result IS NOT NULL AND (jsonb_typeof(p_result)<>'object' OR p_result->>'scope' IS DISTINCT FROM 'synthetic'
 OR p_result->>'category' IS DISTINCT FROM j.category OR p_result->'external_action' IS DISTINCT FROM 'false'::jsonb OR p_result->'verified_completion' IS DISTINCT FROM 'false'::jsonb
 OR octet_length(p_result::text)>16384 OR COALESCE(p_result->>'status','') NOT IN ('needs_evidence','ready_for_independent_review')) THEN RAISE EXCEPTION 'invalid result'; END IF;
 UPDATE sal_ops.jobs SET state=CASE WHEN p_result IS NOT NULL THEN 'succeeded' WHEN attempts>=3 THEN 'failed' ELSE 'queued' END,
 result=p_result,lease_id=NULL,lease_until=NULL,available_at=clock_timestamp()+make_interval(secs=>power(2,attempts)::int),updated_at=clock_timestamp() WHERE id=j.id;
 RETURN true;
END $$;

CREATE FUNCTION public.sal_submit_evidence_job(p_slug text,p_category text,p_key text,p_refs jsonb)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; who uuid:=auth.uid(); tool text; j sal_ops.jobs%ROWTYPE;
BEGIN
 SELECT m.workspace_id INTO w FROM sal_ops.members m JOIN sal_ops.workspaces s ON s.id=m.workspace_id
 WHERE s.slug=p_slug AND m.user_id=who AND m.role='founder';
 IF w IS NULL THEN RAISE EXCEPTION 'founder required' USING ERRCODE='42501'; END IF;
 tool:=CASE
  WHEN p_category IN ('engineering','technical_writing') THEN 'git_revision'
  WHEN p_category IN ('research','market_research','competitive_intelligence') THEN 'research_export'
  WHEN p_category IN ('marketing_analytics','observability','data_engineering') THEN 'analytics_export'
  WHEN p_category IN ('knowledge_ops','compliance','content_strategy') THEN 'document_export'
 END;
 IF tool IS NULL OR jsonb_typeof(p_refs) IS DISTINCT FROM 'object'
    OR p_refs='{}'::jsonb OR octet_length(p_refs::text)>8192 THEN
  RAISE EXCEPTION 'invalid evidence request';
 END IF;
 INSERT INTO sal_ops.jobs(workspace_id,category,request_key,requested_by,evidence,delivery_tool)
 VALUES(w,p_category,p_key,who,p_refs,tool) ON CONFLICT(workspace_id,request_key) DO NOTHING
 RETURNING * INTO j;
 IF NOT FOUND THEN
  SELECT * INTO STRICT j FROM sal_ops.jobs WHERE workspace_id=w AND request_key=p_key;
  IF j.category IS DISTINCT FROM p_category OR j.delivery_tool IS DISTINCT FROM tool
     OR j.evidence IS DISTINCT FROM p_refs THEN RAISE EXCEPTION 'request key conflict'; END IF;
 END IF;
 RETURN j.id;
END $$;

CREATE FUNCTION sal_ops.claim_evidence_job() RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; lim sal_ops.job_limits%ROWTYPE; j sal_ops.jobs%ROWTYPE;
BEGIN
 SELECT id INTO STRICT w FROM sal_ops.workspaces WHERE slug=sal_ops.bound_worker_slug();
 SELECT * INTO STRICT lim FROM sal_ops.job_limits WHERE workspace_id=w FOR UPDATE;
 IF lim.stopped THEN RETURN NULL; END IF;
 UPDATE sal_ops.jobs SET state=CASE WHEN attempts>=3 THEN 'failed' ELSE 'queued' END,
   lease_id=NULL,lease_until=NULL,available_at=clock_timestamp()+make_interval(secs=>power(2,attempts)::int),updated_at=clock_timestamp()
   WHERE workspace_id=w AND state='running' AND delivery_tool IS NOT NULL AND lease_until<=clock_timestamp();
 IF lim.attempts_used>=lim.attempt_limit THEN RETURN NULL; END IF;
 SELECT q.* INTO j FROM sal_ops.jobs q JOIN sal_ops.agent_controls a ON a.workspace_id=q.workspace_id AND a.category=q.category
 WHERE q.workspace_id=w AND q.delivery_tool IS NOT NULL AND q.state='queued' AND q.approved_by IS NOT NULL AND NOT a.paused
 AND q.available_at<=clock_timestamp() AND q.attempts<3 ORDER BY q.created_at,q.id LIMIT 1 FOR UPDATE OF q SKIP LOCKED;
 IF NOT FOUND THEN RETURN NULL; END IF;
 UPDATE sal_ops.job_limits SET attempts_used=attempts_used+1 WHERE workspace_id=w;
 UPDATE sal_ops.jobs SET state='running',attempts=attempts+1,lease_id=gen_random_uuid(),lease_until=clock_timestamp()+interval '60 seconds',updated_at=clock_timestamp()
 WHERE id=j.id RETURNING * INTO j;
 RETURN jsonb_build_object('id',j.id,'lease_id',j.lease_id,'category',j.category,'evidence',j.evidence,'tool',j.delivery_tool);
END $$;

CREATE FUNCTION sal_ops.finish_evidence_job(p_id uuid,p_lease uuid,p_body jsonb)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; lim sal_ops.job_limits%ROWTYPE; j sal_ops.jobs%ROWTYPE;
BEGIN
 SELECT id INTO STRICT w FROM sal_ops.workspaces WHERE slug=sal_ops.bound_worker_slug();
 SELECT * INTO STRICT lim FROM sal_ops.job_limits WHERE workspace_id=w FOR UPDATE;
 IF p_body IS NOT NULL AND EXISTS (
  SELECT 1 FROM sal_ops.agent_deliverables
  WHERE workspace_id=w AND job_id=p_id AND commit_lease=p_lease AND body=p_body
 ) THEN RETURN true; END IF;
 IF lim.stopped THEN RETURN false; END IF;
 SELECT * INTO j FROM sal_ops.jobs WHERE workspace_id=w AND id=p_id
  AND delivery_tool IS NOT NULL AND approved_by IS NOT NULL
  AND state='running' AND lease_id=p_lease AND lease_until>clock_timestamp() FOR UPDATE;
 IF NOT FOUND OR NOT EXISTS(
  SELECT 1 FROM sal_ops.agent_controls WHERE workspace_id=w AND category=j.category AND NOT paused
 ) THEN RETURN false; END IF;
 IF p_body IS NOT NULL THEN
  IF p_body->'recorded_evidence' IS DISTINCT FROM j.evidence THEN RAISE EXCEPTION 'evidence mismatch'; END IF;
  INSERT INTO sal_ops.agent_deliverables(workspace_id,job_id,category,tool,body,commit_lease)
  VALUES(w,j.id,j.category,j.delivery_tool,p_body,p_lease);
 END IF;
 UPDATE sal_ops.jobs SET state=CASE WHEN p_body IS NOT NULL THEN 'succeeded'
  WHEN attempts>=3 THEN 'failed' ELSE 'queued' END,
  lease_id=NULL,lease_until=NULL,available_at=clock_timestamp()+make_interval(secs=>power(2,attempts)::int),
  updated_at=clock_timestamp() WHERE id=j.id;
 RETURN true;
END $$;

REVOKE ALL ON FUNCTION public.sal_submit_evidence_job(text,text,text,jsonb),
 sal_ops.claim_evidence_job(),sal_ops.finish_evidence_job(uuid,uuid,jsonb)
 FROM PUBLIC,anon,authenticated,service_role,sal_job_worker,sal_hourly_worker;
GRANT EXECUTE ON FUNCTION public.sal_submit_evidence_job(text,text,text,jsonb) TO authenticated;
GRANT EXECUTE ON FUNCTION sal_ops.claim_evidence_job(),sal_ops.finish_evidence_job(uuid,uuid,jsonb)
 TO sal_hourly_worker;
COMMIT;
