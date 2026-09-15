from __future__ import annotations

import argparse
import json
import random
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Mapping

def read_excel_records(excel_path: str | Path) -> list[dict[str, str]]:
    path = Path(excel_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Excel file not found: {path}")

    with zipfile.ZipFile(path, "r") as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            tree = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            for si in tree.findall(".//m:si", ns):
                elems = si.findall(".//m:t", ns)
                shared_strings.append("".join(e.text or "" for e in elems))

        sheet_tree = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        rows = sheet_tree.findall(".//m:row", ns)

        if not rows:
            return []

        records: list[dict[str, str]] = []
        for row in rows[1:]:
            row_dict: dict[str, str] = {}
            for cell in row.findall("m:c", ns):
                cell_ref = cell.attrib.get("r", "")
                col_name = "".join(ch for ch in cell_ref if ch.isalpha())
                cell_type = cell.attrib.get("t", "")
                val_node = cell.find("m:v", ns)
                val = val_node.text if val_node is not None else ""
                if cell_type == "s" and val.isdigit():
                    val = shared_strings[int(val)]
                row_dict[col_name] = val
            records.append(row_dict)

    return records

def parse_time_minutes(time_str: str) -> int:
    time_str = time_str.lower().strip()
    if "g" in time_str:
        parts = time_str.split("g")
        hour = int(parts[0]) if parts[0].isdigit() else 0
        minute = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        return hour * 60 + minute
    return 0

def extract_slices(
    excel_path: str | Path,
    seed: int = 287892112,
    num_shifts: int = 4,
) -> tuple[dict[str, Any], dict[str, Any]]:
    records = read_excel_records(excel_path)
    if not records:
        raise ValueError("Excel file contains no data rows.")

    shift_info: dict[str, dict[str, Any]] = {}
    for r in records:
        shift_id = r.get("D", "").strip()
        staff_id = r.get("F", "").strip()
        if not shift_id or not staff_id:
            continue

        if shift_id not in shift_info:
            duration = float(r.get("G", 150) or 150)
            start_min = parse_time_minutes(r.get("C", ""))
            shift_info[shift_id] = {
                "id": shift_id,
                "day": r.get("B", "").strip(),
                "time_str": r.get("C", "").strip(),
                "start_min": start_min,
                "duration": duration,
                "end_min": start_min + int(duration),
                "campus": r.get("I", "").strip(),
                "staff": set(),
            }
        shift_info[shift_id]["staff"].add(staff_id)

    eligible_shifts = [
        sid for sid, info in shift_info.items()
        if 1 <= len(info["staff"]) <= 5
    ]
    eligible_shifts.sort()

    rng = random.Random(seed)
    if len(eligible_shifts) < num_shifts:
        selected_shift_ids = eligible_shifts
    else:
        selected_shift_ids = sorted(rng.sample(eligible_shifts, num_shifts))

    selected_shifts = [shift_info[sid] for sid in selected_shift_ids]

    all_staff_set: set[str] = set()
    for s in selected_shifts:
        all_staff_set.update(s["staff"])
    invigilators = sorted(list(all_staff_set))

    shifts_payload = [
        {"id": s["id"], "capacity": len(s["staff"])}
        for s in selected_shifts
    ]

    overlaps_set: set[tuple[str, str]] = set()
    for i in range(len(selected_shifts)):
        for j in range(i + 1, len(selected_shifts)):
            s1, s2 = selected_shifts[i], selected_shifts[j]
            if s1["day"] == s2["day"]:
                if max(s1["start_min"], s2["start_min"]) < min(s1["end_min"], s2["end_min"]):
                    pair = tuple(sorted((s1["id"], s2["id"])))
                    overlaps_set.add(pair)
    overlaps_payload = [list(pair) for pair in sorted(overlaps_set)]

    sat_busy: list[dict[str, str]] = []
    for s in selected_shifts:
        non_assigned = [p for p in invigilators if p not in s["staff"]]
        if non_assigned:
            busy_count = rng.randint(0, min(2, len(non_assigned)))
            chosen_busy = rng.sample(non_assigned, busy_count)
            for person in sorted(chosen_busy):
                sat_busy.append({"invigilator": person, "shift": s["id"]})

    sat_instance: dict[str, Any] = {
        "schema_version": "1.0",
        "instance_name": f"excel_slice_sat_seed_{seed}",
        "format": "iap",
        "invigilators": invigilators,
        "shifts": shifts_payload,
        "busy": sat_busy,
        "overlaps": overlaps_payload,
        "eligibility": [],
        "metadata": {
            "seed": seed,
            "source_file": Path(excel_path).name,
            "selected_shifts": selected_shift_ids,
            "num_invigilators": len(invigilators),
            "expected_status": "SAT",
            "description": "Deterministic slice from real Faculty exam schedule with historically feasible assignment.",
        },
    }

    target_shift = selected_shifts[0]
    target_id = target_shift["id"]
    target_capacity = len(target_shift["staff"])
    available_for_target = [
        p for p in invigilators
        if {"invigilator": p, "shift": target_id} not in sat_busy
    ]

    forced_busy_count = max(0, len(available_for_target) - target_capacity + 1)
    new_busy_people = sorted(rng.sample(available_for_target, forced_busy_count))

    unsat_busy = [dict(entry) for entry in sat_busy]
    for person in new_busy_people:
        unsat_busy.append({"invigilator": person, "shift": target_id})

    unsat_busy.sort(key=lambda x: (x["invigilator"], x["shift"]))

    unsat_instance: dict[str, Any] = {
        "schema_version": "1.0",
        "instance_name": f"excel_slice_unsat_seed_{seed}",
        "format": "iap",
        "invigilators": invigilators,
        "shifts": shifts_payload,
        "busy": unsat_busy,
        "overlaps": overlaps_payload,
        "eligibility": [],
        "metadata": {
            "seed": seed,
            "source_file": Path(excel_path).name,
            "selected_shifts": selected_shift_ids,
            "num_invigilators": len(invigilators),
            "expected_status": "UNSAT",
            "unsat_rationale": (
                f"Shift '{target_id}' requires capacity={target_capacity}, but {forced_busy_count} "
                f"additional invigilator(s) {new_busy_people} were marked busy, leaving only "
                f"{len(available_for_target) - forced_busy_count} available staff member(s). "
                f"This strictly violates the exact capacity requirement."
            ),
        },
    }

    return sat_instance, unsat_instance

def save_json(data: Mapping[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return path

def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare SAT and UNSAT slices from Excel dataset.")
    parser.add_argument(
        "--excel",
        type=Path,
        default=Path("data/Dataset_Anonymized_Invigilator_Assignment_Problem.xlsx"),
        help="Path to Excel dataset file.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=287892112,
        help="Deterministic random seed.",
    )
    parser.add_argument(
        "--num-shifts",
        type=int,
        default=4,
        help="Number of shifts to include in slice.",
    )
    parser.add_argument(
        "--out-sat",
        type=Path,
        default=Path("data/generated/m1_sat_slice.json"),
        help="Destination path for SAT slice JSON.",
    )
    parser.add_argument(
        "--out-unsat",
        type=Path,
        default=Path("data/generated/m1_unsat_slice.json"),
        help="Destination path for UNSAT slice JSON.",
    )
    args = parser.parse_args()

    sat_inst, unsat_inst = extract_slices(
        excel_path=args.excel,
        seed=args.seed,
        num_shifts=args.num_shifts,
    )

    path_sat = save_json(sat_inst, args.out_sat)
    path_unsat = save_json(unsat_inst, args.out_unsat)

    save_json(sat_inst, Path("data/m1_sat_slice.json"))
    save_json(unsat_inst, Path("data/m1_unsat_slice.json"))

    print(f"[prepare_logic_data] SAT slice saved to: {path_sat}")
    print(f"[prepare_logic_data] UNSAT slice saved to: {path_unsat}")
    print(f"[prepare_logic_data] Synced to data/m1_sat_slice.json and data/m1_unsat_slice.json")

if __name__ == "__main__":
    main()
