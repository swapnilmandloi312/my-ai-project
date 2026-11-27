import unittest
from swapnil_ai_labs.goal_agents import GOALS
from swapnil_ai_labs.forty_profiles import PROFILES, evaluate

class ProfileAcceptance(unittest.TestCase):
    def test_catalog(self):
        self.assertEqual(len(PROFILES), 40)
        self.assertTrue(set(GOALS) <= set(PROFILES))

    def test_reject_unknown(self):
        with self.assertRaises(KeyError): evaluate("unknown", {})
        with self.assertRaises(ValueError): evaluate("ceo", {"bogus": "synthetic:x"})
        with self.assertRaises(ValueError): evaluate("ceo", {"roadmap": "real"})

def case(category):
    def test(self):
        spec = PROFILES[category]
        partial = evaluate(category, {})
        self.assertEqual(partial["missing"], sorted(spec.checks))
        self.assertEqual(partial["status"], "needs_evidence")
        result = evaluate(category, {k: "synthetic:"+k for k in spec.checks})
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["status"], "ready_for_independent_review")
        self.assertFalse(result["verified_completion"])
        self.assertFalse(result["external_action"])
    return test

for name in PROFILES:
    setattr(ProfileAcceptance, "test_agent_"+name, case(name))

if __name__ == "__main__":
    unittest.main(verbosity=2)
