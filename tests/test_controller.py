import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from snowblind import Action, Controller
from snowblind.cli import main


CLEAR_SCAN = [(15, 340, 1500), (15, 0, 1800), (15, 20, 1600)]


class ControllerTests(unittest.TestCase):
    def test_clear_scan_recommends_forward(self):
        decision = Controller().evaluate(1.5, CLEAR_SCAN)
        self.assertEqual((decision.action, decision.reason), (Action.FORWARD, "clear"))

    def test_forward_obstacle_latches_stop(self):
        controller = Controller()
        blocked = [(15, 340, 1500), (15, 0, 750), (15, 20, 1600)]
        self.assertEqual(controller.evaluate(1.5, blocked).reason, "forward_obstacle")
        self.assertEqual(controller.evaluate(1.5, CLEAR_SCAN).reason, "latched_stop")

    def test_proximity_breach_latches_stop(self):
        controller = Controller()
        self.assertEqual(controller.evaluate(0.3, CLEAR_SCAN).reason, "proximity_breach")
        self.assertEqual(controller.evaluate(1.5, CLEAR_SCAN).action, Action.STOP)

    def test_missing_forward_sector_stops(self):
        self.assertEqual(
            Controller().evaluate(1.5, CLEAR_SCAN[:2]).reason,
            "incomplete_forward_scan",
        )

    def test_zero_distance_does_not_count_as_coverage(self):
        scan = [(15, 340, 1500), (15, 0, 0), (15, 20, 1600)]
        self.assertEqual(
            Controller().evaluate(1.5, scan).reason,
            "incomplete_forward_scan",
        )

    def test_invalid_inputs_stop(self):
        self.assertEqual(Controller().evaluate(None, CLEAR_SCAN).reason, "invalid_proximity")
        self.assertEqual(Controller().evaluate(1.5, None).reason, "invalid_scan")
        self.assertEqual(
            Controller().evaluate(1.5, [(15, 340)]).reason, "invalid_scan"
        )

    def test_cli_playback(self):
        frames = [
            {"proximity_m": 1.5, "scan": CLEAR_SCAN},
            {"proximity_m": 0.2, "scan": CLEAR_SCAN},
            {"proximity_m": 1.5, "scan": CLEAR_SCAN},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frames.json"
            path.write_text(json.dumps(frames), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["simulate", str(path)]), 0)
        decisions = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(
            [decision["reason"] for decision in decisions],
            ["clear", "proximity_breach", "latched_stop"],
        )


if __name__ == "__main__":
    unittest.main()
