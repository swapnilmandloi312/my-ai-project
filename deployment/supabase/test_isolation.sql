-- CI disposable fixture; the request.jwt.claim.sub setting emulates a verified JWT subject.
SET ROLE service_role;
INSERT INTO public.sal_tenants(id,label) VALUES ('11111111-0000-0000-0000-000000000001','Tenant A'),('22222222-0000-0000-0000-000000000002','Tenant B');
INSERT INTO public.sal_members VALUES ('11111111-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000001'),('22222222-0000-0000-0000-000000000002','bbbbbbbb-0000-0000-0000-000000000002');
INSERT INTO public.sal_operations_runs(tenant_id,source,run_id,state,summary,completed_at,verified_at)
VALUES ('11111111-0000-0000-0000-000000000001','coordinator','run-a','completed','synthetic A',now(),now()),
       ('22222222-0000-0000-0000-000000000002','coordinator','run-b','completed','synthetic B',now(),now());
DO $$ BEGIN
  BEGIN
    INSERT INTO public.sal_operations_runs(tenant_id,source,run_id,state,verified_at) VALUES ('11111111-0000-0000-0000-000000000001','coordinator','bad','completed',now());
    RAISE EXCEPTION 'Missing completion time accepted';
  EXCEPTION WHEN check_violation THEN NULL; END;
  BEGIN
    INSERT INTO public.sal_operations_runs(tenant_id,source,run_id,state,verified_at) VALUES ('11111111-0000-0000-0000-000000000001','coordinator','run-a','scheduled',now());
    RAISE EXCEPTION 'Duplicate run accepted';
  EXCEPTION WHEN unique_violation THEN NULL; END;
END $$;
RESET ROLE;
SET ROLE anon;
DO $$ BEGIN
  BEGIN PERFORM count(*) FROM public.sal_operations_runs; RAISE EXCEPTION 'Anonymous read accepted';
  EXCEPTION WHEN insufficient_privilege THEN NULL; END;
END $$;
RESET ROLE;
SET ROLE authenticated;
SELECT set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',false);
DO $$ BEGIN
  IF (SELECT count(*) FROM public.sal_tenants)<>1 OR (SELECT count(*) FROM public.sal_members)<>1 OR (SELECT count(*) FROM public.sal_operations_runs)<>1 THEN RAISE EXCEPTION 'Isolation failure'; END IF;
  IF EXISTS (SELECT 1 FROM public.sal_operations_runs WHERE run_id='run-b') THEN RAISE EXCEPTION 'Cross tenant read'; END IF;
  BEGIN
    INSERT INTO public.sal_members VALUES ('22222222-0000-0000-0000-000000000002','aaaaaaaa-0000-0000-0000-000000000001');
    RAISE EXCEPTION 'Membership escalation accepted';
  EXCEPTION WHEN insufficient_privilege THEN NULL; END;
  BEGIN
    UPDATE public.sal_operations_runs SET state='failed' WHERE run_id='run-a';
    RAISE EXCEPTION 'Browser write accepted';
  EXCEPTION WHEN insufficient_privilege THEN NULL; END;
  BEGIN
    DELETE FROM public.sal_operations_runs WHERE run_id='run-a';
    RAISE EXCEPTION 'Browser delete accepted';
  EXCEPTION WHEN insufficient_privilege THEN NULL; END;
END $$;
SELECT set_config('request.jwt.claim.sub','bbbbbbbb-0000-0000-0000-000000000002',false);
DO $$ BEGIN
  IF (SELECT count(*) FROM public.sal_operations_runs)<>1 OR EXISTS (SELECT 1 FROM public.sal_operations_runs WHERE run_id='run-a') THEN RAISE EXCEPTION 'Tenant B isolation failure'; END IF;
END $$;
SELECT set_config('request.jwt.claim.sub','',false);
DO $$ BEGIN
  IF EXISTS(SELECT 1 FROM public.sal_operations_runs) OR EXISTS(SELECT 1 FROM public.sal_tenants) THEN RAISE EXCEPTION 'Missing subject accepted'; END IF;
END $$;
RESET ROLE;
DELETE FROM public.sal_members WHERE user_id='aaaaaaaa-0000-0000-0000-000000000001';
SET ROLE authenticated;
SELECT set_config('request.jwt.claim.sub','aaaaaaaa-0000-0000-0000-000000000001',false);
DO $$ BEGIN
  IF EXISTS(SELECT 1 FROM public.sal_operations_runs) THEN RAISE EXCEPTION 'Revoked membership still visible'; END IF;
END $$;
RESET ROLE;
SELECT 'PASS: role restrictions, cross-tenant reads, membership escalation, revoked membership, duplicates and timestamp constraints' AS result;
