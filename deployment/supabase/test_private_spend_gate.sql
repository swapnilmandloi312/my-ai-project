-- Disposable PostgreSQL acceptance, after scoped worker acceptance.
DO $$
DECLARE w uuid:='11111111-1111-1111-1111-111111111111'; s constant text:='test-workspace'; a jsonb;
BEGIN
 IF (sal_ops.reserve_spend(s,'default-denied',1)->>'dispatch_allowed')::boolean THEN RAISE EXCEPTION 'default enabled'; END IF;
 UPDATE sal_ops.spend_limits SET enabled=true,cap_microusd=100 WHERE workspace_id=w;
 UPDATE sal_ops.job_limits SET stopped=true WHERE workspace_id=w;
 IF (sal_ops.reserve_spend(s,'stop-denied',1)->>'dispatch_allowed')::boolean THEN RAISE EXCEPTION 'stop bypass'; END IF;
 UPDATE sal_ops.job_limits SET stopped=false WHERE workspace_id=w;
 a:=sal_ops.reserve_spend(s,'a',60);
 IF NOT (a->>'dispatch_allowed')::boolean THEN RAISE EXCEPTION 'reservation rejected'; END IF;
 IF (sal_ops.reserve_spend(s,'a',60)->>'dispatch_allowed')::boolean THEN RAISE EXCEPTION 'duplicate dispatch'; END IF;
 IF (sal_ops.reserve_spend(s,'b',41)->>'dispatch_allowed')::boolean THEN RAISE EXCEPTION 'cap bypass'; END IF;
 IF NOT (sal_ops.reserve_spend(s,'b',40)->>'dispatch_allowed')::boolean THEN RAISE EXCEPTION 'remaining cap'; END IF;
 a:=sal_ops.settle_spend(s,'a',50,'synthetic:receipt-a');
 IF NOT (a->>'settled')::boolean OR (a->>'overrun')::boolean THEN RAISE EXCEPTION 'settlement wrong'; END IF;
 IF (sal_ops.settle_spend(s,'a',50,'synthetic:receipt-a')->>'settled')::boolean THEN RAISE EXCEPTION 'duplicate settlement'; END IF;
 a:=sal_ops.settle_spend(s,'b',60,'synthetic:receipt-b');
 IF NOT (a->>'overrun')::boolean THEN RAISE EXCEPTION 'overrun not recorded'; END IF;
 IF NOT EXISTS(SELECT 1 FROM sal_ops.spend_limits WHERE workspace_id=w AND settled_microusd=110 AND reserved_microusd=0 AND NOT enabled) THEN RAISE EXCEPTION 'overrun accounting'; END IF;
 IF (sal_ops.reserve_spend(s,'c',1)->>'dispatch_allowed')::boolean THEN RAISE EXCEPTION 'overrun bypass'; END IF;
 IF EXISTS(SELECT 1 FROM sal_ops.spend_limits WHERE workspace_id='22222222-2222-2222-2222-222222222222' AND (enabled OR cap_microusd<>0 OR settled_microusd<>0 OR reserved_microusd<>0)) THEN RAISE EXCEPTION 'cross workspace mutation'; END IF;
 IF has_function_privilege('authenticated','sal_ops.reserve_spend(text,text,bigint)','EXECUTE') OR has_function_privilege('sal_hourly_worker','sal_ops.reserve_spend(text,text,bigint)','EXECUTE') OR has_function_privilege('anon','sal_ops.settle_spend(text,text,bigint,text)','EXECUTE') OR has_table_privilege('sal_hourly_worker','sal_ops.spend_limits','UPDATE') THEN RAISE EXCEPTION 'spend grant exposed'; END IF;
END $$;
SELECT 'private monetary reservation acceptance passed';
