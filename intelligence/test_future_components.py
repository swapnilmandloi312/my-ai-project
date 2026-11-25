import unittest
from intelligence.semantic_cache import SemanticCache
from intelligence.knowledge_graph import KnowledgeGraph
from intelligence.compression import compress
from intelligence.protocol import AgentMailbox
from intelligence.improvement import assess
class Future(unittest.TestCase):
    def test_cache_exact(self):
        c=SemanticCache();c.put("a","m","p","d","invoice amount","100",20,10);self.assertEqual(c.get("a","m","p","d","invoice amount",11),"100")
    def test_cache_scopes(self):
        c=SemanticCache();c.put("a","m","p","d","invoice amount","100",20,10)
        for scope in [("b","m","p","d"),("a","n","p","d"),("a","m","q","d"),("a","m","p","e")]:self.assertIsNone(c.get(*scope,"invoice amount",11))
        self.assertIsNone(c.get("a","m","p","d","invoice amount",20))
    def test_cache_near_not_reused(self):
        c=SemanticCache();c.put("a","m","p","d","invoice amount one","100",20,10)
        self.assertIsNone(c.get("a","m","p","d","invoice amount two",11));self.assertTrue(c.suggest("a","m","p","d","invoice amount two",.5,11)[0]["requires_review"])
    def test_graph(self):
        g=KnowledgeGraph();g.add("a","invoice","belongs","customer","e1");g.add("a","customer","located","city","e2");g.add("b","invoice","belongs","private","e3")
        self.assertEqual(len(g.traverse("a","invoice")),2);self.assertEqual(len(g.traverse("a","invoice",1)),1);self.assertEqual(g.traverse("c","invoice"),[])
    def test_graph_cycle(self):
        g=KnowledgeGraph();g.add("a","x","to","y","e1");g.add("a","y","to","x","e2");self.assertEqual(len(g.traverse("a","x",5)),2)
    def test_compression(self):
        r=compress("invoice amount",[{"id":"a","text":"General background. Invoice amount is 100."}],4);self.assertEqual(r["output_words"],4);self.assertEqual(r["segments"][0]["source_id"],"a")
    def test_compression_zero(self):self.assertEqual(compress("invoice",[{"id":"a","text":"invoice amount"}],0)["segments"],[])
    def test_protocol(self):
        m=AgentMailbox();v={"version":"1.0","id":"1","recipient":"worker","kind":"task","payload":{"synthetic":True},"expires":20}
        try:
            m.send("a","host",{"worker"},v,10);self.assertEqual(len(m.inbox("a","worker",11)),1);self.assertEqual(m.inbox("b","worker",11),[]);self.assertEqual(m.inbox("a","worker",20),[])
            with self.assertRaises(ValueError):m.send("a","host",{"worker"},v,10)
            with self.assertRaises(ValueError):m.send("a","host",set(),{**v,"id":"2"},10)
        finally:m.close()
    def test_improvement(self):
        b={"authorized":20,"unauthorized":20,"completed":10,"unsafe_executions":1};r=assess(b,{**b,"completed":15,"unsafe_executions":0});self.assertTrue(r["eligible"]);self.assertTrue(r["human_review"])
        self.assertFalse(assess(b,{**b,"completed":20,"unsafe_executions":1})["eligible"])
    def test_improvement_low_sample(self):
        b={"authorized":2,"unauthorized":2,"completed":1,"unsafe_executions":0};self.assertFalse(assess(b,{**b,"completed":2})["eligible"])
