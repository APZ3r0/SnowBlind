"""Command line interface for offline scan playback."""

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .controller import Controller


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SnowBlind offline simulator")
    commands = parser.add_subparsers(dest="command", required=True)
    simulate = commands.add_parser("simulate", help="evaluate JSON scan frames")
    simulate.add_argument("frames", type=Path, help="path to a JSON frame list")
    args = parser.parse_args(argv)

    try:
        frames = json.loads(args.frames.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.error(f"cannot read frames: {exc}")
    if not isinstance(frames, list) or not frames:
        parser.error("frames must be a nonempty JSON list")

    controller = Controller()
    for index, frame in enumerate(frames, start=1):
        if not isinstance(frame, dict):
            parser.error(f"frame {index} must be an object")
        decision = controller.evaluate(frame.get("proximity_m"), frame.get("scan"))
        print(
            json.dumps(
                {"cycle": index, "action": decision.action.value, "reason": decision.reason}
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
