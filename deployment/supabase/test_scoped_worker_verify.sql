DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM sal_ops.jobs WHERE request_key='scoped-worker-acceptance' AND state='succeeded' AND result->>'scope'='synthetic') THEN RAISE EXCEPTION 'real scoped login job missing'; END IF;
 IF NOT EXISTS(SELECT 1 FROM sal_ops.run_reports WHERE source='github_worker' AND run_id='100:1' AND summary->'worker_reported_counts'->>'claimed'='1') THEN RAISE EXCEPTION 'worker heartbeat missing'; END IF;
 IF (SELECT count(*) FROM sal_ops.run_reports WHERE source='github_worker' AND run_id='100:1')<>1 THEN RAISE EXCEPTION 'duplicate heartbeat'; END IF;
 IF EXISTS(SELECT 1 FROM sal_ops.jobs WHERE workspace_id='22222222-2222-2222-2222-222222222222') THEN RAISE EXCEPTION 'other workspace changed'; END IF;
END $$;
SELECT 'scoped Python worker acceptance passed';
