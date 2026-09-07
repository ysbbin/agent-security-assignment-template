from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    base_dir: Path
    provider: str = "gemini"
    model: str = "gemini-2.5-flash-lite"
    temperature: float = 0.0
    max_steps: int = 6
    trace_enabled: bool = True

    @property
    def seed_dir(self) -> Path:
        return self.base_dir / "environment" / "seed"

    @property
    def runtime_dir(self) -> Path:
        return self.base_dir / "environment" / "runtime"

    @property
    def trace_dir(self) -> Path:
        return self.base_dir / "traces"

    @property
    def plugin_dir(self) -> Path:
        return self.base_dir / "plugins" / "manifests"

    @classmethod
    def from_env(cls, base_dir: Path | None = None) -> "Config":
        root = (base_dir or Path(__file__).resolve().parents[1]).resolve()
        max_steps = int(os.getenv("MAX_STEPS", "6"))
        if max_steps < 1 or max_steps > 8:
            raise ValueError("MAX_STEPS must be between 1 and 8")
        model = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite")
        if model != "gemini-2.5-flash-lite":
            raise ValueError("LLM_MODEL is fixed to gemini-2.5-flash-lite")
        return cls(
            base_dir=root,
            provider=os.getenv("LLM_PROVIDER", "gemini"),
            model=model,
            temperature=float(os.getenv("TEMPERATURE", "0")),
            max_steps=max_steps,
            trace_enabled=os.getenv("TRACE_ENABLED", "true").lower() == "true",
        )
