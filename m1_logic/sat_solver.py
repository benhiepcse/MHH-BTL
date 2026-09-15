from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable, Mapping, Sequence

try:
    import z3
except ImportError as exc:  # pragma: no cover - depends on local environment
    raise SystemExit(
        "Missing dependency 'z3-solver'. Install the pinned requirements with "
        "'python -m pip install -r requirements.txt'."
    ) from exc


SCHEMA_VERSION = "1.0"
MODULE = "M1"
REQUIREMENT = "1.2"
TASK = "W02-T4"
DEFAULT_OUTPUT = Path("data/generated/m1_results.json")
_SAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]+")


class InputValidationError(ValueError):
    """Raised when an input instance violates the documented data contract."""


@dataclass(frozen=True, order=True)
class AssignmentRecord:
    """One decoded invigilator-to-shift assignment."""

    shift: str
    invigilator: str


@dataclass(frozen=True)
class ValidationResult:
    """Result of independently checking a decoded IAP assignment."""

    valid: bool
    violations: tuple[str, ...]


@dataclass(frozen=True)
class TrackedConstraint:
    """A Z3 expression paired with its stable, human-readable name."""

    name: str
    expression: Any


def _require_mapping(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InputValidationError(f"{where} must be a JSON object")
    return value


def _require_list(value: Any, where: str) -> list[Any]:
    if not isinstance(value, list):
        raise InputValidationError(f"{where} must be a JSON array")
    return value


def _nonempty_id(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputValidationError(f"{where} must be a non-empty string")
    return value.strip()


def _safe_token(value: str) -> str:
    token = _SAFE_NAME.sub("_", value).strip("_")
    return token or "unnamed"


def _unique_ids(values: Iterable[str], where: str) -> tuple[str, ...]:
    result = tuple(values)
    duplicates = sorted({item for item in result if result.count(item) > 1})
    if duplicates:
        raise InputValidationError(f"duplicate {where}: {duplicates}")
    return result


def load_instance(source: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    """Load an instance from a mapping or UTF-8 JSON file and validate its root."""

    if isinstance(source, Mapping):
        data = dict(source)
    else:
        path = Path(source).expanduser().resolve()
        if not path.is_file():
            raise InputValidationError(f"input file does not exist: {path}")
        try:
            with path.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
        except UnicodeDecodeError as exc:
            raise InputValidationError(f"input must be UTF-8 JSON: {path}") from exc
        except json.JSONDecodeError as exc:
            raise InputValidationError(
                f"invalid JSON in {path} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
            ) from exc
        data = dict(_require_mapping(data, "document root"))
        data.setdefault("source", str(path))

    version = data.get("schema_version", SCHEMA_VERSION)
    if version != SCHEMA_VERSION:
        raise InputValidationError(
            f"unsupported schema_version {version!r}; expected {SCHEMA_VERSION!r}"
        )
    data["schema_version"] = version
    data["instance_name"] = _nonempty_id(
        data.get("instance_name", "unnamed_instance"), "instance_name"
    )
    data["format"] = str(data.get("format", "iap")).lower()
    if data["format"] not in {"iap", "cnf"}:
        raise InputValidationError("format must be either 'iap' or 'cnf'")
    return data


class InvigilatorSATSolver:
    """Build, solve, explain and independently validate one SAT instance."""

    def __init__(self, instance: Mapping[str, Any], timeout_ms: int = 30_000):
        if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise InputValidationError("timeout_ms must be a positive integer")
        self.instance = load_instance(instance)
        self.timeout_ms = timeout_ms
        self.variables: dict[Any, Any] = {}
        self.assignment_keys: dict[Any, tuple[str, str]] = {}
        self.constraints: list[TrackedConstraint] = []
        self._constraint_names: set[str] = set()
        self._iap: dict[str, Any] | None = None
        self._cnf_clauses: list[tuple[str, tuple[int, ...]]] | None = None
        self._build()

    def _add_constraint(self, name: str, expression: Any) -> None:
        name = _nonempty_id(name, "constraint name")
        if name in self._constraint_names:
            raise InputValidationError(f"duplicate constraint name: {name}")
        self._constraint_names.add(name)
        self.constraints.append(TrackedConstraint(name, expression))

    def _build(self) -> None:
        if self.instance["format"] == "iap":
            self._build_iap()
        else:
            self._build_cnf()

    def _build_iap(self) -> None:
        raw_staff = _require_list(self.instance.get("invigilators"), "invigilators")
        staff = _unique_ids(
            (_nonempty_id(x.get("id") if isinstance(x, Mapping) else x,
                          f"invigilators[{index}]")
             for index, x in enumerate(raw_staff)),
            "invigilator IDs",
        )
        if not staff:
            raise InputValidationError("invigilators must not be empty")

        raw_shifts = _require_list(self.instance.get("shifts"), "shifts")
        shifts: list[str] = []
        capacities: dict[str, int] = {}
        for index, raw in enumerate(raw_shifts):
            item = _require_mapping(raw, f"shifts[{index}]")
            shift = _nonempty_id(item.get("id"), f"shifts[{index}].id")
            capacity = item.get("capacity")
            if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 0:
                raise InputValidationError(
                    f"shifts[{index}].capacity must be a non-negative integer"
                )
            if capacity > len(staff):
                raise InputValidationError(
                    f"shift {shift!r} capacity {capacity} exceeds {len(staff)} invigilators"
                )
            shifts.append(shift)
            capacities[shift] = capacity
        shift_ids = _unique_ids(shifts, "shift IDs")
        if not shift_ids:
            raise InputValidationError("shifts must not be empty")

        staff_set, shift_set = set(staff), set(shift_ids)
        busy: set[tuple[str, str]] = set()
        for index, raw in enumerate(_require_list(self.instance.get("busy", []), "busy")):
            item = _require_mapping(raw, f"busy[{index}]")
            pair = (
                _nonempty_id(item.get("invigilator"), f"busy[{index}].invigilator"),
                _nonempty_id(item.get("shift"), f"busy[{index}].shift"),
            )
            self._validate_pair(pair, staff_set, shift_set, f"busy[{index}]")
            if pair in busy:
                raise InputValidationError(f"duplicate busy entry: {pair}")
            busy.add(pair)

        ineligible: set[tuple[str, str]] = set()
        eligibility_seen: set[tuple[str, str]] = set()
        for index, raw in enumerate(
            _require_list(self.instance.get("eligibility", []), "eligibility")
        ):
            item = _require_mapping(raw, f"eligibility[{index}]")
            pair = (
                _nonempty_id(item.get("invigilator"), f"eligibility[{index}].invigilator"),
                _nonempty_id(item.get("shift"), f"eligibility[{index}].shift"),
            )
            self._validate_pair(pair, staff_set, shift_set, f"eligibility[{index}]")
            if pair in eligibility_seen:
                raise InputValidationError(f"duplicate eligibility entry: {pair}")
            eligibility_seen.add(pair)
            eligible = item.get("eligible")
            if not isinstance(eligible, bool):
                raise InputValidationError(f"eligibility[{index}].eligible must be Boolean")
            if not eligible:
                ineligible.add(pair)

        overlaps: set[tuple[str, str]] = set()
        for index, raw in enumerate(
            _require_list(self.instance.get("overlaps", []), "overlaps")
        ):
            pair_raw = _require_list(raw, f"overlaps[{index}]")
            if len(pair_raw) != 2:
                raise InputValidationError(f"overlaps[{index}] must contain exactly two shift IDs")
            left = _nonempty_id(pair_raw[0], f"overlaps[{index}][0]")
            right = _nonempty_id(pair_raw[1], f"overlaps[{index}][1]")
            if left not in shift_set or right not in shift_set:
                raise InputValidationError(f"overlaps[{index}] references an unknown shift")
            if left == right:
                raise InputValidationError(f"overlaps[{index}] is reflexive: {left!r}")
            canonical = tuple(sorted((left, right)))
            if canonical in overlaps:
                raise InputValidationError(f"duplicate/symmetric overlap entry: {canonical}")
            overlaps.add(canonical)

        for invigilator in staff:
            for shift in shift_ids:
                key = (invigilator, shift)
                self.variables[key] = z3.Bool(
                    f"assign__{_safe_token(invigilator)}__{_safe_token(shift)}"
                )
                self.assignment_keys[key] = key

        if len({str(variable) for variable in self.variables.values()}) != len(self.variables):
            raise InputValidationError(
                "invigilator/shift IDs collide after safe-name normalization; rename the IDs"
            )

        for shift in shift_ids:
            terms = [(self.variables[(person, shift)], 1) for person in staff]
            self._add_constraint(
                f"capacity__{shift}", z3.PbEq(terms, capacities[shift])
            )
        for person, shift in sorted(busy):
            self._add_constraint(
                f"availability__{person}__{shift}",
                z3.Not(self.variables[(person, shift)]),
            )
        for person, shift in sorted(ineligible):
            self._add_constraint(
                f"eligibility__{person}__{shift}",
                z3.Not(self.variables[(person, shift)]),
            )
        for left, right in sorted(overlaps):
            for person in staff:
                self._add_constraint(
                    f"overlap__{person}__{left}__{right}",
                    z3.Or(
                        z3.Not(self.variables[(person, left)]),
                        z3.Not(self.variables[(person, right)]),
                    ),
                )

        self._iap = {
            "staff": staff,
            "shifts": shift_ids,
            "capacities": capacities,
            "busy": busy,
            "ineligible": ineligible,
            "overlaps": overlaps,
        }

    @staticmethod
    def _validate_pair(
        pair: tuple[str, str], staff: set[str], shifts: set[str], where: str
    ) -> None:
        person, shift = pair
        if person not in staff:
            raise InputValidationError(f"{where} references unknown invigilator {person!r}")
        if shift not in shifts:
            raise InputValidationError(f"{where} references unknown shift {shift!r}")

    def _build_cnf(self) -> None:
        raw_variables = _require_mapping(self.instance.get("variables"), "variables")
        number_to_name: dict[int, str] = {}
        for raw_name, raw_number in raw_variables.items():
            name = _nonempty_id(raw_name, "variables key")
            if isinstance(raw_number, bool) or not isinstance(raw_number, int) or raw_number <= 0:
                raise InputValidationError(f"variable {name!r} must map to a positive integer")
            if raw_number in number_to_name:
                raise InputValidationError(f"duplicate CNF variable number: {raw_number}")
            number_to_name[raw_number] = name
            self.variables[raw_number] = z3.Bool(f"cnf__{raw_number}__{_safe_token(name)}")
        if not self.variables:
            raise InputValidationError("variables must not be empty")

        self._cnf_clauses = []
        for index, raw in enumerate(_require_list(self.instance.get("clauses"), "clauses")):
            item = _require_mapping(raw, f"clauses[{index}]")
            name = _nonempty_id(item.get("name"), f"clauses[{index}].name")
            literals = _require_list(item.get("literals"), f"clauses[{index}].literals")
            if not literals:
                expression = z3.BoolVal(False)
            else:
                terms = []
                for position, literal in enumerate(literals):
                    if isinstance(literal, bool) or not isinstance(literal, int) or literal == 0:
                        raise InputValidationError(
                            f"clauses[{index}].literals[{position}] must be a non-zero integer"
                        )
                    variable = self.variables.get(abs(literal))
                    if variable is None:
                        raise InputValidationError(
                            f"clause {name!r} references unmapped variable {abs(literal)}"
                        )
                    terms.append(variable if literal > 0 else z3.Not(variable))
                expression = z3.Or(*terms)
            self._add_constraint(name, expression)
            self._cnf_clauses.append((name, tuple(literals)))

        seen_assignment_vars: set[int] = set()
        for index, raw in enumerate(
            _require_list(self.instance.get("assignments", []), "assignments")
        ):
            item = _require_mapping(raw, f"assignments[{index}]")
            number = item.get("variable")
            if isinstance(number, bool) or not isinstance(number, int) or number not in self.variables:
                raise InputValidationError(f"assignments[{index}].variable is not mapped")
            if number in seen_assignment_vars:
                raise InputValidationError(f"duplicate assignment mapping for variable {number}")
            seen_assignment_vars.add(number)
            self.assignment_keys[number] = (
                _nonempty_id(item.get("invigilator"), f"assignments[{index}].invigilator"),
                _nonempty_id(item.get("shift"), f"assignments[{index}].shift"),
            )

    def _new_solver(self, selected_names: set[str] | None = None) -> tuple[Any, dict[str, str]]:
        solver = z3.Solver()
        solver.set(timeout=self.timeout_ms)
        tracker_to_name: dict[str, str] = {}
        for index, constraint in enumerate(self.constraints):
            if selected_names is not None and constraint.name not in selected_names:
                continue
            tracker_name = f"track__{index}"
            tracker = z3.Bool(tracker_name)
            tracker_to_name[tracker_name] = constraint.name
            solver.assert_and_track(constraint.expression, tracker)
        return solver, tracker_to_name

    def _check_names(self, names: Sequence[str]) -> tuple[str, float]:
        solver, _ = self._new_solver(set(names))
        started = perf_counter()
        status = solver.check()
        elapsed_ms = (perf_counter() - started) * 1000.0
        return str(status).upper(), elapsed_ms

    def _minimize_core(self, names: Sequence[str]) -> tuple[list[str], list[dict[str, Any]]]:
        candidate = list(dict.fromkeys(names))
        checks: list[dict[str, Any]] = []
        index = 0
        while index < len(candidate):
            removed = candidate[index]
            trial = candidate[:index] + candidate[index + 1 :]
            status, runtime_ms = self._check_names(trial)
            checks.append(
                {
                    "removed_constraint": removed,
                    "remaining_status": status,
                    "runtime_ms": round(runtime_ms, 3),
                    "necessary": status == "SAT",
                }
            )
            if status == "UNSAT":
                candidate = trial
            elif status == "SAT":
                index += 1
            else:
                raise RuntimeError(
                    f"solver returned {status} while minimizing core after removing {removed!r}"
                )
        return candidate, checks

    def _verify_minimal_core(
        self, names: Sequence[str]
    ) -> tuple[bool, float, list[dict[str, Any]]]:
        """Recheck UNSAT and every single-removal subset of a candidate core."""

        full_status, full_runtime_ms = self._check_names(names)
        if full_status != "UNSAT":
            return False, full_runtime_ms, []
        checks: list[dict[str, Any]] = []
        for index, removed in enumerate(names):
            trial = list(names[:index]) + list(names[index + 1 :])
            status, runtime_ms = self._check_names(trial)
            checks.append(
                {
                    "removed_constraint": removed,
                    "remaining_status": status,
                    "runtime_ms": round(runtime_ms, 3),
                    "necessary": status == "SAT",
                }
            )
        is_minimal = bool(names) and all(item["necessary"] for item in checks)
        return is_minimal, full_runtime_ms, checks

    def decode_model(self, model: Any) -> list[AssignmentRecord]:
        """Decode true assignment variables from a SAT Z3 model."""

        records: list[AssignmentRecord] = []
        for key, (person, shift) in self.assignment_keys.items():
            if z3.is_true(model.eval(self.variables[key], model_completion=True)):
                records.append(AssignmentRecord(shift=shift, invigilator=person))
        return sorted(records)

    def validate_assignment(self, records: Sequence[AssignmentRecord]) -> ValidationResult:
        """Independently check decoded records against high-level hard constraints."""

        if self._iap is None:
            return ValidationResult(True, ())
        data = self._iap
        assigned = {(item.invigilator, item.shift) for item in records}
        violations: list[str] = []
        if len(assigned) != len(records):
            violations.append("decoded assignment contains duplicate records")
        valid_pairs = {(p, s) for p in data["staff"] for s in data["shifts"]}
        for pair in sorted(assigned - valid_pairs):
            violations.append(f"assignment outside domain: {pair[0]} -> {pair[1]}")
        for shift in data["shifts"]:
            actual = sum((person, shift) in assigned for person in data["staff"])
            required = data["capacities"][shift]
            if actual != required:
                violations.append(
                    f"capacity violation at {shift}: assigned={actual}, required={required}"
                )
        for person, shift in sorted(assigned & data["busy"]):
            violations.append(f"availability violation: {person} is busy at {shift}")
        for person, shift in sorted(assigned & data["ineligible"]):
            violations.append(f"eligibility violation: {person} is ineligible for {shift}")
        for left, right in sorted(data["overlaps"]):
            for person in data["staff"]:
                if (person, left) in assigned and (person, right) in assigned:
                    violations.append(f"overlap violation: {person} assigned to {left} and {right}")
        return ValidationResult(not violations, tuple(violations))

    def _validate_cnf_model(self, model: Any) -> ValidationResult:
        """Evaluate every CNF clause again using ordinary Python Boolean logic."""

        if self._cnf_clauses is None:
            return ValidationResult(True, ())
        values = {
            number: z3.is_true(model.eval(variable, model_completion=True))
            for number, variable in self.variables.items()
        }
        violations: list[str] = []
        for name, literals in self._cnf_clauses:
            satisfied = any(
                values[abs(literal)] if literal > 0 else not values[abs(literal)]
                for literal in literals
            )
            if not satisfied:
                violations.append(f"CNF clause is false under decoded model: {name}")
        return ValidationResult(not violations, tuple(violations))

    def solve(self) -> dict[str, Any]:
        """Solve the instance and return a JSON-serializable result object."""

        solver, tracker_to_name = self._new_solver()
        started = perf_counter()
        status = solver.check()
        runtime_ms = (perf_counter() - started) * 1000.0
        common: dict[str, Any] = {
            "instance_name": self.instance["instance_name"],
            "source": self.instance.get("source"),
            "format": self.instance["format"],
            "status": str(status).upper(),
            "statistics": {
                "variables": len(self.variables),
                "assignment_variables": len(self.assignment_keys),
                "constraints": len(self.constraints),
            },
            "runtime_ms": round(runtime_ms, 3),
        }
        if status == z3.sat:
            model = solver.model()
            records = self.decode_model(model)
            validation = (
                self.validate_assignment(records)
                if self._iap is not None
                else self._validate_cnf_model(model)
            )
            if not validation.valid:
                raise RuntimeError(
                    "internal correctness failure: SAT model failed independent validation: "
                    + "; ".join(validation.violations)
                )
            common.update(
                assignment=[asdict(record) for record in records],
                validation=asdict(validation),
                unsat_core=None,
            )
        elif status == z3.unsat:
            initial = [tracker_to_name[str(item)] for item in solver.unsat_core()]
            minimal, shrinking_checks = self._minimize_core(initial)
            is_minimal, verification_ms, verification_checks = (
                self._verify_minimal_core(minimal)
            )
            if not is_minimal:
                raise RuntimeError("failed to establish a subset-minimal UNSAT core")
            common.update(
                assignment=None,
                validation=None,
                unsat_core={
                    "initial": initial,
                    "initial_size": len(initial),
                    "subset_minimal": minimal,
                    "final_size": len(minimal),
                    "is_unsat": True,
                    "is_subset_minimal": True,
                    "verification_runtime_ms": round(verification_ms, 3),
                    "shrinking_checks": shrinking_checks,
                    "removal_checks": verification_checks,
                },
            )
        else:
            common.update(
                assignment=None,
                validation=None,
                unsat_core=None,
                reason_unknown=solver.reason_unknown(),
            )
        return common


def solve_instance(
    source: str | Path | Mapping[str, Any], *, timeout_ms: int = 30_000
) -> dict[str, Any]:
    """Public API used by ``run_all.py`` and tests."""

    return InvigilatorSATSolver(load_instance(source), timeout_ms=timeout_ms).solve()


def build_results_document(
    result: Mapping[str, Any], *, team_id: str | None, seed: int | None
) -> dict[str, Any]:
    """Wrap one solver result in the stable M1 output envelope."""

    status = result.get("status")
    successful = status in {"SAT", "UNSAT"}
    return {
        "schema_version": SCHEMA_VERSION,
        "module": MODULE,
        "requirement": REQUIREMENT,
        "task": TASK,
        "team_id": team_id,
        "seed": seed,
        "solver": {
            "name": "z3",
            "version": z3.get_version_string(),
        },
        "instances": [dict(result)],
        "summary": {
            "all_runs_successful": successful,
            "sat_instances": int(status == "SAT"),
            "unsat_instances": int(status == "UNSAT"),
            "unknown_instances": int(status == "UNKNOWN"),
        },
    }


def write_results(document: Mapping[str, Any], output: str | Path) -> Path:
    """Atomically write finite JSON data as UTF-8 and return the resolved path."""

    def reject_non_finite(value: float) -> None:
        if not math.isfinite(value):
            raise ValueError(f"non-finite JSON number is not allowed: {value}")

    path = Path(output).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(
            document,
            stream,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
            default=reject_non_finite,
        )
        stream.write("\n")
    temporary.replace(path)
    return path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Solve a named IAP/CNF SAT instance and emit deterministic JSON."
    )
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 instance JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="result JSON path")
    parser.add_argument("--seed", type=int, default=None, help="team seed recorded in output")
    parser.add_argument("--team-id", default=None, help="canonical CO2011 team ID")
    parser.add_argument(
        "--timeout-ms", type=int, default=30_000, help="positive Z3 timeout in milliseconds"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point."""

    args = _parser().parse_args(argv)
    try:
        if args.input.expanduser().resolve() == args.output.expanduser().resolve():
            raise InputValidationError("--output must not overwrite --input")
        result = solve_instance(args.input, timeout_ms=args.timeout_ms)
        document = build_results_document(result, team_id=args.team_id, seed=args.seed)
        output = write_results(document, args.output)
    except (InputValidationError, OSError, ValueError, RuntimeError) as exc:
        print(f"[sat_solver] error: {exc}", file=sys.stderr)
        return 2

    print(
        f"[sat_solver] {result['instance_name']}: {result['status']} -> {output}",
        file=sys.stdout,
    )
    return 0 if result["status"] in {"SAT", "UNSAT"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
