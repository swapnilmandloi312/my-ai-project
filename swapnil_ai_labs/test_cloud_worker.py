"""Disposable PostgreSQL integration; do not run against a real workspace."""
import json
import os
import unittest
from unittest.mock import patch
from swapnil_ai_labs.forty_profiles import PROFILES
from swapnil_ai_labs.cloud_worker import sql,Queue,tick

WS="test-workspace"
FOUNDER="aaaaaaaa-0000-0000-0000-000000000001"
VIEWER="bbbbbbbb-0000-0000-0000-000000000002"
WID="11111111-1111-1111-1111-111111111111"

def command(action,args=None,who=FOUNDER,ws=WS):
    return json.loads(sql("SET ROLE authenticated; SELECT set_config('request.jwt.claim.sub',:'who',false) \\gset\nSELECT public.sal_job_command(:'ws',:'action',:'args'::jsonb);",
                          who=who,ws=ws,action=action,args=json.dumps(args or {})))

def configure(stopped,limit):
    return command("configure",{"stopped":stopped,"attempt_limit":limit})

def submit(cat,key,parent=None):
    return command("submit",{"category":cat,"request_key":key,"evidence":{},"parent_id":parent})

def approve(job): return command("approve",{"id":job["id"]})
def claim():
    with patch.dict(os.environ,{"PGOPTIONS":"-c role=sal_job_worker"}):
        return Queue(WS).claim()

@unittest.skipUnless(os.environ.get('PGDATABASE')=='sal_test' and os.environ.get('PGHOST')=='127.0.0.1', 'disposable PostgreSQL fixture required')
class CloudAcceptance(unittest.TestCase):
    def test_lifecycle(self):
        self.assertEqual(os.environ.get("PGDATABASE"),"sal_test")
        self.assertEqual(os.environ.get("PGHOST"),"127.0.0.1")
        for category,spec in PROFILES.items():
            sql("INSERT INTO sal_ops.agent_profiles VALUES(:'cat',ARRAY(SELECT jsonb_array_elements_text(:'refs'::jsonb))); INSERT INTO sal_ops.agent_controls(workspace_id,category) VALUES(:'wid'::uuid,:'cat');",
                cat=category,refs=json.dumps(spec.checks),wid=WID)
        self.assertEqual(len(command("snapshot")["profiles"]),40)
        self.assertIsNone(claim())
        with self.assertRaises(RuntimeError): command("configure",{"stopped":False,"attempt_limit":100},who=VIEWER)
        with self.assertRaises(RuntimeError): command("snapshot",ws="other-workspace")
        with self.assertRaises(RuntimeError): sql("SET ROLE anon; SELECT public.sal_job_command('test-workspace','snapshot','{}');")
        with self.assertRaises(RuntimeError): sql("SET ROLE authenticated; SELECT * FROM sal_ops.jobs;")
        with self.assertRaises(RuntimeError): sql("SET ROLE authenticated; SELECT sal_ops.claim_job('test-workspace');")
        configure(False,45)
        for category in PROFILES:
            command("agent_pause",{"category":category,"paused":False})
            job=submit(category,"acceptance-"+category)
            self.assertEqual(submit(category,"acceptance-"+category),job)
            self.assertIsNone(claim())  # approval required
            approve(job)
            with patch.dict(os.environ,{"PGOPTIONS":"-c role=sal_job_worker"}):
                self.assertTrue(tick(Queue(WS)))
        snapshot=command("snapshot")
        self.assertEqual(len(snapshot["jobs"]),40)
        self.assertTrue(all(j["state"]=="succeeded" and j["result"]["scope"]=="synthetic" for j in snapshot["jobs"]))
        self.assertEqual(snapshot["limits"]["attempts_used"],40)
        self.assertEqual(command("snapshot",who=VIEWER)["role"],"viewer")
        self.assertEqual(command("snapshot",who=VIEWER,ws="other-workspace")["jobs"],[])
        # Explicit delegation: child must reference a successful parent in the same workspace.
        child=submit("ceo","retry",snapshot["jobs"][0]["id"])
        approve(child); first=claim(); self.assertEqual(first["id"],child["id"])
        # Crash recovery: expire lease in disposable admin fixture and force backoff elapsed.
        sql("UPDATE sal_ops.jobs SET lease_until=now()-interval '1 second' WHERE id=:'id'::uuid;",id=child["id"])
        self.assertIsNone(claim())
        sql("UPDATE sal_ops.jobs SET available_at=now()-interval '1 second' WHERE id=:'id'::uuid;",id=child["id"])
        second=claim(); self.assertNotEqual(first["lease_id"],second["lease_id"])
        with patch.dict(os.environ,{"PGOPTIONS":"-c role=sal_job_worker"}):
            self.assertFalse(Queue(WS).finish(first,None))
            self.assertTrue(Queue(WS).finish(second,None))
        sql("UPDATE sal_ops.jobs SET available_at=now()-interval '1 second' WHERE id=:'id'::uuid;",id=child["id"])
        third=claim()
        with patch.dict(os.environ,{"PGOPTIONS":"-c role=sal_job_worker"}):
            self.assertTrue(Queue(WS).finish(third,None))
        self.assertEqual(next(j for j in command("snapshot")["jobs"] if j["id"]==child["id"])["state"],"failed")
        # Stop cancels active lease; budget then blocks a fresh approved job.
        stop=submit("ceo","stop"); approve(stop); active=claim(); configure(True,45)
        with patch.dict(os.environ,{"PGOPTIONS":"-c role=sal_job_worker"}):
            self.assertFalse(Queue(WS).finish(active,None))
        self.assertIsNone(claim())
        configure(False,44)
        budget=submit("ceo","budget");approve(budget);self.assertIsNone(claim())
        self.assertEqual(command("snapshot")["limits"]["attempts_used"],44)
        self.assertTrue(command("snapshot")["events"])
        configure(True,0)

if __name__=="__main__": unittest.main(verbosity=2)
