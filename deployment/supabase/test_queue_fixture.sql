-- Disposable CI ONLY; mimics the existing private cloud tables used by queue.
CREATE SCHEMA sal_ops;
CREATE TABLE sal_ops.workspaces(id uuid PRIMARY KEY,slug text UNIQUE NOT NULL);
CREATE TABLE sal_ops.members(workspace_id uuid REFERENCES sal_ops.workspaces,user_id uuid REFERENCES auth.users,role text NOT NULL,PRIMARY KEY(workspace_id,user_id));
CREATE TABLE sal_ops.agent_profiles(category text PRIMARY KEY,required_evidence text[] NOT NULL);
CREATE TABLE sal_ops.agent_controls(workspace_id uuid REFERENCES sal_ops.workspaces,category text REFERENCES sal_ops.agent_profiles,paused boolean DEFAULT true,revision bigint DEFAULT 1,updated_at timestamptz DEFAULT now(),PRIMARY KEY(workspace_id,category));
INSERT INTO sal_ops.workspaces VALUES('11111111-1111-1111-1111-111111111111','test-workspace'),('22222222-2222-2222-2222-222222222222','other-workspace');
INSERT INTO sal_ops.members VALUES('11111111-1111-1111-1111-111111111111','aaaaaaaa-0000-0000-0000-000000000001','founder'),('11111111-1111-1111-1111-111111111111','bbbbbbbb-0000-0000-0000-000000000002','viewer'),('22222222-2222-2222-2222-222222222222','bbbbbbbb-0000-0000-0000-000000000002','founder');
