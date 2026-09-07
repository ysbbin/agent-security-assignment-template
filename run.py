from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from agent.config import Config
from agent.core import OfficeAgent
from agent.llm.gemini_client import GeminiClient
from agent.llm.scripted_client import ScriptedLLM
from reset import reset_state


ROOT = Path(__file__).resolve().parent


def load_tasks() -> list[dict]:
    return json.loads((ROOT / "tasks" / "public_tasks.json").read_text(encoding="utf-8"))


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Run the mock Office agent")
    parser.add_argument("--task-id")
    parser.add_argument("--prompt")
    parser.add_argument("--user", default="alice")
    parser.add_argument("--provider", choices=["gemini", "scripted"])
    parser.add_argument("--script", type=Path)
    parser.add_argument("--email-context", action="append", default=[])
    parser.add_argument("--file-context", action="append", default=[])
    args = parser.parse_args()

    task = None
    if args.task_id:
        task = next((item for item in load_tasks() if item["task_id"] == args.task_id), None)
        if task is None:
            raise SystemExit(f"Unknown task id: {args.task_id}")
    if task is None and not args.prompt:
        raise SystemExit("Provide --task-id or --prompt")

    config = Config.from_env(ROOT)
    provider = args.provider or config.provider
    if not (config.runtime_dir / "users.json").exists():
        reset_state(ROOT, "all")

    if provider == "scripted":
        if args.script:
            llm = ScriptedLLM.from_file(args.script)
        elif task:
            llm = ScriptedLLM(task["script"])
        else:
            raise SystemExit("Ad-hoc scripted runs require --script")
    else:
        llm = GeminiClient(config.model, config.temperature)

    context_sources = {
        "emails": args.email_context,
        "files": args.file_context,
    }
    result = OfficeAgent(config, llm).run(
        user_task=task["prompt"] if task else args.prompt,
        user_id=task["user_id"] if task else args.user,
        task_id=task["task_id"] if task else "ad-hoc",
        task_kind=task.get("kind") if task else None,
        context_sources=context_sources,
    )
    print(result.final_text)
    print(f"run_id={result.run_id}")
    print(f"trace={result.trace_path}")


if __name__ == "__main__":
    main()
