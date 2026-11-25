import unittest
from ecosystem.discover import load,search
class Catalog(unittest.TestCase):
    def setUp(self):self.c=load()
    def test_brand(self):self.assertEqual(self.c["brand"],"Swapnil AI Labs")
    def test_unique(self):
        for group,key in [("industries","id"),("research_tracks","id"),("products","id"),("languages","code")]:
            ids=[r[key] for r in self.c[group]];self.assertEqual(len(ids),len(set(ids)))
    def test_coverage(self):
        self.assertEqual(len(self.c["industries"]),24);self.assertEqual(len(self.c["products"]),72);self.assertEqual(len(self.c["research_tracks"]),12);self.assertEqual(len(self.c["languages"]),22)
        self.assertEqual({r["id"] for r in self.c["industries"]},{p["industry"] for p in self.c["products"]})
    def test_references(self):
        tracks={r["id"] for r in self.c["research_tracks"]}
        for p in self.c["products"]:self.assertTrue(set(p["research_tracks"])<=tracks)
    def test_safety(self):
        for p in self.c["products"]:
            self.assertEqual(p["stage"],"planned")
            self.assertTrue(p["data_requirements"])
            self.assertEqual(p["execution"],"advisory_or_read_only")
            if p["risk"]=="high":self.assertEqual(p["human_review"],"required")
    def test_filter(self):
        self.assertEqual(len(search(self.c,industry="agriculture")),3)
        self.assertTrue(all("farmers" in p["audience"] for p in search(self.c,audience="farmers")))
        self.assertTrue(all(p["risk"]=="high" for p in search(self.c,risk="high")))
        self.assertEqual(search(self.c,industry="unknown"),[])
    def test_language_claims(self):
        self.assertEqual({r["code"] for r in self.c["languages"] if r["status"]=="initial_copy"},{"en","hi","hi-Latn"})
        for r in self.c["languages"]:self.assertIn("No model language capability verified",r["qualification"])
