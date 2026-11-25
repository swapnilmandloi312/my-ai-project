import unittest,tempfile
from pathlib import Path
from intelligence.context import select
from intelligence.memory import Memory
from intelligence.routing import Candidate,route
class Context(unittest.TestCase):
    def test_relevance(self):
        r=[{"id":"a","text":"general marketing advice"},{"id":"b","text":"invoice payment status paid"}]
        self.assertEqual([x["id"] for x in select("invoice status",r,4)],["b"])
    def test_budget(self): self.assertEqual(select("a",[{"text":"a b c"}],2),[])
    def test_no_match(self): self.assertEqual(select("a",[{"text":"z"}],10),[])
    def test_empty(self): self.assertEqual(select("a",[],10),[])
class MemoryTests(unittest.TestCase):
    def test_tenant_expiry(self):
        m=Memory()
        try:
            m.put("a","key","A","verified_host",20,10)
            m.put("b","key","B","user_confirmed",30,10)
            self.assertEqual(m.get("a","key",11)["value"],"A")
            self.assertEqual(m.get("b","key",11)["value"],"B")
            self.assertIsNone(m.get("a","key",20))
            self.assertIsNone(m.get("c","key",11))
        finally:m.close()
    def test_untrusted(self):
        m=Memory()
        try:
            with self.assertRaises(ValueError):m.put("a","key","bad","model_claim",30,10)
        finally:m.close()
    def test_persist_and_forget(self):
        with tempfile.TemporaryDirectory() as p:
            file=str(Path(p)/"m.db");m=Memory(file);m.put("a","key","v","verified_host",20,10);m.close()
            m=Memory(file);self.assertEqual(m.get("a","key",11)["value"],"v");m.forget("a","key");self.assertIsNone(m.get("a","key",11));m.close()
    def test_stale_update(self):
        m=Memory()
        try:
            m.put("a","key","new","verified_host",30,20);m.put("a","key","old","verified_host",30,10)
            self.assertEqual(m.get("a","key",21)["value"],"new")
        finally:m.close()
class Routing(unittest.TestCase):
    def test_cheapest_eligible(self): self.assertEqual(route([Candidate("cheap",1,.7,100),Candidate("mid",3,.91,300),Candidate("high",5,.99,500)],5).name,"mid")
    def test_abstain(self): self.assertIsNone(route([Candidate("x",3,.9,300)],2))
    def test_latency(self): self.assertIsNone(route([Candidate("x",1,.99,3000)],2))
    def test_invalid(self):
        with self.assertRaises(ValueError):route([Candidate("x",float("nan"),.9,1)],2)
if __name__=="__main__":unittest.main()
