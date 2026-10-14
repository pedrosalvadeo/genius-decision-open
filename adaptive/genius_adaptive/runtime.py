"""LangGraph Functional API with explicit, resumable mission stages.

Only registered Python adapters may execute. Plans and runtime identities are
bound before resuming. Task caching is not an exactly-once side-effect promise.
"""
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sqlite3
import zlib

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.func import entrypoint, task
from langgraph.types import RetryPolicy

from .journal import Journal, canonical, exclusive, publish, sha

STAGES = ("measure", "represent", "evaluate", "act", "observe", "remember")


def identity():
    from genius_twin.registry import STOCKFLOW, execution_identity
    own = Path(__file__).resolve().parent
    return {"protocol": "genius-mission/1", "python": platform.python_version(),
            "zlib": zlib.ZLIB_RUNTIME_VERSION,
            "packages": {d.metadata["Name"]: d.version for d in sorted(
                importlib.metadata.distributions(), key=lambda d: d.metadata["Name"])},
            "sources": {p.name: sha(p.read_bytes()) for p in sorted(own.glob("*.py"))},
            "model_template": sha((own / "distribution_model.json").read_bytes()),
            "engine": execution_identity(STOCKFLOW)}


def run(directory, adapter, *, after_stage=None):
    """Resume once; the hook is for fault-injection tests, not a user tool."""
    directory = Path(directory)
    with exclusive(directory):
        spec = json.loads((directory / "mission.json").read_text())
        adapter.validate(directory, spec)
        journal = Journal(directory / "journal.sqlite3")
        journal.bind({"spec": spec, "runtime": identity()})
        # Receipt files are reviewable exports. The journal is authoritative.
        for stage in STAGES:
            prior = journal.get(stage)
            if prior is not None:
                publish(directory / "evidence" / (stage + ".json"), (canonical(prior) + "\n").encode())
        done = journal.get("remember")
        if done is not None:
            # Completion is historical evidence. Refuse to present a corrupted
            # or missing local delivery as a healthy reusable result today.
            history = {stage: journal.get(stage) for stage in STAGES}
            if adapter.observe(directory, spec, history, journal) != history["observe"]:
                raise ValueError("COMPLETED_DELIVERY_CHANGED")
            return {"status": "completed", "memory": done, "reused": True}
        # Disable implicit remote tracing. This operator prototype handles local
        # state only and does not create a provider client or make model calls.
        if any(os.environ.get(k, "").lower() in ("true", "1") for k in
               ("LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2")):
            raise ValueError("REMOTE_TRACING_NOT_SUPPORTED")
        connection = sqlite3.connect(directory / "checkpoints.sqlite3", check_same_thread=False)
        connection.execute("PRAGMA synchronous=FULL")
        try:
            saver = SqliteSaver(connection)

            @task(retry_policy=RetryPolicy(max_attempts=1))
            def perform(stage, history):
                value = journal.once(stage, lambda: getattr(adapter, stage)(directory, spec, history, journal))
                publish(directory / "evidence" / (stage + ".json"), (canonical(value) + "\n").encode())
                if after_stage:
                    after_stage(stage)
                return value

            @entrypoint(checkpointer=saver)
            def mission(input_spec):
                history = {}
                for stage in STAGES:
                    history[stage] = perform(stage, history).result()
                return history["remember"]

            config = {"configurable": {"thread_id": spec["id"]}, "recursion_limit": 32, "max_concurrency": 4}
            snapshot = mission.get_state(config)
            value = mission.invoke(None if snapshot.created_at else spec, config, durability="sync")
            return {"status": "completed", "memory": value, "reused": False}
        finally:
            connection.close()
