DO $$ BEGIN
 IF NOT EXISTS (
  SELECT 1 FROM sal_ops.jobs j JOIN sal_ops.agent_deliverables d ON d.job_id=j.id
  WHERE j.request_key='evidence-test' AND j.state='succeeded' AND j.attempts=1
  AND d.commit_lease IS NOT NULL AND d.body->'recorded_evidence'->>'hypothesis'='approved:fixture'
  AND EXISTS (SELECT 1 FROM sal_ops.job_events e WHERE e.job_id=j.id AND e.event='succeeded')
 ) THEN RAISE EXCEPTION 'approved evidence job missing deliverable or event'; END IF;
END $$;
