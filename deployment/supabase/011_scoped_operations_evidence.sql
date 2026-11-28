BEGIN;
ALTER TABLE sal_ops.jobs DROP CONSTRAINT jobs_delivery_tool_check,
 ADD CONSTRAINT jobs_delivery_tool_check CHECK (delivery_tool IN
 ('git_revision','research_export','analytics_export','document_export','workspace_operations'));
ALTER TABLE sal_ops.agent_deliverables DROP CONSTRAINT agent_deliverables_tool_check,
 ADD CONSTRAINT agent_deliverables_tool_check CHECK (tool IN
 ('git_revision','research_export','analytics_export','document_export','workspace_operations'));

CREATE OR REPLACE FUNCTION public.sal_submit_evidence_job(p_slug text,p_category text,p_key text,p_refs jsonb)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; who uuid:=auth.uid(); tool text; j sal_ops.jobs%ROWTYPE;
BEGIN
 SELECT m.workspace_id INTO w FROM sal_ops.members m JOIN sal_ops.workspaces s ON s.id=m.workspace_id
 WHERE s.slug=p_slug AND m.user_id=who AND m.role='founder';
 IF w IS NULL THEN RAISE EXCEPTION 'founder required' USING ERRCODE='42501'; END IF;
 tool:=CASE
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


CREATE FUNCTION sal_ops.claim_operations_evidence_job() RETURNS jsonb
LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$
 SELECT sal_ops.claim_evidence_job_for_tool('workspace_operations');
$$;

CREATE FUNCTION sal_ops.operations_evidence(p_id uuid,p_lease uuid) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE w uuid; j sal_ops.jobs%ROWTYPE; payload jsonb;
BEGIN
 SELECT id INTO STRICT w FROM sal_ops.workspaces WHERE slug=sal_ops.bound_worker_slug();
 SELECT q.* INTO j FROM sal_ops.jobs q
 JOIN sal_ops.job_limits l ON l.workspace_id=q.workspace_id
 JOIN sal_ops.agent_controls a ON a.workspace_id=q.workspace_id AND a.category=q.category
 WHERE q.workspace_id=w AND q.id=p_id AND q.lease_id=p_lease AND q.lease_until>statement_timestamp()
 AND q.state='running' AND q.approved_by IS NOT NULL AND q.delivery_tool='workspace_operations'
 AND NOT l.stopped AND NOT a.paused;
 IF NOT FOUND THEN RAISE EXCEPTION 'active operations lease required' USING ERRCODE='42501'; END IF;

 CASE j.category
 WHEN 'security' THEN
  SELECT jsonb_build_object('kind','execution_control_audit','workspace_stopped',l.stopped,
    'positive_spend_enabled',coalesce((SELECT enabled AND cap_microusd>0 FROM sal_ops.spend_limits WHERE workspace_id=w),false),
    'active_worker_bindings',(SELECT count(*) FROM sal_ops.worker_bindings WHERE workspace_id=w AND enabled),
    'unapproved_running',(SELECT count(*) FROM sal_ops.jobs WHERE workspace_id=w AND state='running' AND approved_by IS NULL))
  INTO payload FROM sal_ops.job_limits l WHERE l.workspace_id=w;
 WHEN 'privacy' THEN
  SELECT jsonb_build_object('kind','deliverable_access_review',
   'authenticated_direct_read',has_table_privilege('authenticated','sal_ops.agent_deliverables','SELECT'),
   'anonymous_index_access',has_function_privilege('anon','public.sal_agent_deliverable_index(text)','EXECUTE'),
   'stored_deliverables',count(*),'oldest_deliverable_at',min(stored_at))
  INTO payload FROM sal_ops.agent_deliverables WHERE workspace_id=w;
 WHEN 'compliance' THEN
  SELECT jsonb_build_object('kind','approval_traceability',
   'stored_deliverables',count(*),'with_approval',count(*) FILTER (WHERE q.approved_by IS NOT NULL),
   'with_success_event',count(*) FILTER (WHERE EXISTS (
     SELECT FROM sal_ops.job_events e WHERE e.workspace_id=w AND e.job_id=q.id AND e.event='succeeded')))
  INTO payload FROM sal_ops.agent_deliverables d JOIN sal_ops.jobs q ON q.id=d.job_id WHERE d.workspace_id=w;
 WHEN 'it_ops' THEN
  SELECT jsonb_build_object('kind','agent_control_inventory','total_agents',count(*),
   'paused_categories',coalesce(jsonb_agg(category ORDER BY category) FILTER (WHERE paused),'[]'::jsonb),
   'enabled_categories',coalesce(jsonb_agg(category ORDER BY category) FILTER (WHERE NOT paused),'[]'::jsonb))
  INTO payload FROM sal_ops.agent_controls WHERE workspace_id=w;
 WHEN 'observability' THEN
  SELECT jsonb_build_object('kind','queue_health_window','window_hours',24,
   'by_state',coalesce(jsonb_object_agg(state,total),'{}'::jsonb))
  INTO payload FROM (SELECT state,count(*) total FROM sal_ops.jobs WHERE workspace_id=w
   AND updated_at>=statement_timestamp()-interval '24 hours' GROUP BY state) q;
 WHEN 'incident_response' THEN
  SELECT jsonb_build_object('kind','queue_incident_triage','window_hours',24,
   'recent_failures',count(*) FILTER (WHERE state='failed' AND updated_at>=statement_timestamp()-interval '24 hours'),
   'expired_running_leases',count(*) FILTER (WHERE state='running' AND lease_until<=statement_timestamp()),
   'last_failure_at',max(updated_at) FILTER (WHERE state='failed'))
  INTO payload FROM sal_ops.jobs WHERE workspace_id=w;
 WHEN 'integration' THEN
  SELECT jsonb_build_object('kind','adapter_delivery_inventory','deliverables_by_tool',
   coalesce(jsonb_object_agg(tool,total),'{}'::jsonb))
  INTO payload FROM (SELECT tool,count(*) total FROM sal_ops.agent_deliverables WHERE workspace_id=w GROUP BY tool) d;
 ELSE RAISE EXCEPTION 'unsupported operations category';
 END CASE;
 RETURN payload || jsonb_build_object('observed_at',statement_timestamp(),'source','workspace_operations');
END $$;
REVOKE ALL ON FUNCTION sal_ops.claim_operations_evidence_job(),sal_ops.operations_evidence(uuid,uuid)
 FROM PUBLIC,anon,authenticated,service_role,sal_job_worker,sal_hourly_worker;
GRANT EXECUTE ON FUNCTION sal_ops.claim_operations_evidence_job(),sal_ops.operations_evidence(uuid,uuid)
 TO sal_hourly_worker;
COMMIT;
