"""Requirement 1.2: encode an IAP JSON instance as named CNF clauses.

The cardinality encoding is deliberately the transparent binomial encoding.
It is practical for the submitted toy/small slice and exposes the clause
growth that motivates the ILP formulation in Module 2.
"""

from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence


class CNFEncodingError(ValueError):
    """Raised when the input does not satisfy the documented IAP schema."""


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CNFEncodingError(f"{label} must be a non-empty string")
    return value.strip()


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise CNFEncodingError(f"{label} must be a JSON array")
    return value


def _unique(values: list[str], label: str) -> tuple[str, ...]:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise CNFEncodingError(f"duplicate {label}: {duplicates}")
    return tuple(values)


def load_iap(path: str | Path) -> dict[str, Any]:
    """Read and validate only the IAP fields needed for the CNF encoding."""

    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except FileNotFoundError as exc:
        raise CNFEncodingError(f"input file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CNFEncodingError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(raw, dict) or raw.get("format", "iap").lower() != "iap":
        raise CNFEncodingError("input must be an IAP JSON document (format: 'iap')")

    staff_raw = _list(raw.get("invigilators"), "invigilators")
    staff = _unique(
        [_id(item.get("id") if isinstance(item, dict) else item, f"invigilators[{i}]")
         for i, item in enumerate(staff_raw)],
        "invigilator IDs",
    )
    if not staff:
        raise CNFEncodingError("invigilators must not be empty")

    shifts: list[str] = []
    capacities: dict[str, int] = {}
    for i, item in enumerate(_list(raw.get("shifts"), "shifts")):
        if not isinstance(item, dict):
            raise CNFEncodingError(f"shifts[{i}] must be an object")
        shift = _id(item.get("id"), f"shifts[{i}].id")
        capacity = item.get("capacity")
        if isinstance(capacity, bool) or not isinstance(capacity, int) or not 0 <= capacity <= len(staff):
            raise CNFEncodingError(f"shifts[{i}].capacity must be an integer from 0 to {len(staff)}")
        shifts.append(shift)
        capacities[shift] = capacity
    shift_ids = _unique(shifts, "shift IDs")
    if not shift_ids:
        raise CNFEncodingError("shifts must not be empty")

    staff_set, shift_set = set(staff), set(shift_ids)

    def read_pairs(field: str, only_ineligible: bool = False) -> set[tuple[str, str]]:
        result: set[tuple[str, str]] = set()
        for i, item in enumerate(_list(raw.get(field, []), field)):
            if not isinstance(item, dict):
                raise CNFEncodingError(f"{field}[{i}] must be an object")
            pair = (_id(item.get("invigilator"), f"{field}[{i}].invigilator"),
                    _id(item.get("shift"), f"{field}[{i}].shift"))
            if pair[0] not in staff_set or pair[1] not in shift_set:
                raise CNFEncodingError(f"{field}[{i}] references an unknown invigilator or shift")
            if only_ineligible:
                if not isinstance(item.get("eligible"), bool):
                    raise CNFEncodingError(f"{field}[{i}].eligible must be Boolean")
                if item["eligible"]:
                    continue
            if pair in result:
                raise CNFEncodingError(f"duplicate {field} entry: {pair}")
            result.add(pair)
        return result

    overlaps: set[tuple[str, str]] = set()
    for i, item in enumerate(_list(raw.get("overlaps", []), "overlaps")):
        pair = _list(item, f"overlaps[{i}]")
        if len(pair) != 2:
            raise CNFEncodingError(f"overlaps[{i}] must contain two shifts")
        left, right = _id(pair[0], f"overlaps[{i}][0]"), _id(pair[1], f"overlaps[{i}][1]")
        if left not in shift_set or right not in shift_set or left == right:
            raise CNFEncodingError(f"overlaps[{i}] must contain distinct known shifts")
        canonical = tuple(sorted((left, right)))
        if canonical in overlaps:
            raise CNFEncodingError(f"duplicate/symmetric overlap: {canonical}")
        overlaps.add(canonical)

    return {
        "instance_name": _id(raw.get("instance_name", "unnamed_instance"), "instance_name"),
        "staff": staff,
        "shifts": shift_ids,
        "capacities": capacities,
        "busy": read_pairs("busy"),
        "ineligible": read_pairs("eligibility", only_ineligible=True),
        "overlaps": tuple(sorted(overlaps)),
        "metadata": raw.get("metadata", {}),
    }


class CNFEncoder:
    """Map each ``Assign(invigilator, shift)`` to one positive DIMACS ID."""

    def __init__(self, instance: Mapping[str, Any]):
        self.instance = instance
        self.variable_of = {
            pair: number
            for number, pair in enumerate(
                itertools.product(instance["staff"], instance["shifts"]), start=1
            )
        }
        self.clauses: list[dict[str, Any]] = []
        self.counts: Counter[str] = Counter()

    def add(self, kind: str, literals: Sequence[int], description: str) -> None:
        if not literals or any(not isinstance(value, int) or value == 0 for value in literals):
            raise AssertionError("CNF clauses require non-zero integer literals")
        self.clauses.append({
            "name": f"c{len(self.clauses) + 1:04d}__{kind}",
            "kind": kind,
            "description": description,
            "literals": list(literals),
        })
        self.counts[kind] += 1

    def at_least_k(self, variables: Sequence[int], k: int, label: str) -> None:
        # Every subset of n-k+1 variables contains at least one true variable.
        for subset in itertools.combinations(variables, len(variables) - k + 1):
            self.add("at_least", subset, f"{label}: at least {k}")

    def at_most_k(self, variables: Sequence[int], k: int, label: str) -> None:
        # No subset of k+1 variables can all be true simultaneously.
        for subset in itertools.combinations(variables, k + 1):
            self.add("at_most", [-variable for variable in subset], f"{label}: at most {k}")

    def exactly_k(self, variables: Sequence[int], k: int, label: str) -> None:
        self.at_least_k(variables, k, label)
        self.at_most_k(variables, k, label)

    def encode(self) -> dict[str, Any]:
        for person, shift in sorted(self.instance["busy"]):
            self.add("availability", [-self.variable_of[(person, shift)]],
                     f"Busy({person}, {shift}) -> not Assign({person}, {shift})")
        for person, shift in sorted(self.instance["ineligible"]):
            self.add("eligibility", [-self.variable_of[(person, shift)]],
                     f"{person} is ineligible for {shift}")
        for left, right in self.instance["overlaps"]:
            for person in self.instance["staff"]:
                self.add("no_double_booking",
                         [-self.variable_of[(person, left)], -self.variable_of[(person, right)]],
                         f"{person} cannot cover overlapping shifts {left} and {right}")
        for shift in self.instance["shifts"]:
            variables = [self.variable_of[(person, shift)] for person in self.instance["staff"]]
            self.exactly_k(variables, self.instance["capacities"][shift], f"capacity({shift})")

        return {
            "schema_version": "1.0",
            "instance_name": f"{self.instance['instance_name']}__cnf",
            "source_instance": self.instance["instance_name"],
            "format": "cnf",
            "variables": {f"Assign({person},{shift})": number
                          for (person, shift), number in self.variable_of.items()},
            "assignments": [{"variable": number, "invigilator": person, "shift": shift}
                            for (person, shift), number in self.variable_of.items()],
            "clauses": self.clauses,
            "statistics": {
                "variable_count": len(self.variable_of),
                "clause_count": len(self.clauses),
                "clauses_by_kind": dict(sorted(self.counts.items())),
                "cardinality_encoding": "naive combinatorial subsets",
            },
            "metadata": self.instance["metadata"],
        }


def encode_instance(path: str | Path) -> dict[str, Any]:
    return CNFEncoder(load_iap(path)).encode()


def write_json(document: Mapping[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Encode IAP constraints as named CNF clauses.")
    parser.add_argument("--input", required=True, type=Path, help="IAP JSON input")
    parser.add_argument("--output", required=True, type=Path, help="CNF JSON output")
    args = parser.parse_args(argv)
    try:
        document = encode_instance(args.input)
        output = write_json(document, args.output)
    except (CNFEncodingError, OSError, ValueError) as exc:
        print(f"[cnf_encoder] error: {exc}")
        return 2
    stats = document["statistics"]
    print(f"[cnf_encoder] {document['source_instance']}: {stats['variable_count']} variables, "
          f"{stats['clause_count']} clauses -> {output}")
    print(f"[cnf_encoder] clauses by kind: {stats['clauses_by_kind']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
