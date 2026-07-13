import unittest

from pc_cleanguard.persistence.graph import build_persistence_chain_graph
from pc_cleanguard.persistence.governance_plan import build_persistence_governance_plan, render_persistence_governance_plan_markdown


class PersistenceGovernancePlanTest(unittest.TestCase):
    def test_plan_has_l0_to_l5_and_blocks_execution(self):
        plan = build_persistence_governance_plan(build_persistence_chain_graph({"services": [{"display_name": "Example Service"}]}))
        self.assertEqual(["L0", "L1", "L2", "L3", "L4", "L5"], [x["level"] for x in plan["levels"]])
        self.assertTrue(plan["blocked_steps"])
        self.assertEqual(0, plan["execution_gating_eligible_count"])
        self.assertIn("不自动执行", render_persistence_governance_plan_markdown(plan))

    def test_l3_and_l4_are_proposals_only(self):
        plan = build_persistence_governance_plan(build_persistence_chain_graph({"services": [{"display_name": "Example"}], "scheduled_tasks": [{"task_name": "Example"}]}))
        for step in plan["proposed_steps"]:
            if step["level"] in {"L3", "L4"}:
                self.assertTrue(step["proposal_only"])
                self.assertFalse(step["execution_authorized"])
