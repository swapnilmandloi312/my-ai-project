BEGIN;
ALTER TABLE sal_ops.jobs DROP CONSTRAINT jobs_delivery_tool_check,
 ADD CONSTRAINT jobs_delivery_tool_check CHECK (delivery_tool IN
 ('git_revision','research_export','analytics_export','document_export','workspace_operations','crossref_doi'));
ALTER TABLE sal_ops.agent_deliverables DROP CONSTRAINT agent_deliverables_tool_check,
 ADD CONSTRAINT agent_deliverables_tool_check CHECK (tool IN
 ('git_revision','research_export','analytics_export','document_export','workspace_operations','crossref_doi'));

CREATE OR REPLACE FUNCTION public.sal_submit_evidence_job(p_slug text,p_category text,p_key text,p_refs jsonb)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; who uuid:=auth.uid(); tool text; j sal_ops.jobs%ROWTYPE;
BEGIN
 SELECT m.workspace_id INTO w FROM sal_ops.members m JOIN sal_ops.workspaces s ON s.id=m.workspace_id
 WHERE s.slug=p_slug AND m.user_id=who AND m.role='founder';
 IF w IS NULL THEN RAISE EXCEPTION 'founder required' USING ERRCODE='42501'; END IF;
 tool:=CASE
  WHEN p_category='research' AND p_refs=jsonb_build_object('doi',p_refs->>'doi')
   AND jsonb_typeof(p_refs->'doi')='string' AND length(p_refs->>'doi')<=180
   AND (p_refs->>'doi') ~* '^10\.[0-9]{4,9}/[-._;()/:A-Z0-9]+
  WHEN p_category IN ('security','privacy','compliance','it_ops','observability','incident_response','integration') AND p_refs='{"snapshot":"workspace"}'::jsonb THEN 'workspace_operations'
  WHEN p_category IN ('engineering','technical_writing','architecture','automation','backend','devops','frontend','quality') THEN 'git_revision'
  WHEN p_category IN ('research','market_research','competitive_intelligence') AND NOT (p_refs ? 'doi') THEN 'research_export'
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
END $$; THEN 'crossref_doi'
  WHEN p_category IN ('security','privacy','compliance','it_ops','observability','incident_response','integration') AND p_refs='{"snapshot":"workspace"}'::jsonb THEN 'workspace_operations'
  WHEN p_category IN ('engineering','technical_writing','architecture','automation','backend','devops','frontend','quality') THEN 'git_revision'
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

CREATE FUNCTION sal_ops.claim_crossref_evidence_job() RETURNS jsonb
LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$
 SELECT sal_ops.claim_evidence_job_for_tool('crossref_doi');
$$;
REVOKE ALL ON FUNCTION sal_ops.claim_crossref_evidence_job()
 FROM PUBLIC,anon,authenticated,service_role,sal_job_worker,sal_hourly_worker;
GRANT EXECUTE ON FUNCTION sal_ops.claim_crossref_evidence_job() TO sal_hourly_worker;
COMMIT;
