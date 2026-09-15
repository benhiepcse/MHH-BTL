from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

def get_toy_instance(variant: str = "sat") -> dict[str, Any]:
    variant = variant.lower().strip()
    if variant not in {"sat", "unsat"}:
        raise ValueError(f"Unknown variant: {variant!r}. Expected 'sat' or 'unsat'.")

    invigilators = ["CB1", "CB2", "CB3"]
    shifts = [
        {"id": "Morning", "capacity": 2},
        {"id": "Afternoon", "capacity": 2},
    ]

    if variant == "sat":
        busy = [
            {"invigilator": "CB1", "shift": "Morning"}
        ]
        instance_name = "toy_instance_sat"
    else:
        busy = [
            {"invigilator": "CB1", "shift": "Morning"},
            {"invigilator": "CB2", "shift": "Morning"},
        ]
        instance_name = "toy_instance_unsat"

    return {
        "schema_version": "1.0",
        "instance_name": instance_name,
        "format": "iap",
        "invigilators": invigilators,
        "shifts": shifts,
        "busy": busy,
        "overlaps": [],
        "eligibility": [],
    }

def save_instance(instance: Mapping[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(instance, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return path

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate CO2011 Module 1 Toy Instances.")
    parser.add_argument(
        "--variant",
        choices=["sat", "unsat"],
        default="sat",
        help="Variant of toy instance to generate (sat or unsat).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path to save JSON. If omitted, prints JSON to stdout.",
    )
    args = parser.parse_args()

    data = get_toy_instance(variant=args.variant)

    if args.output:
        saved_path = save_instance(data, args.output)
        print(f"Toy instance ({args.variant}) saved to {saved_path}")
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
