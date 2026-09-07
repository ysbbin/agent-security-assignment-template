from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def reset_state(base_dir: Path = ROOT, target: str = "all") -> None:
    seed = base_dir / "environment" / "seed"
    runtime = base_dir / "environment" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)

    if target == "all":
        for path in runtime.glob("*.json"):
            path.unlink()
        for path in seed.glob("*.json"):
            shutil.copy2(path, runtime / path.name)
        (runtime / "session.json").write_text("{}\n", encoding="utf-8")
        (runtime / "outbox.json").write_text("[]\n", encoding="utf-8")
        trace_dir = base_dir / "traces"
        if trace_dir.exists():
            for path in trace_dir.glob("*.jsonl"):
                path.unlink()
    elif target == "session":
        (runtime / "session.json").write_text("{}\n", encoding="utf-8")
    elif target == "memory":
        shutil.copy2(seed / "memory.json", runtime / "memory.json")
    else:
        raise ValueError(f"Unknown reset target: {target}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset mock Office state")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--session", action="store_true")
    group.add_argument("--memory", action="store_true")
    args = parser.parse_args()
    target = "all" if args.all else "session" if args.session else "memory"
    reset_state(target=target)
    print(f"Reset complete: {target}")


if __name__ == "__main__":
    main()
