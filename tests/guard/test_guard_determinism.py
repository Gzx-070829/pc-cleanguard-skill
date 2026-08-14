import unittest

from pc_cleanguard.guard import Guard

from tests.guard.helpers import context, request


class GuardDeterminismTests(unittest.TestCase):
    def test_identical_inputs_produce_identical_decisions_one_hundred_times(self):
        guard = Guard()
        expected = guard.evaluate(request(), context()).to_dict()
        for _ in range(100):
            self.assertEqual(expected, guard.evaluate(request(), context()).to_dict())


if __name__ == "__main__":
    unittest.main()

