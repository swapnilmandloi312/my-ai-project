-- Private fail-closed lifetime USD budget ledger. No paid adapter or public grant.
BEGIN;
CREATE TABLE sal_ops.spend_limits (
 workspace_id uuid PRIMARY KEY REFERENCES sal_ops.workspaces(id),
 enabled boolean NOT NULL DEFAULT false,
 cap_microusd bigint NOT NULL DEFAULT 0 CHECK (cap_microusd BETWEEN 0 AND 1000000000000),
 reserved_microusd bigint NOT NULL DEFAULT 0 CHECK (reserved_microusd>=0),
 settled_microusd bigint NOT NULL DEFAULT 0 CHECK (settled_microusd>=0)
);
INSERT INTO sal_ops.spend_limits(workspace_id) SELECT id FROM sal_ops.workspaces;
CREATE TABLE sal_ops.spend_reservations (
 workspace_id uuid NOT NULL REFERENCES sal_ops.spend_limits(workspace_id),
 request_key text NOT NULL CHECK(length(request_key) BETWEEN 1 AND 100),
 ceiling_microusd bigint NOT NULL CHECK(ceiling_microusd BETWEEN 1 AND 1000000000000),
 actual_microusd bigint CHECK(actual_microusd BETWEEN 0 AND 1000000000000),
 receipt_ref text CHECK(length(receipt_ref) BETWEEN 1 AND 200),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 settled_at timestamptz,
 PRIMARY KEY(workspace_id,request_key),
 CHECK((actual_microusd IS NULL AND receipt_ref IS NULL AND settled_at IS NULL)
    OR (actual_microusd IS NOT NULL AND receipt_ref IS NOT NULL AND settled_at IS NOT NULL))
);
ALTER TABLE sal_ops.spend_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE sal_ops.spend_reservations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON sal_ops.spend_limits,sal_ops.spend_reservations FROM PUBLIC,anon,authenticated,service_role,sal_job_worker,sal_hourly_worker;
CREATE FUNCTION sal_ops.reserve_spend(p_slug text,p_key text,p_ceiling bigint) RETURNS jsonb
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
DECLARE w uuid; stopped boolean; l sal_ops.spend_limits%ROWTYPE; prior sal_ops.spend_reservations%ROWTYPE;
BEGIN
 IF p_key IS NULL OR length(p_key) NOT BETWEEN 1 AND 100 OR p_ceiling IS NULL OR p_ceiling NOT BETWEEN 1 AND 1000000000000 THEN RAISE EXCEPTION 'invalid reservation'; END IF;
 SELECT id INTO STRICT w FROM sal_ops.workspaces WHERE slug=p_slug;
 SELECT j.stopped INTO STRICT stopped FROM sal_ops.job_limits j WHERE workspace_id=w FOR UPDATE;
 SELECT * INTO STRICT l FROM sal_ops.spend_limits WHERE workspace_id=w FOR UPDATE;
 SELECT * INTO prior FROM sal_ops.spend_reservations WHERE workspace_id=w AND request_key=p_key;
 IF FOUND THEN
  IF prior.ceiling_microusd<>p_ceiling THEN RAISE EXCEPTION 'reservation conflict'; END IF;
  RETURN jsonb_build_object('dispatch_allowed',false,'reason','duplicate','settled',prior.settled_at IS NOT NULL);
 END IF;
 IF stopped OR NOT l.enabled OR l.cap_microusd=0 OR l.cap_microusd::numeric-l.reserved_microusd-l.settled_microusd<p_ceiling THEN
  RETURN jsonb_build_object('dispatch_allowed',false,'reason','gate_closed_or_insufficient');
 END IF;
 INSERT INTO sal_ops.spend_reservations(workspace_id,request_key,ceiling_microusd) VALUES(w,p_key,p_ceiling);
 UPDATE sal_ops.spend_limits SET reserved_microusd=reserved_microusd+p_ceiling WHERE workspace_id=w;
 RETURN jsonb_build_object('dispatch_allowed',true,'ceiling_microusd',p_ceiling);
END $$;
CREATE FUNCTION sal_ops.settle_spend(p_slug text,p_key text,p_actual bigint,p_receipt text) RETURNS jsonb
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
DECLARE w uuid; l sal_ops.spend_limits%ROWTYPE; prior sal_ops.spend_reservations%ROWTYPE; overrun boolean;
BEGIN
 IF p_actual IS NULL OR p_actual NOT BETWEEN 0 AND 1000000000000 OR p_receipt IS NULL OR length(p_receipt) NOT BETWEEN 1 AND 200 THEN RAISE EXCEPTION 'invalid settlement'; END IF;
 SELECT id INTO STRICT w FROM sal_ops.workspaces WHERE slug=p_slug;
 SELECT * INTO STRICT l FROM sal_ops.spend_limits WHERE workspace_id=w FOR UPDATE;
 SELECT * INTO STRICT prior FROM sal_ops.spend_reservations WHERE workspace_id=w AND request_key=p_key FOR UPDATE;
 IF prior.settled_at IS NOT NULL THEN
  IF prior.actual_microusd<>p_actual OR prior.receipt_ref<>p_receipt THEN RAISE EXCEPTION 'settlement conflict'; END IF;
  RETURN jsonb_build_object('settled',false,'reason','duplicate');
 END IF;
 overrun:=p_actual>prior.ceiling_microusd OR l.settled_microusd::numeric+p_actual+l.reserved_microusd-prior.ceiling_microusd>l.cap_microusd;
 UPDATE sal_ops.spend_reservations SET actual_microusd=p_actual,receipt_ref=p_receipt,settled_at=clock_timestamp() WHERE workspace_id=w AND request_key=p_key;
 UPDATE sal_ops.spend_limits SET reserved_microusd=reserved_microusd-prior.ceiling_microusd,
 settled_microusd=settled_microusd+p_actual,enabled=enabled AND NOT overrun WHERE workspace_id=w;
 RETURN jsonb_build_object('settled',true,'overrun',overrun);
END $$;
REVOKE ALL ON FUNCTION sal_ops.reserve_spend(text,text,bigint),sal_ops.settle_spend(text,text,bigint,text) FROM PUBLIC,anon,authenticated,service_role,sal_job_worker,sal_hourly_worker;
COMMIT;
