DO $$ BEGIN
 IF NOT EXISTS (SELECT FROM sal_ops.jobs j JOIN sal_ops.agent_deliverables d ON d.job_id=j.id
 WHERE j.request_key='crossref-ci' AND j.state='succeeded' AND j.attempts=1 AND j.approved_by IS NOT NULL
 AND d.tool='crossref_doi' AND d.body->'source_evidence'->>'doi'='10.1093/mind/lix.236.433'
 AND d.body->'source_evidence'->>'publication_year'='1950'
 AND EXISTS (SELECT FROM sal_ops.job_events e WHERE e.job_id=j.id AND e.event='succeeded'))
 THEN RAISE EXCEPTION 'missing real Crossref deliverable or success event'; END IF;
 IF has_function_privilege('authenticated','sal_ops.claim_crossref_evidence_job()','EXECUTE')
 THEN RAISE EXCEPTION 'dashboard can claim Crossref jobs'; END IF;
END $$;
SET ROLE authenticated;
SELECT set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',false);
DO $$ BEGIN
 IF (SELECT count(*) FROM jsonb_array_elements(public.sal_agent_deliverable_index('test-workspace')) d
 WHERE d->>'tool'='crossref_doi' AND d->>'category'='research')<>1
 THEN RAISE EXCEPTION 'Crossref deliverable absent from authenticated index'; END IF;
END $$;
RESET ROLE;
