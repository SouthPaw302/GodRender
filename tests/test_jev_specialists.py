"""Jev orchestrator's guard and escalation behavior."""
import sys, unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"studio"))
import harness_tools
class SpecialistTests(unittest.TestCase):
    def _base(self):
        return [mock.patch.object(harness_tools.base,"find_project",return_value={"id":"p","name":"Song"}),
                mock.patch.object(harness_tools.production_project,"status",return_value={"initialized":True,"branch":"song/p"}),
                mock.patch.object(harness_tools.CORE,"status",return_value={"bootstrapped":True})]
    def test_fail_never_runs_specialist(self):
        p=self._base()
        with p[0],p[1],p[2],mock.patch("tool_api.jev_decide",return_value={"decision":"FAIL"}) as jev,\
             mock.patch.object(harness_tools,"fx_resolve") as specialist:
            r=harness_tools.route("p",{"specialist":"fx","evidence":{"gate":"DENY"}})
        self.assertEqual(r["final_decision"],"FAIL")
        specialist.assert_not_called()
        self.assertFalse(r["production_mutation"])
    def test_escalation_dispatches_real_evidence_without_approval(self):
        p=self._base()
        with p[0],p[1],p[2],mock.patch("tool_api.jev_decide",return_value={"decision":"ESCALATE"}),\
             mock.patch.object(harness_tools,"fx_resolve",return_value={"FX2-ATM-001":"approved"}) as specialist:
            r=harness_tools.route("p",{"specialist":"fx","evidence":{"gate":"PASS","ambiguous":True}})
        self.assertTrue(specialist.called)
        self.assertEqual(r["final_decision"],"ESCALATE")
        self.assertTrue(r["requires_authorized_review"])
        self.assertEqual(len(r["receipt_sha256"]),64)
    def test_no_unverified_execution_without_project_boot(self):
        with mock.patch.object(harness_tools.base,"find_project",return_value={"id":"p"}),\
             mock.patch.object(harness_tools.production_project,"status",return_value={"initialized":False}),\
             mock.patch.object(harness_tools.CORE,"status",return_value={"bootstrapped":False}):
            with self.assertRaises(RuntimeError):harness_tools.route("p",{"specialist":"model","evidence":{"gate":"PASS"}})
if __name__=="__main__":unittest.main()
