BEGIN;
ALTER TABLE sal_ops.evidence_schedules
 ADD COLUMN approval_founder uuid REFERENCES auth.users(id),
 ADD COLUMN approval_until timestamptz,
 ADD COLUMN approval_remaining int NOT NULL DEFAULT 0 CHECK (approval_remaining BETWEEN 0 AND 24);

-- A founder authorizes bounded repeats of their own existing, approved GitHub template.
-- Revoke with zero occurrences. The worker cannot invoke this function.
CREATE FUNCTION public.sal_set_recurring_evidence_approval(
 p_slug text,p_key text,p_occurrences int,p_hours int
) RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; who uuid:=auth.uid();
BEGIN
 SELECT m.workspace_id INTO w FROM sal_ops.members m JOIN sal_ops.workspaces s ON s.id=m.workspace_id
 WHERE s.slug=p_slug AND m.user_id=who AND m.role='founder';
 IF w IS NULL THEN RAISE EXCEPTION 'founder required' USING ERRCODE='42501'; END IF;
 IF p_occurrences IS NULL OR p_occurrences NOT BETWEEN 0 AND 24
 OR (p_occurrences>0 AND (p_hours IS NULL OR p_hours NOT BETWEEN 1 AND 24))
 THEN RAISE EXCEPTION 'invalid policy bounds'; END IF;
 PERFORM 1 FROM sal_ops.job_limits WHERE workspace_id=w FOR UPDATE;
 UPDATE sal_ops.evidence_schedules p SET approval_remaining=p_occurrences,
   approval_until=CASE WHEN p_occurrences>0 THEN clock_timestamp()+make_interval(hours=>p_hours) END,
   approval_founder=CASE WHEN p_occurrences>0 THEN who END
 FROM sal_ops.jobs j
 WHERE p.workspace_id=w AND p.schedule_key=p_key AND p.created_by=who AND p.enabled
 AND j.workspace_id=w AND j.id=p.template_job AND j.approved_by IS NOT NULL
 AND j.delivery_tool='git_revision' AND j.evidence->>'source_revision' ~ '^[0-9a-f]{40}$';
 RETURN FOUND;
END $$;
REVOKE ALL ON FUNCTION public.sal_set_recurring_evidence_approval(text,text,int,int)
 FROM PUBLIC,anon,authenticated,service_role,sal_job_worker,sal_hourly_worker;
GRANT EXECUTE ON FUNCTION public.sal_set_recurring_evidence_approval(text,text,int,int) TO authenticated;

CREATE OR REPLACE FUNCTION sal_ops.materialize_github_evidence_schedules()
RETURNS integer LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; lim sal_ops.job_limits%ROWTYPE; plan record; new_job uuid;
        slots integer; policy_approver uuid; materialized integer:=0; tick timestamptz:=clock_timestamp();
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
  policy_approver:=NULL;
  IF plan.approval_remaining>0 AND plan.approval_until>tick THEN
   policy_approver:=plan.approval_founder;
  END IF;
  new_job:=gen_random_uuid();
  INSERT INTO sal_ops.jobs(id,workspace_id,category,request_key,parent_id,requested_by,evidence,delivery_tool,approved_by,state)
  VALUES(new_job,w,plan.category,'scheduled:'||new_job,plan.depends_on_job,
         plan.created_by,plan.evidence,plan.delivery_tool,policy_approver,
         CASE WHEN policy_approver IS NULL THEN 'pending' ELSE 'queued' END);
  IF policy_approver IS NOT NULL THEN
   INSERT INTO sal_ops.job_events(workspace_id,job_id,event,detail)
   VALUES(w,new_job,'recurring_approval',jsonb_build_object('schedule_id',plan.id,'remaining_after',plan.approval_remaining-1));
  END IF;
  UPDATE sal_ops.evidence_schedules
  SET last_job=new_job, next_due=tick+make_interval(hours=>plan.interval_hours),
      approval_remaining=approval_remaining-CASE WHEN policy_approver IS NULL THEN 0 ELSE 1 END
  WHERE id=plan.id;
  materialized:=materialized+1;
 END LOOP;
 RETURN materialized;
END $$;


COMMIT;
