from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Sequence

try:
    import z3
except ImportError as exc:  # pragma: no cover - depends on local environment
    raise SystemExit(
        "Missing dependency 'z3-solver'. Install the pinned requirements with "
        "'python -m pip install -r requirements.txt'."
    ) from exc

try:  # Supports both `python -m m1_logic...` and direct script execution.
    from .sat_solver import (
        InputValidationError,
        InvigilatorSATSolver,
        load_instance,
        write_results,
    )
except ImportError:  # pragma: no cover - used only for direct execution
    from sat_solver import (  # type: ignore[no-redef]
        InputValidationError,
        InvigilatorSATSolver,
        load_instance,
        write_results,
    )


@dataclass(frozen=True)
class RemovalCheck:
    """Solver result after removing one constraint from a candidate core."""

    removed_constraint: str
    remaining_status: str
    runtime_ms: float
    necessary: bool | None
    reason_unknown: str | None = None


@dataclass(frozen=True)
class CoreVerification:
    """Complete, JSON-serializable evidence about one candidate core."""

    core: tuple[str, ...]
    core_size: int
    full_core_status: str
    full_core_runtime_ms: float
    is_unsat: bool
    is_subset_minimal: bool
    removal_checks: tuple[RemovalCheck, ...]
    total_runtime_ms: float
    solver_name: str
    solver_version: str
    timeout_ms: int
    reason: str | None = None


def _load_json_object(path: str | Path, label: str) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise InputValidationError(f"{label} file does not exist: {resolved}")
    try:
        with resolved.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except UnicodeDecodeError as exc:
        raise InputValidationError(f"{label} must be UTF-8 JSON: {resolved}") from exc
    except json.JSONDecodeError as exc:
        raise InputValidationError(
            f"invalid JSON in {resolved} at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise InputValidationError(f"{label} root must be a JSON object")
    return value


def load_results(path: str | Path) -> dict[str, Any]:
    """Load and structurally validate an M1 results document."""

    document = _load_json_object(path, "results")
    instances = document.get("instances")
    if not isinstance(instances, list) or not instances:
        raise InputValidationError("results.instances must be a non-empty array")
    for index, entry in enumerate(instances):
        if not isinstance(entry, dict):
            raise InputValidationError(f"results.instances[{index}] must be an object")
        if not isinstance(entry.get("instance_name"), str) or not entry["instance_name"]:
            raise InputValidationError(
                f"results.instances[{index}].instance_name must be a non-empty string"
            )
    return document


def select_result_entries(
    document: Mapping[str, Any], instance_names: Sequence[str] | None
) -> list[dict[str, Any]]:
    """Select named UNSAT entries, or every UNSAT entry when names are omitted."""

    entries = document["instances"]
    if not instance_names:
        selected = [entry for entry in entries if entry.get("status") == "UNSAT"]
        if not selected:
            raise InputValidationError("results contain no UNSAT instance to verify")
        return selected

    duplicates = sorted({name for name in instance_names if instance_names.count(name) > 1})
    if duplicates:
        raise InputValidationError(f"duplicate --instance-name values: {duplicates}")
    selected: list[dict[str, Any]] = []
    for instance_name in instance_names:
        candidates = [entry for entry in entries if entry.get("instance_name") == instance_name]
        if len(candidates) != 1:
            raise InputValidationError(
                f"expected exactly one result named {instance_name!r}, found {len(candidates)}"
            )
        entry = candidates[0]
        if entry.get("status") != "UNSAT":
            raise InputValidationError(
                f"instance {instance_name!r} has status {entry.get('status')!r}, not 'UNSAT'"
            )
        selected.append(entry)
    return selected


def index_instances(
    sources: Sequence[str | Path | Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Load verification inputs and index them by their stable instance name."""

    indexed: dict[str, dict[str, Any]] = {}
    for source in sources:
        instance = load_instance(source)
        name = instance["instance_name"]
        if name in indexed:
            raise InputValidationError(f"duplicate verification input instance: {name!r}")
        indexed[name] = instance
    return indexed


def extract_core(entry: Mapping[str, Any], mode: str) -> list[str]:
    """Extract the correct candidate core for verify or minimize mode."""

    core_data = entry.get("unsat_core")
    if not isinstance(core_data, Mapping):
        raise InputValidationError("selected result has no unsat_core object")
    preferred_keys = (
        ("subset_minimal", "initial") if mode == "verify" else ("initial", "subset_minimal")
    )
    raw_core: Any = None
    selected_key: str | None = None
    for key in preferred_keys:
        candidate = core_data.get(key)
        if isinstance(candidate, list) and candidate:
            raw_core, selected_key = candidate, key
            break
    if raw_core is None:
        raise InputValidationError(
            f"unsat_core must contain a non-empty {preferred_keys[0]!r} "
            f"or {preferred_keys[1]!r} array"
        )

    core: list[str] = []
    for index, name in enumerate(raw_core):
        if not isinstance(name, str) or not name.strip():
            raise InputValidationError(
                f"unsat_core.{selected_key}[{index}] must be a non-empty string"
            )
        core.append(name.strip())
    duplicates = sorted({name for name in core if core.count(name) > 1})
    if duplicates:
        raise InputValidationError(f"UNSAT core contains duplicate names: {duplicates}")
    return core


class UnsatCoreVerifier:
    """Incrementally verify named subsets of one already-built SAT model."""

    def __init__(self, instance: Mapping[str, Any], timeout_ms: int = 30_000):
        self.engine = InvigilatorSATSolver(instance, timeout_ms=timeout_ms)
        self.timeout_ms = timeout_ms
        self.constraints = {item.name: item.expression for item in self.engine.constraints}

    def validate_names(self, names: Sequence[str]) -> tuple[str, ...]:
        """Return names after checking non-emptiness, uniqueness and existence."""

        if not names:
            raise InputValidationError("UNSAT core must not be empty")
        normalized = tuple(names)
        if len(set(normalized)) != len(normalized):
            raise InputValidationError("UNSAT core names must be unique")
        unknown = sorted(set(normalized) - set(self.constraints))
        if unknown:
            raise InputValidationError(
                f"UNSAT core references unknown constraint names: {unknown}"
            )
        return normalized

    def _check(self, names: Sequence[str]) -> tuple[str, float, str | None]:
        solver = z3.Solver()
        solver.set(timeout=self.timeout_ms)
        for name in names:
            solver.add(self.constraints[name])
        started = perf_counter()
        status = solver.check()
        runtime_ms = (perf_counter() - started) * 1000.0
        reason = solver.reason_unknown() if status == z3.unknown else None
        return str(status).upper(), runtime_ms, reason

    def verify(self, names: Sequence[str]) -> CoreVerification:
        """Prove or refute UNSAT and subset-minimality of ``names``."""

        core = self.validate_names(names)
        total_started = perf_counter()
        full_status, full_runtime_ms, full_reason = self._check(core)
        if full_status != "UNSAT":
            reason = (
                "candidate core is satisfiable"
                if full_status == "SAT"
                else f"solver returned UNKNOWN: {full_reason}"
            )
            return CoreVerification(
                core=core,
                core_size=len(core),
                full_core_status=full_status,
                full_core_runtime_ms=round(full_runtime_ms, 3),
                is_unsat=False,
                is_subset_minimal=False,
                removal_checks=(),
                total_runtime_ms=round((perf_counter() - total_started) * 1000.0, 3),
                solver_name="z3",
                solver_version=z3.get_version_string(),
                timeout_ms=self.timeout_ms,
                reason=reason,
            )

        checks: list[RemovalCheck] = []
        for index, removed in enumerate(core):
            remainder = core[:index] + core[index + 1 :]
            status, runtime_ms, reason_unknown = self._check(remainder)
            necessary: bool | None
            if status == "SAT":
                necessary = True
            elif status == "UNSAT":
                necessary = False
            else:
                necessary = None
            checks.append(
                RemovalCheck(
                    removed_constraint=removed,
                    remaining_status=status,
                    runtime_ms=round(runtime_ms, 3),
                    necessary=necessary,
                    reason_unknown=reason_unknown,
                )
            )

        is_minimal = all(check.necessary is True for check in checks)
        if is_minimal:
            reason = None
        elif any(check.necessary is None for check in checks):
            reason = "minimality is inconclusive because at least one removal check was UNKNOWN"
        else:
            redundant = [
                check.removed_constraint for check in checks if check.necessary is False
            ]
            reason = f"candidate core contains redundant constraints: {redundant}"
        return CoreVerification(
            core=core,
            core_size=len(core),
            full_core_status=full_status,
            full_core_runtime_ms=round(full_runtime_ms, 3),
            is_unsat=True,
            is_subset_minimal=is_minimal,
            removal_checks=tuple(checks),
            total_runtime_ms=round((perf_counter() - total_started) * 1000.0, 3),
            solver_name="z3",
            solver_version=z3.get_version_string(),
            timeout_ms=self.timeout_ms,
            reason=reason,
        )

    def minimize(
        self, names: Sequence[str]
    ) -> tuple[tuple[str, ...], tuple[RemovalCheck, ...]]:
        """Shrink an UNSAT core using deterministic deletion-based minimization."""

        candidate = list(self.validate_names(names))
        initial_status, _, initial_reason = self._check(candidate)
        if initial_status != "UNSAT":
            detail = f": {initial_reason}" if initial_reason else ""
            raise InputValidationError(
                f"cannot minimize a core whose status is {initial_status}{detail}"
            )

        shrinking_checks: list[RemovalCheck] = []
        index = 0
        while index < len(candidate):
            removed = candidate[index]
            remainder = candidate[:index] + candidate[index + 1 :]
            status, runtime_ms, reason_unknown = self._check(remainder)
            necessary = True if status == "SAT" else False if status == "UNSAT" else None
            shrinking_checks.append(
                RemovalCheck(
                    removed_constraint=removed,
                    remaining_status=status,
                    runtime_ms=round(runtime_ms, 3),
                    necessary=necessary,
                    reason_unknown=reason_unknown,
                )
            )
            if status == "UNSAT":
                candidate = remainder
            elif status == "SAT":
                index += 1
            else:
                raise RuntimeError(
                    f"cannot establish minimality: removing {removed!r} returned "
                    f"UNKNOWN ({reason_unknown})"
                )
        return tuple(candidate), tuple(shrinking_checks)


def verification_to_dict(report: CoreVerification) -> dict[str, Any]:
    """Convert a nested verification dataclass to ordinary JSON data."""

    return asdict(report)


def verify_unsat_core(
    instance: str | Path | Mapping[str, Any],
    core: Sequence[str],
    *,
    timeout_ms: int = 30_000,
) -> dict[str, Any]:
    """Public API for independently verifying one named candidate core."""

    verifier = UnsatCoreVerifier(load_instance(instance), timeout_ms=timeout_ms)
    return verification_to_dict(verifier.verify(core))


def minimize_unsat_core(
    instance: str | Path | Mapping[str, Any],
    core: Sequence[str],
    *,
    timeout_ms: int = 30_000,
) -> dict[str, Any]:
    """Public API for shrinking and then independently verifying one core."""

    verifier = UnsatCoreVerifier(load_instance(instance), timeout_ms=timeout_ms)
    minimal, shrinking_checks = verifier.minimize(core)
    verification = verification_to_dict(verifier.verify(minimal))
    if not verification["is_subset_minimal"]:
        raise RuntimeError("deletion-based minimization did not produce a verified minimal core")
    return {
        "initial_core": list(core),
        "initial_size": len(core),
        "subset_minimal_core": list(minimal),
        "final_size": len(minimal),
        "shrinking_checks": [asdict(check) for check in shrinking_checks],
        "verification": verification,
    }


def update_result_entry(
    entry: dict[str, Any], mode: str, report: Mapping[str, Any]
) -> None:
    """Attach verification evidence without deleting the solver's original core."""

    core_data = entry.get("unsat_core")
    if not isinstance(core_data, dict):
        raise InputValidationError("selected result has no mutable unsat_core object")
    if mode == "minimize":
        core_data["subset_minimal"] = list(report["subset_minimal_core"])
        core_data["final_size"] = report["final_size"]
        core_data["shrinking_checks"] = list(report["shrinking_checks"])
        core_data["verification"] = dict(report["verification"])
        core_data["is_unsat"] = bool(report["verification"]["is_unsat"])
        core_data["is_subset_minimal"] = bool(
            report["verification"]["is_subset_minimal"]
        )
    else:
        core_data["verification"] = dict(report)
        core_data["is_unsat"] = bool(report["is_unsat"])
        core_data["is_subset_minimal"] = bool(report["is_subset_minimal"])


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify or deletion-minimize a named UNSAT core and update m1_results.json."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        nargs="+",
        help="one or more original CNF JSON inputs used to produce the result entries",
    )
    parser.add_argument(
        "--results", required=True, type=Path, help="m1_results.json from sat_solver.py"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="output results path; default updates --results atomically",
    )
    parser.add_argument(
        "--instance-name",
        action="append",
        default=None,
        help="UNSAT result to check; repeatable; omitted means verify every UNSAT entry",
    )
    parser.add_argument(
        "--mode", choices=("verify", "minimize"), default="verify", help="operation to run"
    )
    parser.add_argument(
        "--timeout-ms", type=int, default=30_000, help="positive Z3 timeout per solver check"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point; returns 0 only for a verified minimal core."""

    args = _parser().parse_args(argv)
    try:
        if args.timeout_ms <= 0:
            raise InputValidationError("--timeout-ms must be a positive integer")
        instances = index_instances(args.input)
        document = load_results(args.results)
        entries = select_result_entries(document, args.instance_name)
        statuses: list[dict[str, Any]] = []
        for entry in entries:
            name = entry["instance_name"]
            instance = instances.get(name)
            if instance is None:
                raise InputValidationError(
                    f"no --input matches UNSAT result instance_name {name!r}"
                )
            if instance.get("format") != "cnf":
                raise InputValidationError(
                    f"verification input {name!r} is not CNF; W02-T4 cores must be "
                    "verified against the named clauses emitted by W02-T3"
                )
            core = extract_core(entry, args.mode)
            if args.mode == "minimize":
                report = minimize_unsat_core(instance, core, timeout_ms=args.timeout_ms)
                verified = bool(report["verification"]["is_subset_minimal"])
            else:
                report = verify_unsat_core(instance, core, timeout_ms=args.timeout_ms)
                verified = bool(report["is_subset_minimal"])
            update_result_entry(entry, args.mode, report)
            statuses.append({"instance_name": name, "verified": verified})

        all_verified = all(item["verified"] for item in statuses)
        document["core_verification"] = {
            "mode": args.mode,
            "checked_instances": statuses,
            "checked_count": len(statuses),
            "all_subset_minimal": all_verified,
        }
        summary = document.get("summary")
        if isinstance(summary, dict):
            summary["verified_subset_minimal_cores"] = sum(
                item["verified"] for item in statuses
            )
        destination = args.output if args.output is not None else args.results
        output = write_results(document, destination)
    except (InputValidationError, OSError, ValueError, RuntimeError) as exc:
        print(f"[verify_unsat_core] error: {exc}", file=sys.stderr)
        return 2

    for item in statuses:
        status = "VERIFIED SUBSET-MINIMAL" if item["verified"] else "VERIFICATION FAILED"
        print(f"[verify_unsat_core] {item['instance_name']}: {status}")
    print(f"[verify_unsat_core] checked {len(statuses)} UNSAT core(s) -> {output}")
    return 0 if all_verified else 4


if __name__ == "__main__":
    raise SystemExit(main())
