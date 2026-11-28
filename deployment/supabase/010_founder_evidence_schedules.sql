-- Founder-managed plans only materialize pending evidence jobs. Every occurrence
-- still needs the existing founder approval and worker attempt controls.
BEGIN;

CREATE TABLE sal_ops.evidence_schedules (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 workspace_id uuid NOT NULL REFERENCES sal_ops.workspaces(id),
 schedule_key text NOT NULL CHECK (length(schedule_key) BETWEEN 1 AND 64),
 template_job uuid NOT NULL REFERENCES sal_ops.jobs(id),
 depends_on_job uuid REFERENCES sal_ops.jobs(id),
 created_by uuid NOT NULL REFERENCES auth.users(id),
 interval_hours integer NOT NULL CHECK (interval_hours BETWEEN 1 AND 168),
 next_due timestamptz NOT NULL,
 last_job uuid REFERENCES sal_ops.jobs(id),
 enabled boolean NOT NULL DEFAULT true,
 UNIQUE (workspace_id,schedule_key)
);
ALTER TABLE sal_ops.evidence_schedules ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON sal_ops.evidence_schedules
 FROM PUBLIC,anon,authenticated,service_role,sal_job_worker,sal_hourly_worker;

CREATE FUNCTION public.sal_evidence_schedule(
 p_slug text,p_key text,p_template uuid,p_dependency uuid,p_interval_hours int
) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; who uuid:=auth.uid(); s sal_ops.evidence_schedules%ROWTYPE;
BEGIN
 SELECT m.workspace_id INTO w FROM sal_ops.members m
 JOIN sal_ops.workspaces ws ON ws.id=m.workspace_id
 WHERE ws.slug=p_slug AND m.user_id=who AND m.role='founder';
 IF w IS NULL THEN RAISE EXCEPTION 'founder required' USING ERRCODE='42501'; END IF;
 IF p_key IS NULL OR p_key !~ '^[a-zA-Z0-9_-]{1,64}$' OR p_interval_hours IS NULL
    OR p_interval_hours NOT BETWEEN 1 AND 168
    OR NOT EXISTS (
     SELECT 1 FROM sal_ops.jobs WHERE workspace_id=w AND id=p_template
     AND delivery_tool='git_revision' AND approved_by IS NOT NULL
    ) OR (p_dependency IS NOT NULL AND NOT EXISTS (
     SELECT 1 FROM sal_ops.jobs WHERE workspace_id=w AND id=p_dependency
    ))
 THEN RAISE EXCEPTION 'invalid schedule'; END IF;
 PERFORM 1 FROM sal_ops.job_limits WHERE workspace_id=w FOR UPDATE;
 SELECT * INTO s FROM sal_ops.evidence_schedules WHERE workspace_id=w AND schedule_key=p_key;
 IF FOUND THEN
  IF s.template_job IS DISTINCT FROM p_template OR s.depends_on_job IS DISTINCT FROM p_dependency
     OR s.interval_hours IS DISTINCT FROM p_interval_hours
  THEN RAISE EXCEPTION 'schedule key conflict'; END IF;
  RETURN s.id;
 END IF;
 IF (SELECT count(*) FROM sal_ops.evidence_schedules WHERE workspace_id=w AND enabled)>=40
 THEN RAISE EXCEPTION 'enabled schedule limit reached'; END IF;
 INSERT INTO sal_ops.evidence_schedules(
  workspace_id,schedule_key,template_job,depends_on_job,created_by,interval_hours,next_due
 ) VALUES (
  w,p_key,p_template,p_dependency,who,p_interval_hours,clock_timestamp()
 ) RETURNING * INTO s;
 RETURN s.id;
END $$;

CREATE FUNCTION public.sal_stop_evidence_schedule(p_slug text,p_key text)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid;
BEGIN
 SELECT m.workspace_id INTO w FROM sal_ops.members m
 JOIN sal_ops.workspaces ws ON ws.id=m.workspace_id
 WHERE ws.slug=p_slug AND m.user_id=auth.uid() AND m.role='founder';
 IF w IS NULL THEN RAISE EXCEPTION 'founder required' USING ERRCODE='42501'; END IF;
 PERFORM 1 FROM sal_ops.job_limits WHERE workspace_id=w FOR UPDATE;
 UPDATE sal_ops.evidence_schedules SET enabled=false
 WHERE workspace_id=w AND schedule_key=p_key AND enabled;
 RETURN FOUND;
END $$;

CREATE FUNCTION sal_ops.materialize_github_evidence_schedules()
RETURNS integer LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; lim sal_ops.job_limits%ROWTYPE; plan record; new_job uuid;
        slots integer; materialized integer:=0; tick timestamptz:=clock_timestamp();
BEGIN
 SELECT id INTO STRICT w FROM sal_ops.workspaces WHERE slug=sal_ops.bound_worker_slug();
 SELECT * INTO STRICT lim FROM sal_ops.job_limits WHERE workspace_id=w FOR UPDATE;
 IF lim.stopped OR lim.attempts_used>=lim.attempt_limit THEN RETURN 0; END IF;
 SELECT greatest(0,100-count(*))::int INTO slots FROM sal_ops.jobs
 WHERE workspace_id=w AND state IN ('pending','queued','running');
 FOR plan IN
  SELECT s.*, t.category,t.evidence,t.delivery_tool
  FROM sal_ops.evidence_schedules s
  JOIN sal_ops.jobs t ON t.workspace_id=s.workspace_id AND t.id=s.template_job
  JOIN sal_ops.agent_controls a ON a.workspace_id=t.workspace_id AND a.category=t.category
  JOIN sal_ops.members m ON m.workspace_id=s.workspace_id AND m.user_id=s.created_by AND m.role='founder'
  WHERE s.workspace_id=w AND s.enabled AND s.next_due<=tick AND NOT a.paused
  AND t.delivery_tool='git_revision' AND t.approved_by IS NOT NULL
  AND (s.depends_on_job IS NULL OR EXISTS (
   SELECT 1 FROM sal_ops.jobs j WHERE j.id=s.depends_on_job AND j.workspace_id=w AND j.state='succeeded'
  ))
  AND NOT EXISTS (
   SELECT 1 FROM sal_ops.jobs j WHERE j.id=s.last_job AND j.workspace_id=w
   AND j.state IN ('pending','queued','running')
  )
  ORDER BY s.next_due,s.id LIMIT least(slots,4)
 LOOP
  new_job:=gen_random_uuid();
  INSERT INTO sal_ops.jobs(id,workspace_id,category,request_key,parent_id,requested_by,evidence,delivery_tool)
  VALUES(new_job,w,plan.category,'scheduled:'||new_job,plan.depends_on_job,
         plan.created_by,plan.evidence,plan.delivery_tool);
  UPDATE sal_ops.evidence_schedules
  SET last_job=new_job, next_due=tick+make_interval(hours=>plan.interval_hours)
  WHERE id=plan.id;
  materialized:=materialized+1;
 END LOOP;
 RETURN materialized;
END $$;

CREATE FUNCTION public.sal_evidence_schedule_index(p_slug text)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $
DECLARE w uuid; result jsonb;
BEGIN
 SELECT m.workspace_id INTO w FROM sal_ops.members m
 JOIN sal_ops.workspaces ws ON ws.id=m.workspace_id
 WHERE ws.slug=p_slug AND m.user_id=auth.uid();
 IF w IS NULL THEN RAISE EXCEPTION 'workspace member required' USING ERRCODE='42501'; END IF;
 SELECT coalesce(jsonb_agg(to_jsonb(plan) ORDER BY plan.next_due,plan.id),'[]'::jsonb)
 INTO result FROM (
  SELECT s.id,s.schedule_key,t.category,s.interval_hours,s.next_due,s.last_job,
         s.enabled,s.depends_on_job,j.state AS dependency_state
  FROM sal_ops.evidence_schedules s
  JOIN sal_ops.jobs t ON t.id=s.template_job AND t.workspace_id=s.workspace_id
  LEFT JOIN sal_ops.jobs j ON j.id=s.depends_on_job AND j.workspace_id=s.workspace_id
  WHERE s.workspace_id=w ORDER BY s.next_due,s.id LIMIT 100
 ) plan;
 RETURN result;
END $;

REVOKE ALL ON FUNCTION public.sal_evidence_schedule_index(text),public.sal_evidence_schedule(text,text,uuid,uuid,int),
 public.sal_stop_evidence_schedule(text,text),sal_ops.materialize_github_evidence_schedules()
 FROM PUBLIC,anon,authenticated,service_role,sal_job_worker,sal_hourly_worker;
GRANT EXECUTE ON FUNCTION public.sal_evidence_schedule_index(text),public.sal_evidence_schedule(text,text,uuid,uuid,int),
 public.sal_stop_evidence_schedule(text,text) TO authenticated;
GRANT EXECUTE ON FUNCTION sal_ops.materialize_github_evidence_schedules() TO sal_hourly_worker;
COMMIT;
