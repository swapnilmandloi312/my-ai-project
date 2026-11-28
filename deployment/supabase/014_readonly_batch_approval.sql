BEGIN;
CREATE FUNCTION public.sal_approve_readonly_evidence_batch(p_slug text,p_jobs uuid[])
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; who uuid:=auth.uid(); job_id uuid; approved jsonb:='[]'::jsonb;
BEGIN
 SELECT m.workspace_id INTO w FROM sal_ops.members m JOIN sal_ops.workspaces s ON s.id=m.workspace_id
 WHERE s.slug=p_slug AND m.user_id=who AND m.role='founder';
 IF w IS NULL THEN RAISE EXCEPTION 'founder required' USING ERRCODE='42501'; END IF;
 IF p_jobs IS NULL OR cardinality(p_jobs) NOT BETWEEN 1 AND 8 OR array_ndims(p_jobs)<>1 OR
   (SELECT count(DISTINCT id) FROM unnest(p_jobs) AS ids(id))<>cardinality(p_jobs)
 THEN RAISE EXCEPTION 'select one to eight distinct job IDs'; END IF;
 PERFORM 1 FROM sal_ops.job_limits WHERE workspace_id=w FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'workspace controls missing'; END IF;

 FOR job_id IN SELECT id FROM unnest(p_jobs) AS ids(id) ORDER BY id LOOP
  PERFORM 1 FROM sal_ops.jobs j WHERE j.workspace_id=w AND j.id=job_id
   AND j.state='pending' AND j.approved_by IS NULL AND j.attempts=0
   AND j.delivery_tool IN ('git_revision','workspace_operations','crossref_doi')
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'batch contains an ineligible job'; END IF;
  approved:=approved || jsonb_build_array(sal_ops.job_command(p_slug,'approve',jsonb_build_object('id',job_id)));
  INSERT INTO sal_ops.job_events(workspace_id,job_id,event,detail)
  VALUES(w,job_id,'batch_approval',jsonb_build_object('batch_size',cardinality(p_jobs)));
 END LOOP;
 RETURN approved;
END $$;
REVOKE ALL ON FUNCTION public.sal_approve_readonly_evidence_batch(text,uuid[])
 FROM PUBLIC,anon,authenticated,service_role,sal_job_worker,sal_hourly_worker;
GRANT EXECUTE ON FUNCTION public.sal_approve_readonly_evidence_batch(text,uuid[]) TO authenticated;
COMMIT;
