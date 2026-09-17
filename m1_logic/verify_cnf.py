"""Requirement 1.2: solve and verify CNF produced by ``cnf_encoder.py``."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Sequence

try:
    import z3
except ImportError as exc:  # pragma: no cover - depends on local environment
    raise SystemExit(
        "Missing dependency 'z3-solver'. Run: python -m pip install -r requirements.txt"
    ) from exc


class CNFVerificationError(ValueError):
    """Raised when a CNF document has an invalid shape or literal."""


def load_cnf(path: str | Path) -> dict[str, Any]:
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            document = json.load(handle)
    except FileNotFoundError as exc:
        raise CNFVerificationError(f"input file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CNFVerificationError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(document, dict) or document.get("format") != "cnf":
        raise CNFVerificationError("input must be a CNF JSON document")
    return document


def verify_cnf(document: Mapping[str, Any], timeout_ms: int = 30_000) -> dict[str, Any]:
    """Solve clauses with Z3, then evaluate every clause against the returned model."""

    if timeout_ms <= 0:
        raise CNFVerificationError("timeout_ms must be positive")
    variable_map, raw_clauses = document.get("variables"), document.get("clauses")
    if not isinstance(variable_map, Mapping) or not isinstance(raw_clauses, list):
        raise CNFVerificationError("CNF document requires variables and clauses")

    numbers: set[int] = set()
    for name, number in variable_map.items():
        if (not isinstance(name, str) or not name or isinstance(number, bool)
                or not isinstance(number, int) or number <= 0 or number in numbers):
            raise CNFVerificationError("variables must map unique names to positive integer IDs")
        numbers.add(number)
    if not numbers:
        raise CNFVerificationError("variables must not be empty")
    atoms = {number: z3.Bool(f"v_{number}") for number in numbers}

    clauses: list[tuple[str, list[int]]] = []
    names: set[str] = set()
    for index, item in enumerate(raw_clauses):
        if not isinstance(item, Mapping):
            raise CNFVerificationError(f"clauses[{index}] must be an object")
        name, literals = item.get("name"), item.get("literals")
        if not isinstance(name, str) or not name or name in names:
            raise CNFVerificationError(f"clauses[{index}].name must be unique and non-empty")
        if not isinstance(literals, list) or not literals:
            raise CNFVerificationError(f"clauses[{index}].literals must be a non-empty array")
        if any(isinstance(literal, bool) or not isinstance(literal, int)
               or literal == 0 or abs(literal) not in atoms for literal in literals):
            raise CNFVerificationError(f"clauses[{index}] contains an invalid literal")
        names.add(name)
        clauses.append((name, literals))

    solver = z3.Solver()
    solver.set(timeout=timeout_ms)
    for _, literals in clauses:
        solver.add(z3.Or(*[
            atoms[abs(literal)] if literal > 0 else z3.Not(atoms[abs(literal)])
            for literal in literals
        ]))
    started = perf_counter()
    status = solver.check()
    report: dict[str, Any] = {
        "instance_name": document.get("instance_name"),
        "status": str(status).upper(),
        "variable_count": len(atoms),
        "clause_count": len(clauses),
        "solver": {
            "name": "z3",
            "version": z3.get_version_string(),
            "timeout_ms": timeout_ms,
            "runtime_ms": round((perf_counter() - started) * 1000, 3),
        },
    }
    declared_stats = document.get("statistics")
    if isinstance(declared_stats, Mapping) and isinstance(declared_stats.get("clause_count"), int):
        report["declared_clause_count"] = declared_stats["clause_count"]
        report["clause_count_matches_encoding"] = (
            declared_stats["clause_count"] == len(clauses)
        )
    if status != z3.sat:
        if status == z3.unknown:
            report["reason_unknown"] = solver.reason_unknown()
        return report

    model = solver.model()
    truth = {
        number: z3.is_true(model.eval(atom, model_completion=True))
        for number, atom in atoms.items()
    }
    unsatisfied = [
        name for name, literals in clauses
        if not any(truth[abs(literal)] == (literal > 0) for literal in literals)
    ]
    true_assignments: list[dict[str, str]] = []
    assignments = document.get("assignments", [])
    if isinstance(assignments, list):
        for item in assignments:
            if isinstance(item, Mapping) and truth.get(item.get("variable"), False):
                true_assignments.append({
                    "invigilator": str(item.get("invigilator")),
                    "shift": str(item.get("shift")),
                })
    report.update({
        "all_clauses_satisfied": not unsatisfied,
        "unsatisfied_clauses": unsatisfied,
        "true_assignments": sorted(
            true_assignments, key=lambda item: (item["shift"], item["invigilator"])
        ),
    })
    return report


def write_json(document: Mapping[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Solve and independently verify named CNF clauses.")
    parser.add_argument("--input", required=True, type=Path, help="CNF JSON from cnf_encoder.py")
    parser.add_argument("--output", type=Path, default=None, help="optional verification-report JSON")
    parser.add_argument("--expect-status", choices=("SAT", "UNSAT"), default=None)
    parser.add_argument(
        "--expect-clauses", type=int, default=None,
        help="fail unless the encoded clause count equals this value (use for toy checks)",
    )
    parser.add_argument("--timeout-ms", type=int, default=30_000)
    args = parser.parse_args(argv)
    try:
        report = verify_cnf(load_cnf(args.input), args.timeout_ms)
        if args.output:
            write_json(report, args.output)
    except (CNFVerificationError, OSError, ValueError) as exc:
        print(f"[verify_cnf] error: {exc}")
        return 2
    print(f"[verify_cnf] {report['instance_name']}: {report['status']} "
          f"({report['variable_count']} variables, {report['clause_count']} clauses)")
    if report["status"] == "SAT":
        print(f"[verify_cnf] all clauses satisfied: {report['all_clauses_satisfied']}")
        print(f"[verify_cnf] decoded true assignments: {report['true_assignments']}")
    if args.expect_status and report["status"] != args.expect_status:
        print(f"[verify_cnf] expected {args.expect_status}, got {report['status']}")
        return 4
    if args.expect_clauses is not None and report["clause_count"] != args.expect_clauses:
        print(f"[verify_cnf] expected {args.expect_clauses} clauses, got {report['clause_count']}")
        return 5
    if report.get("clause_count_matches_encoding") is False:
        print("[verify_cnf] declared clause count does not match the actual clauses")
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
