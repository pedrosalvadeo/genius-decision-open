"""A real, bounded technical mission over an explicitly pinned Git snapshot.

The declared objective is fewer archive bytes with identical file contents and
executable bits. CPU is observed, not optimized. No network delivery, external
adoption, human wellbeing or probability of sustained life is inferred.
"""
from datetime import datetime, timezone
import gzip
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import time
import zipfile

from .journal import Conflict, canonical, publish, sha

MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_FILES = 4096
MAX_STATE_BYTES = 256 * 1024 * 1024
FORMATS = {"tar": "source.tar", "gzip": "source.tar.gz", "zip": "source.zip"}


def safe_name(name):
    path = PurePosixPath(name)
    if not name or path.is_absolute() or any(p in (".", "..", ".git") for p in path.parts) or "\\" in name:
        raise ValueError("UNSAFE_SOURCE_PATH")
    if path.as_posix() != name:
        raise ValueError("NONCANONICAL_SOURCE_PATH")
    return name


def git(source, *args):
    return subprocess.check_output(["git", "-C", str(source), *args], timeout=15,
                                   stderr=subprocess.PIPE)


def prepare(source, commit, directory):
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("FULL_SOURCE_COMMIT_REQUIRED")
    if git(source, "rev-parse", commit + "^{commit}").decode().strip() != commit:
        raise ValueError("SOURCE_COMMIT_MISMATCH")
    rows = git(source, "ls-tree", "-rz", "--full-tree", commit).split(b"\0")
    inventory, blobs, total = {}, {}, 0
    for row in filter(None, rows):
        meta, raw_name = row.split(b"\t", 1)
        mode, kind, oid = meta.decode().split()
        name = safe_name(raw_name.decode("utf-8"))
        if kind != "blob" or mode not in ("100644", "100755"):
            raise ValueError("ONLY_REGULAR_GIT_FILES_SUPPORTED")
        size = int(git(source, "cat-file", "-s", oid))
        total += size
        if total > MAX_INPUT_BYTES or len(inventory) >= MAX_FILES:
            raise ValueError("SOURCE_BUDGET_EXCEEDED")
        raw = git(source, "cat-file", "blob", oid)
        if len(raw) != size:
            raise ValueError("SOURCE_SIZE_CHANGED")
        blobs[name] = raw
        inventory[name] = {"sha256": sha(raw), "bytes": size, "mode": int(mode[-3:], 8)}
    if not inventory:
        raise ValueError("EMPTY_SOURCE")
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name, raw in blobs.items():
        publish(directory / "input" / name, raw)
    digest = sha(canonical(inventory).encode())
    spec = {"id": "distribution_" + commit, "kind": "source_distribution_v1",
            "source_commit": commit, "inventory": inventory, "input_sha256": digest,
            "objective": "MIN_ARCHIVE_BYTES_WITH_EXACT_ROUND_TRIP",
            "scope": "LOCAL_TECHNICAL_EXPERIMENT", "formats": list(FORMATS),
            "created_at": datetime.now(timezone.utc).isoformat()}
    publish(directory / "mission.json", (canonical(spec) + "\n").encode())
    return {"id": spec["id"], "files": len(inventory), "input_bytes": total, "input_sha256": digest}


def prepare_files(files, directory, mission_id):
    """Immutable UTF-8 snapshot supplied by an authenticated service principal."""
    directory = Path(directory)
    inventory, total = {}, 0
    for name, content in files.items():
        safe_name(name)
        raw = content.encode('utf-8')
        total += len(raw)
        inventory[name] = {"sha256": sha(raw), "bytes": len(raw), "mode": 0o644}
    if not inventory or len(inventory) > 16 or total > 65536:
        raise ValueError("SOURCE_BUDGET_EXCEEDED")
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name, content in files.items():
        publish(directory / 'input' / name, content.encode('utf-8'))
    digest = sha(canonical(inventory).encode())
    spec = {"id": mission_id, "kind": "source_distribution_v1", "source_commit": None,
            "source_kind": "SUBMITTED_UTF8_SNAPSHOT", "inventory": inventory,
            "input_sha256": digest, "objective": "MIN_ARCHIVE_BYTES_WITH_EXACT_ROUND_TRIP",
            "scope": "LOCAL_TECHNICAL_EXPERIMENT", "formats": list(FORMATS),
            "created_at": datetime.now(timezone.utc).isoformat()}
    publish(directory / 'mission.json', (canonical(spec) + '\n').encode())
    return spec


def encode(kind, files, inventory):
    output = io.BytesIO()
    if kind in ("tar", "gzip"):
        with tarfile.open(fileobj=output, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for name, raw in sorted(files.items()):
                info = tarfile.TarInfo(name)
                info.size, info.mode, info.mtime = len(raw), inventory[name]["mode"], 0
                archive.addfile(info, io.BytesIO(raw))
        raw = output.getvalue()
        return gzip.compress(raw, compresslevel=9, mtime=0) if kind == "gzip" else raw
    if kind != "zip":
        raise ValueError("UNSUPPORTED_FORMAT")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o100000 | inventory[name]["mode"]) << 16
            archive.writestr(info, raw, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output.getvalue()


def inventory_of(kind, raw):
    result, total = {}, 0

    def add(name, size, mode, read):
        nonlocal total
        safe_name(name)
        if name in result or len(result) >= MAX_FILES or size < 0:
            raise ValueError("INVALID_ARCHIVE_ENTRY")
        total += size
        if total > MAX_INPUT_BYTES:
            raise ValueError("ARCHIVE_BUDGET_EXCEEDED")
        body = read(size + 1)
        if len(body) != size:
            raise ValueError("ARCHIVE_SIZE_MISMATCH")
        result[name] = {"sha256": sha(body), "bytes": size, "mode": mode & 0o777}

    if kind == "zip":
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for member in archive.infolist():
                if member.is_dir() or member.external_attr >> 28 != 0o10:
                    raise ValueError("ARCHIVE_NOT_REGULAR_FILE")
                with archive.open(member) as handle:
                    add(member.filename, member.file_size, member.external_attr >> 16, handle.read)
    elif kind in ("tar", "gzip"):
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:*") as archive:
            for member in archive:
                if not member.isfile():
                    raise ValueError("ARCHIVE_NOT_REGULAR_FILE")
                with archive.extractfile(member) as handle:
                    add(member.name, member.size, member.mode, handle.read)
    else:
        raise ValueError("UNSUPPORTED_FORMAT")
    return result


class Distribution:
    def validate(self, directory, spec):
        if (spec["kind"] != "source_distribution_v1" or spec["formats"] != list(FORMATS)
                or spec["objective"] != "MIN_ARCHIVE_BYTES_WITH_EXACT_ROUND_TRIP"):
            raise ValueError("UNSUPPORTED_MISSION")
        if sha(canonical(spec["inventory"]).encode()) != spec["input_sha256"]:
            raise Conflict("INVENTORY_CHANGED")
        paths = list(directory.rglob("*"))
        if any(p.is_symlink() for p in paths):
            raise Conflict("STATE_SYMLINK_NOT_SUPPORTED")
        if sum(p.stat().st_size for p in paths if p.is_file()) > MAX_STATE_BYTES:
            raise ValueError("STATE_BUDGET_EXCEEDED")
        actual = {p.relative_to(directory / "input").as_posix(): p
                  for p in (directory / "input").rglob("*") if p.is_file()}
        if set(actual) != set(spec["inventory"]):
            raise Conflict("SOURCE_INVENTORY_CHANGED")
        for name, row in spec["inventory"].items():
            safe_name(name)
            path = actual[name]
            if path.stat().st_size != row["bytes"] or sha(path.read_bytes()) != row["sha256"]:
                raise Conflict("SOURCE_BYTES_CHANGED")

    def measure(self, directory, spec, history, journal):
        files = {name: (directory / "input" / name).read_bytes() for name in spec["inventory"]}
        artifacts = {}
        for kind, filename in FORMATS.items():
            started = time.process_time_ns()
            raw = encode(kind, files, spec["inventory"])
            cpu = time.process_time_ns() - started
            if inventory_of(kind, raw) != spec["inventory"]:
                raise ValueError("CANDIDATE_INTEGRITY_FAILED")
            publish(directory / "candidates" / filename, raw)
            artifacts[kind] = {"bytes": len(raw), "sha256": sha(raw), "create_cpu_ns": cpu,
                               "round_trip_verified": True}
        return {"input_sha256": spec["input_sha256"], "source_commit": spec["source_commit"],
                "files": len(files), "artifacts": artifacts,
                "cpu_method": "Single local observation; no CPU superiority inferred"}

    def represent(self, directory, spec, history, journal):
        model = json.loads(Path(__file__).with_name("distribution_model.json").read_text())
        artifacts = history["measure"]["artifacts"]
        budget = max(a["bytes"] for a in artifacts.values())
        model["name"] = "Distribución local del snapshot " + (spec["source_commit"] or spec["input_sha256"])[:12]
        model["stocks"][0].update(initial=f"{budget}/1", capacity=f"{budget}/1")
        model["stocks"][0]["label"] = "Margen frente al mayor archivo medido"
        for action in model["actions"]:
            kind = action["id"].removeprefix("send_")
            action["withdrawals"]["remaining"] = str(artifacts[kind]["bytes"]) + "/1"
        return model

    def evaluate(self, directory, spec, history, journal):
        from genius_twin.registry import evaluate
        result = evaluate(history["represent"])
        if result["verification"]["valid"] is not True:
            raise ValueError("NATIVE_RESULT_NOT_VERIFIED")
        # Independent arithmetic oracle for this declared one-dimensional case.
        rows = history["measure"]["artifacts"]
        best_size = min(row["bytes"] for row in rows.values())
        best = [key for key, row in rows.items() if row["bytes"] == best_size]
        selected = result["canonical_results"]["decision"]["selected"]
        if len(best) != 1 or selected != best[0]:
            raise ValueError("NO_UNIQUE_VERIFIED_CHOICE")
        return result

    def act(self, directory, spec, history, journal):
        selected = history["evaluate"]["canonical_results"]["decision"]["selected"]
        artifact = history["measure"]["artifacts"][selected]
        destination = directory / "delivery" / FORMATS[selected]
        request = {"kind": "LOCAL_IMMUTABLE_ARCHIVE", "destination": "delivery/" + destination.name,
                   "format": selected, "sha256": artifact["sha256"], "bytes": artifact["bytes"]}

        def reconcile():
            if not destination.exists():
                return None  # Missing receipt or file is NOT proof that an arbitrary effect is safe to retry.
            raw = destination.read_bytes()
            if len(raw) != artifact["bytes"] or sha(raw) != artifact["sha256"]:
                raise Conflict("DELIVERED_ARTIFACT_CHANGED")
            return {**request, "confirmed": True}

        def apply():
            raw = (directory / "candidates" / FORMATS[selected]).read_bytes()
            if sha(raw) != artifact["sha256"] or len(raw) != artifact["bytes"]:
                raise Conflict("CANDIDATE_CHANGED")
            publish(destination, raw)
            return reconcile()

        return journal.effect("publish_archive", request, apply, reconcile)

    def observe(self, directory, spec, history, journal):
        action = history["act"]
        raw = (directory / action["destination"]).read_bytes()
        if sha(raw) != action["sha256"] or inventory_of(action["format"], raw) != spec["inventory"]:
            raise Conflict("DELIVERY_READBACK_FAILED")
        baseline = history["measure"]["artifacts"]["tar"]["bytes"]
        return {"readback_verified": True, "input_sha256": spec["input_sha256"],
                "artifact_sha256": sha(raw), "files_verified": len(spec["inventory"]),
                "archive_bytes": len(raw), "tar_bytes": baseline, "bytes_avoided_vs_tar": baseline - len(raw),
                "network_transfers": 0, "independent_users": 0,
                "human_wellbeing_effect": "UNMEASURED", "life_sustainment_effect": "UNMEASURED"}

    def remember(self, directory, spec, history, journal):
        return {"kind": "EMPIRICAL_SNAPSHOT_MEMORY", "source_commit": spec["source_commit"],
                "input_sha256": spec["input_sha256"], "selected": history["act"]["format"],
                "observation": history["observe"],
                "reuse_condition": "Exact inventory and execution context only; remeasure changed inputs",
                "learning_status": "OBSERVATION_RECORDED; NO_MODEL_OR_CODE_SELF_MODIFICATION"}
