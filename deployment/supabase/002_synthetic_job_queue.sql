-- Additive migration candidate for the existing private sal_ops workspace.
-- Synthetic-only; never grants external tools or spends money.
BEGIN;
CREATE TABLE sal_ops.job_limits(
 workspace_id uuid PRIMARY KEY REFERENCES sal_ops.workspaces(id),
 stopped boolean NOT NULL DEFAULT true,
 attempt_limit integer NOT NULL DEFAULT 0 CHECK(attempt_limit BETWEEN 0 AND 1000),
 attempts_used integer NOT NULL DEFAULT 0 CHECK(attempts_used>=0)
);
INSERT INTO sal_ops.job_limits(workspace_id) SELECT id FROM sal_ops.workspaces;
CREATE TABLE sal_ops.jobs(
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 workspace_id uuid NOT NULL REFERENCES sal_ops.workspaces(id),
 category text NOT NULL REFERENCES sal_ops.agent_profiles(category),
 request_key text NOT NULL CHECK(length(request_key) BETWEEN 1 AND 100),
 parent_id uuid REFERENCES sal_ops.jobs(id),
 requested_by uuid NOT NULL REFERENCES auth.users(id),
 approved_by uuid REFERENCES auth.users(id),
 evidence jsonb NOT NULL CHECK(jsonb_typeof(evidence)='object' AND octet_length(evidence::text)<=8192),
 state text NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','queued','running','succeeded','failed','cancelled')),
 attempts integer NOT NULL DEFAULT 0 CHECK(attempts BETWEEN 0 AND 3),
 available_at timestamptz NOT NULL DEFAULT now(),
 lease_id uuid, lease_until timestamptz,
 result jsonb CHECK(result IS NULL OR (jsonb_typeof(result)='object' AND octet_length(result::text)<=16384)),
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(workspace_id,request_key)
);
CREATE INDEX jobs_claim_idx ON sal_ops.jobs(workspace_id,state,available_at);
CREATE TABLE sal_ops.job_events(
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 workspace_id uuid NOT NULL REFERENCES sal_ops.workspaces(id),
 job_id uuid REFERENCES sal_ops.jobs(id),
 event text NOT NULL, detail jsonb NOT NULL DEFAULT '{}',
 recorded_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE sal_ops.job_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE sal_ops.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE sal_ops.job_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON sal_ops.job_limits,sal_ops.jobs,sal_ops.job_events FROM PUBLIC,anon,authenticated,service_role;
-- No direct client access; private, checked functions only.
CREATE FUNCTION sal_ops.job_event() RETURNS trigger LANGUAGE plpgsql
 SET search_path=pg_catalog AS $$
BEGIN
 INSERT INTO sal_ops.job_events(workspace_id,job_id,event,detail)
 VALUES(NEW.workspace_id,NEW.id,NEW.state,jsonb_build_object('attempt',NEW.attempts));
 RETURN NEW;
END $$;
CREATE TRIGGER job_event AFTER INSERT OR UPDATE OF state ON sal_ops.jobs
 FOR EACH ROW EXECUTE FUNCTION sal_ops.job_event();

CREATE FUNCTION sal_ops.job_command(p_slug text,p_action text,p_args jsonb DEFAULT '{}')
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; who uuid:=auth.uid(); member_role text; j sal_ops.jobs%ROWTYPE;
 limits sal_ops.job_limits%ROWTYPE; cat text; refs jsonb; parent uuid; key text;
BEGIN
 SELECT m.workspace_id,m.role INTO w,member_role FROM sal_ops.members m
 JOIN sal_ops.workspaces s ON s.id=m.workspace_id WHERE s.slug=p_slug AND m.user_id=who;
 IF w IS NULL OR who IS NULL THEN RAISE EXCEPTION 'membership required' USING ERRCODE='42501'; END IF;
 IF p_action='snapshot' THEN
  RETURN jsonb_build_object('role',member_role,'limits',(SELECT to_jsonb(l)-'workspace_id' FROM sal_ops.job_limits l WHERE l.workspace_id=w),
    'jobs',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.created_at DESC) FROM
     (SELECT id,category,parent_id,state,attempts,result,created_at,updated_at FROM sal_ops.jobs WHERE workspace_id=w ORDER BY created_at DESC,id LIMIT 100) x),'[]'::jsonb),
    'events',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.id DESC) FROM
     (SELECT id,job_id,event,detail,recorded_at FROM sal_ops.job_events WHERE workspace_id=w ORDER BY id DESC LIMIT 200) x),'[]'::jsonb),
    'profiles',COALESCE((SELECT jsonb_agg(jsonb_build_object('category',category,'paused',paused) ORDER BY category) FROM sal_ops.agent_controls WHERE workspace_id=w),'[]'::jsonb));
 END IF;
 IF member_role NOT IN ('founder','operator') THEN RAISE EXCEPTION 'write denied' USING ERRCODE='42501'; END IF;
 IF p_args IS NULL OR jsonb_typeof(p_args)<>'object' OR octet_length(p_args::text)>12000 THEN RAISE EXCEPTION 'invalid arguments'; END IF;
 -- Serialize state changes and worker claims under a single workspace lock.
 SELECT * INTO STRICT limits FROM sal_ops.job_limits WHERE workspace_id=w FOR UPDATE;
 IF p_action='submit' THEN
  cat:=p_args->>'category'; key:=p_args->>'request_key'; refs:=p_args->'evidence';
  parent:=NULLIF(p_args->>'parent_id','')::uuid;
  IF key IS NULL OR length(key) NOT BETWEEN 1 AND 100 OR refs IS NULL OR jsonb_typeof(refs)<>'object' OR octet_length(refs::text)>8192
    OR NOT EXISTS(SELECT 1 FROM sal_ops.agent_controls WHERE workspace_id=w AND category=cat)
    OR EXISTS(SELECT 1 FROM jsonb_each(refs) e WHERE jsonb_typeof(e.value)<>'string' OR e.value#>>'{}' NOT LIKE 'synthetic:%' OR length(e.value#>>'{}')>200
      OR NOT EXISTS(SELECT 1 FROM sal_ops.agent_profiles p WHERE p.category=cat AND e.key=ANY(p.required_evidence))) THEN
    RAISE EXCEPTION 'invalid synthetic task';
  END IF;
  IF parent IS NOT NULL AND NOT EXISTS(SELECT 1 FROM sal_ops.jobs WHERE id=parent AND workspace_id=w AND state='succeeded') THEN RAISE EXCEPTION 'invalid parent'; END IF;
  SELECT * INTO j FROM sal_ops.jobs WHERE workspace_id=w AND request_key=key;
  IF FOUND THEN
    IF j.category IS DISTINCT FROM cat OR j.evidence IS DISTINCT FROM refs OR j.parent_id IS DISTINCT FROM parent OR j.requested_by IS DISTINCT FROM who THEN RAISE EXCEPTION 'request conflict'; END IF;
    RETURN jsonb_build_object('id',j.id,'state',j.state);
  END IF;
  IF (SELECT count(*) FROM sal_ops.jobs WHERE workspace_id=w AND state IN ('pending','queued','running'))>=100 THEN RAISE EXCEPTION 'queue full'; END IF;
  INSERT INTO sal_ops.jobs(workspace_id,category,request_key,parent_id,requested_by,evidence) VALUES(w,cat,key,parent,who,refs) RETURNING * INTO j;
  RETURN jsonb_build_object('id',j.id,'state',j.state);
 END IF;
 IF member_role<>'founder' THEN RAISE EXCEPTION 'founder required' USING ERRCODE='42501'; END IF;
 IF p_action='approve' THEN
  UPDATE sal_ops.jobs SET state='queued',approved_by=who,updated_at=clock_timestamp() WHERE id=(p_args->>'id')::uuid AND workspace_id=w AND state='pending' RETURNING * INTO j;
  IF NOT FOUND THEN RAISE EXCEPTION 'approval conflict'; END IF;
  RETURN jsonb_build_object('id',j.id,'state',j.state);
 ELSIF p_action='configure' THEN
  IF jsonb_typeof(p_args->'stopped') IS DISTINCT FROM 'boolean' OR jsonb_typeof(p_args->'attempt_limit') IS DISTINCT FROM 'number' THEN RAISE EXCEPTION 'invalid settings'; END IF;
  UPDATE sal_ops.job_limits SET stopped=(p_args->>'stopped')::boolean,attempt_limit=(p_args->>'attempt_limit')::integer WHERE workspace_id=w;
  IF (p_args->>'stopped')::boolean THEN
   UPDATE sal_ops.jobs SET state='cancelled',lease_id=NULL,lease_until=NULL,updated_at=clock_timestamp() WHERE workspace_id=w AND state IN ('pending','queued','running');
  END IF;
  INSERT INTO sal_ops.job_events(workspace_id,event,detail) VALUES(w,'configure',jsonb_build_object('actor',who,'stopped',p_args->'stopped','attempt_limit',p_args->'attempt_limit'));
 ELSIF p_action='agent_pause' THEN
  IF jsonb_typeof(p_args->'paused') IS DISTINCT FROM 'boolean' THEN RAISE EXCEPTION 'invalid pause'; END IF;
  UPDATE sal_ops.agent_controls SET paused=(p_args->>'paused')::boolean,revision=revision+1,updated_at=clock_timestamp() WHERE workspace_id=w AND category=p_args->>'category';
  IF NOT FOUND THEN RAISE EXCEPTION 'unknown category'; END IF;
  IF (p_args->>'paused')::boolean THEN
   UPDATE sal_ops.jobs SET state='cancelled',lease_id=NULL,lease_until=NULL,updated_at=clock_timestamp() WHERE workspace_id=w AND category=p_args->>'category' AND state IN ('pending','queued','running');
  END IF;
  INSERT INTO sal_ops.job_events(workspace_id,event,detail) VALUES(w,'agent_pause',jsonb_build_object('actor',who,'category',p_args->>'category','paused',p_args->'paused'));
 ELSE RAISE EXCEPTION 'unknown command';
 END IF;
 RETURN jsonb_build_object('ok',true);
END $$;

CREATE FUNCTION sal_ops.claim_job(p_slug text) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; lim sal_ops.job_limits%ROWTYPE; j sal_ops.jobs%ROWTYPE;
BEGIN
 SELECT id INTO STRICT w FROM sal_ops.workspaces WHERE slug=p_slug;
 SELECT * INTO STRICT lim FROM sal_ops.job_limits WHERE workspace_id=w FOR UPDATE;
 IF lim.stopped THEN RETURN NULL; END IF;
 UPDATE sal_ops.jobs SET state=CASE WHEN attempts>=3 THEN 'failed' ELSE 'queued' END,
   lease_id=NULL,lease_until=NULL,available_at=clock_timestamp()+make_interval(secs=>power(2,attempts)::int),updated_at=clock_timestamp()
   WHERE workspace_id=w AND state='running' AND lease_until<=clock_timestamp();
 IF lim.attempts_used>=lim.attempt_limit THEN RETURN NULL; END IF;
 SELECT q.* INTO j FROM sal_ops.jobs q JOIN sal_ops.agent_controls a ON a.workspace_id=q.workspace_id AND a.category=q.category
 WHERE q.workspace_id=w AND q.state='queued' AND q.approved_by IS NOT NULL AND NOT a.paused
 AND q.available_at<=clock_timestamp() AND q.attempts<3 ORDER BY q.created_at,q.id LIMIT 1 FOR UPDATE OF q SKIP LOCKED;
 IF NOT FOUND THEN RETURN NULL; END IF;
 UPDATE sal_ops.job_limits SET attempts_used=attempts_used+1 WHERE workspace_id=w;
 UPDATE sal_ops.jobs SET state='running',attempts=attempts+1,lease_id=gen_random_uuid(),lease_until=clock_timestamp()+interval '60 seconds',updated_at=clock_timestamp()
 WHERE id=j.id RETURNING * INTO j;
 RETURN jsonb_build_object('id',j.id,'lease_id',j.lease_id,'category',j.category,'evidence',j.evidence);
END $$;

CREATE FUNCTION sal_ops.finish_job(p_slug text,p_id uuid,p_lease uuid,p_result jsonb) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; lim sal_ops.job_limits%ROWTYPE; j sal_ops.jobs%ROWTYPE;
BEGIN
 SELECT id INTO STRICT w FROM sal_ops.workspaces WHERE slug=p_slug;
 SELECT * INTO STRICT lim FROM sal_ops.job_limits WHERE workspace_id=w FOR UPDATE;
 IF lim.stopped THEN RETURN false; END IF;
 SELECT * INTO j FROM sal_ops.jobs WHERE workspace_id=w AND id=p_id AND state='running' AND lease_id=p_lease AND lease_until>clock_timestamp() FOR UPDATE;
 IF NOT FOUND OR NOT EXISTS(SELECT 1 FROM sal_ops.agent_controls WHERE workspace_id=w AND category=j.category AND NOT paused) THEN RETURN false; END IF;
 IF p_result IS NOT NULL AND (jsonb_typeof(p_result)<>'object' OR p_result->>'scope' IS DISTINCT FROM 'synthetic'
 OR p_result->>'category' IS DISTINCT FROM j.category OR p_result->'external_action' IS DISTINCT FROM 'false'::jsonb OR p_result->'verified_completion' IS DISTINCT FROM 'false'::jsonb
 OR octet_length(p_result::text)>16384 OR COALESCE(p_result->>'status','') NOT IN ('needs_evidence','ready_for_independent_review')) THEN RAISE EXCEPTION 'invalid result'; END IF;
 UPDATE sal_ops.jobs SET state=CASE WHEN p_result IS NOT NULL THEN 'succeeded' WHEN attempts>=3 THEN 'failed' ELSE 'queued' END,
 result=p_result,lease_id=NULL,lease_until=NULL,available_at=clock_timestamp()+make_interval(secs=>power(2,attempts)::int),updated_at=clock_timestamp() WHERE id=j.id;
 RETURN true;
END $$;

-- Public wrapper is SECURITY INVOKER; privilege is restricted to the private function,
-- whose authorization is based on current workspace membership, not user metadata.
CREATE FUNCTION public.sal_job_command(p_slug text,p_action text,p_args jsonb DEFAULT '{}')
RETURNS jsonb LANGUAGE sql SECURITY INVOKER SET search_path=pg_catalog AS $$
 SELECT sal_ops.job_command(p_slug,p_action,p_args)
$$;
REVOKE ALL ON FUNCTION sal_ops.job_event(),sal_ops.job_command(text,text,jsonb),sal_ops.claim_job(text),sal_ops.finish_job(text,uuid,uuid,jsonb),public.sal_job_command(text,text,jsonb) FROM PUBLIC,anon,authenticated,service_role;
GRANT USAGE ON SCHEMA sal_ops TO authenticated;
GRANT EXECUTE ON FUNCTION sal_ops.job_command(text,text,jsonb),public.sal_job_command(text,text,jsonb) TO authenticated;
-- Dedicated NOLOGIN group; provisioning a credential is deliberately separate.
CREATE ROLE sal_job_worker NOLOGIN;
GRANT USAGE ON SCHEMA sal_ops TO sal_job_worker;
GRANT EXECUTE ON FUNCTION sal_ops.claim_job(text),sal_ops.finish_job(text,uuid,uuid,jsonb) TO sal_job_worker;
COMMIT;
