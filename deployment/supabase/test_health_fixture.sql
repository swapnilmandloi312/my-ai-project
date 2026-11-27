-- Disposable PostgreSQL only. Verify observation, idempotency and permissions.
CREATE TABLE sal_ops.run_reports(
 workspace_id uuid NOT NULL REFERENCES sal_ops.workspaces(id), source text NOT NULL,
 run_id text NOT NULL, category text, status text NOT NULL, scope text NOT NULL,
 summary jsonb NOT NULL, observed_at timestamptz NOT NULL, completed_at timestamptz,
 PRIMARY KEY(workspace_id,source,run_id),
 CONSTRAINT run_reports_source_check CHECK(source IN ('github_ci','chatgpt_automation','local_demo','independent_benchmark'))
);
