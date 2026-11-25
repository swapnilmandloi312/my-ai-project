import json,unittest
from swapnil_ai_labs.decision_provider import decision_provider
class Tests(unittest.TestCase):
    def test_exact(self):
        e={"action":"read_record","record_id":"a"}
        self.assertEqual(json.loads(decision_provider(lambda _: "READ")(e,"read")),e)
        for s in ["REFUSE","READ other","read","READ\nREFUSE","{}","READ"*30,None]:
            self.assertEqual(decision_provider(lambda _:s)(e,"read"),"{}")
