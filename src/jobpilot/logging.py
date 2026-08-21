from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root = logging.getLogger("jobpilot")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def agent_log(*, agent: str, job_id: str | None, action: str, result: str, duration_ms: int, error: str | None = None) -> None:
    configure_logging()
    logging.getLogger("jobpilot").info(
        json.dumps(
            {
                "agent": agent,
                "job_id": job_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "action": action,
                "result": result,
                "duration": duration_ms,
                "error": error,
            }
        )
    )
