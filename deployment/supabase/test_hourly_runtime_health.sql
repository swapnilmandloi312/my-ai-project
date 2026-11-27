DO $$
DECLARE a jsonb; b jsonb; before_state jsonb; after_state jsonb;
BEGIN
 SELECT to_jsonb(l) INTO before_state FROM sal_ops.job_limits l JOIN sal_ops.workspaces w ON w.id=l.workspace_id WHERE w.slug='test-workspace';
 a:=sal_ops.collect_runtime_health('test-workspace');
 b:=sal_ops.collect_runtime_health('test-workspace');
 IF a->>'inserted'<>'true' OR b->>'inserted'<>'false' THEN RAISE EXCEPTION 'idempotency'; END IF;
 IF (a->'metrics'->>'founder_count')::int<>1 OR (a->'metrics'->>'production_agent_execution')::boolean THEN RAISE EXCEPTION 'metric mismatch'; END IF;
 SELECT to_jsonb(l) INTO after_state FROM sal_ops.job_limits l JOIN sal_ops.workspaces w ON w.id=l.workspace_id WHERE w.slug='test-workspace';
 IF before_state IS DISTINCT FROM after_state THEN RAISE EXCEPTION 'queue mutation'; END IF;
 IF has_function_privilege('anon','sal_ops.collect_runtime_health(text)','EXECUTE') OR has_function_privilege('authenticated','sal_ops.collect_runtime_health(text)','EXECUTE') OR has_function_privilege('sal_job_worker','sal_ops.collect_runtime_health(text)','EXECUTE') THEN RAISE EXCEPTION 'collector exposed'; END IF;
 IF (SELECT count(*) FROM sal_ops.run_reports WHERE source='database_cron')<>1 THEN RAISE EXCEPTION 'report count'; END IF;
END $$;
SELECT 'hourly health acceptance passed' AS result;
