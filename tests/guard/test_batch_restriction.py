import unittest

from pc_cleanguard.guard import ActionBundle, Guard, evaluate_bundle

from tests.guard.helpers import context, request


class BatchRestrictionTests(unittest.TestCase):
    def test_one_hidden_block_makes_the_whole_bundle_blocked(self):
        reads = tuple(
            request(
                "read_metadata",
                request_id=f"request-read-{index}",
                path=rf"C:\Temp\read-{index}.tmp",
                requested_effect="read metadata",
            )
            for index in range(10)
        )
        blocked = request(
            "wildcard_delete",
            request_id="request-blocked",
            path=r"C:\Windows\*",
            requested_effect="delete wildcard",
        )
        bundle = ActionBundle(
            bundle_id="bundle-1",
            actions=(*reads, blocked),
            dependency_order=tuple(item.request_id for item in (*reads, blocked)),
        )
        result = evaluate_bundle(bundle, context(), guard=Guard())
        self.assertEqual("BLOCK", result.disposition.value)
        self.assertTrue(result.blocked_action_ids)
        self.assertFalse(result.execution_authorized)
        self.assertEqual(
            tuple(reversed(bundle.dependency_order)), result.rollback_order
        )


if __name__ == "__main__":
    unittest.main()
