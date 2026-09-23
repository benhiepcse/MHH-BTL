from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def seed_for(team_id: str) -> int:
    h = hashlib.blake2b(team_id.strip().encode("utf-8"), digest_size=8).hexdigest()
    return int(h, 16) % (2**31 - 1)


def soft_weights(team_id: str) -> list[float]:
    rng = random.Random(seed_for(team_id))
    return [round(rng.uniform(0.5, 2.0), 2) for _ in range(3)]


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

            shift_id = row_dict.get("D", "").strip()
            staff_id = row_dict.get("F", "").strip()
            if shift_id and staff_id:
                records.append(row_dict)

    return records


def parse_time_minutes(time_str: str) -> tuple[str, int]:
    text = str(time_str).lower().strip()
    hour, minute = 0, 0
    if "g" in text:
        parts = text.split("g")
        hour = int(parts[0]) if parts[0].isdigit() else 0
        minute = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    elif ":" in text:
        parts = text.split(":")
        hour = int(parts[0]) if parts[0].isdigit() else 0
        minute = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    formatted = f"{hour:02d}:{minute:02d}"
    return formatted, hour * 60 + minute


def format_minutes_to_time(total_min: int) -> str:
    total_min = total_min % (24 * 60)
    hour = total_min // 60
    minute = total_min % 60
    return f"{hour:02d}:{minute:02d}"


def excel_date_to_iso(date_val: str) -> str:
    val = date_val.strip()
    try:
        serial = float(val)
        base = datetime(1899, 12, 30)
        dt = base + timedelta(days=serial)
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    try:
        dt = datetime.strptime(val, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    match = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", val)
    if match:
        return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
    match_vn = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", val)
    if match_vn:
        return f"{int(match_vn.group(3)):04d}-{int(match_vn.group(2)):02d}-{int(match_vn.group(1)):02d}"
    return val


def extract_weekday(desc_text: str, fallback_date_iso: str) -> str:
    match = re.search(r"\b(Thứ\s+[2-7]|Chủ\s+nhật)\b", str(desc_text), flags=re.IGNORECASE)
    if match:
        token = match.group(1).title()
        if "Chu" in token or "Chủ" in token:
            return "Chủ nhật"
        return token
    try:
        dt = datetime.strptime(fallback_date_iso, "%Y-%m-%d")
        wd = dt.weekday()
        if wd == 6:
            return "Chủ nhật"
        return f"Thứ {wd + 2}"
    except Exception:
        return ""


def clean_records(raw_records: list[dict[str, str]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []

    for r in raw_records:
        desc = r.get("A", "").strip()
        date_raw = r.get("B", "").strip()
        time_raw = r.get("C", "").strip()
        shift_id = r.get("D", "").strip()
        task = r.get("E", "").strip()
        staff_id = r.get("F", "").strip()
        duration_raw = r.get("G", "150").strip()
        weekday = r.get("H", "").strip()
        campus = r.get("I", "").strip()

        date_iso = excel_date_to_iso(date_raw)
        start_time_fmt, start_min = parse_time_minutes(time_raw)
        duration_min = int(float(duration_raw)) if duration_raw else 150
        end_time_fmt = format_minutes_to_time(start_min + duration_min)

        if not campus:
            if "LTK" in task:
                campus = "Cơ sở 1"
            elif "DiAn" in task:
                campus = "Cơ sở 2"
            else:
                campus = "Cơ sở 1"

        if not weekday:
            weekday = extract_weekday(desc, date_iso)

        cleaned.append({
            "shift_description": desc,
            "date": date_iso,
            "start_time": start_time_fmt,
            "end_time": end_time_fmt,
            "duration_minutes": duration_min,
            "shift_id": shift_id,
            "task": task,
            "invigilator_id": staff_id,
            "weekday": weekday,
            "campus": campus,
        })

    return cleaned


def generate_simulated_preferences(
    invigilators: list[str],
    seed: int,
    team_id: str,
) -> dict[str, Any]:
    weights = soft_weights(team_id)
    w_location = weights[0]

    rng = random.Random(seed)
    campuses = ["Cơ sở 1", "Cơ sở 2"]

    preferences: dict[str, dict[str, Any]] = {}
    cs1_count = 0
    cs2_count = 0

    for staff in sorted(invigilators):
        choice = rng.choice(campuses)
        if choice == "Cơ sở 1":
            cs1_count += 1
            affinity = {"Cơ sở 1": 1, "Cơ sở 2": 0}
        else:
            cs2_count += 1
            affinity = {"Cơ sở 1": 0, "Cơ sở 2": 1}

        preferences[staff] = {
            "preferred_campus": choice,
            "affinity": affinity,
            "disliked_penalty": 1.0,
        }

    return {
        "team_id": team_id,
        "seed": seed,
        "soft_weights": weights,
        "weight_location_preference": w_location,
        "campuses": campuses,
        "num_invigilators": len(invigilators),
        "preferences": preferences,
        "summary": {
            "preferred_CS1_count": cs1_count,
            "preferred_CS2_count": cs2_count,
            "preferred_CS1_percentage": round(cs1_count / len(invigilators) * 100, 2),
            "preferred_CS2_percentage": round(cs2_count / len(invigilators) * 100, 2),
        },
    }


def aggregate_sessions(cleaned_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    sessions: dict[str, dict[str, Any]] = {}

    for r in cleaned_records:
        sid = r["shift_id"]
        if sid not in sessions:
            sessions[sid] = {
                "shift_id": sid,
                "date": r["date"],
                "start_time": r["start_time"],
                "end_time": r["end_time"],
                "duration_minutes": r["duration_minutes"],
                "weekday": r["weekday"],
                "campus": r["campus"],
                "shift_description": r["shift_description"],
                "capacity": 0,
                "assigned_staff": [],
            }
        sessions[sid]["capacity"] += 1
        sessions[sid]["assigned_staff"].append(r["invigilator_id"])

    return sessions


def evaluate_baseline_preferences(
    cleaned_records: list[dict[str, Any]],
    preferences: dict[str, dict[str, Any]],
    weight_location: float,
) -> dict[str, Any]:
    violations = 0
    violation_details: list[dict[str, Any]] = []

    for r in cleaned_records:
        staff = r["invigilator_id"]
        campus = r["campus"]
        staff_pref = preferences.get(staff, {}).get("preferred_campus")
        if staff_pref and staff_pref != campus:
            violations += 1
            violation_details.append({
                "invigilator_id": staff,
                "shift_id": r["shift_id"],
                "shift_campus": campus,
                "preferred_campus": staff_pref,
            })

    total_assignments = len(cleaned_records)
    penalty_score = round(violations * weight_location, 4)

    return {
        "total_baseline_assignments": total_assignments,
        "location_preference_violations": violations,
        "location_preference_satisfactions": total_assignments - violations,
        "satisfaction_rate_percentage": round((total_assignments - violations) / total_assignments * 100, 2),
        "location_penalty_weight": weight_location,
        "total_baseline_location_penalty": penalty_score,
        "violation_samples": violation_details[:10],
    }


def save_cleaned_csv(cleaned_records: list[dict[str, Any]], output_path: str | Path) -> Path:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "shift_description",
        "date",
        "start_time",
        "end_time",
        "duration_minutes",
        "shift_id",
        "task",
        "invigilator_id",
        "weekday",
        "campus",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in cleaned_records:
            writer.writerow(r)

    return path


def save_json(data: Mapping[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return path


def run_pipeline(
    excel_path: str | Path,
    output_dir: str | Path = "data/generated",
    seed: int = 287892112,
    team_id: str = "CO2011-261-CC-2353150",
) -> dict[str, Any]:
    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_records = read_excel_records(excel_path)
    if not raw_records:
        raise ValueError(f"No valid records found in {excel_path}")

    cleaned = clean_records(raw_records)
    sessions = aggregate_sessions(cleaned)

    invigilators_set = sorted(list({r["invigilator_id"] for r in cleaned}))
    sessions_set = sorted(list(sessions.keys()))
    campuses_set = sorted(list({r["campus"] for r in cleaned}))

    pref_payload = generate_simulated_preferences(
        invigilators=invigilators_set,
        seed=seed,
        team_id=team_id,
    )

    baseline_eval = evaluate_baseline_preferences(
        cleaned_records=cleaned,
        preferences=pref_payload["preferences"],
        weight_location=pref_payload["weight_location_preference"],
    )

    full_package = {
        "metadata": {
            "module": "M2",
            "requirement": "2.6",
            "task": "W03-T2",
            "team_id": team_id,
            "seed": seed,
            "soft_weights": pref_payload["soft_weights"],
            "generated_at": datetime.now().isoformat(),
        },
        "sets": {
            "invigilators_I": invigilators_set,
            "invigilators_count": len(invigilators_set),
            "sessions_J": sessions_set,
            "sessions_count": len(sessions_set),
            "campuses_C": campuses_set,
            "campuses_count": len(campuses_set),
        },
        "sessions": sessions,
        "preferences": pref_payload["preferences"],
        "preference_summary": pref_payload["summary"],
        "baseline_evaluation": baseline_eval,
    }

    csv_path = save_cleaned_csv(cleaned, out_dir / "cleaned_dataset.csv")
    pref_path = save_json(pref_payload, out_dir / "simulated_preferences.json")
    pkg_path = save_json(full_package, out_dir / "m2_preprocessed_input.json")

    print("=== W03-T2 PREPROCESSING & PREFERENCES COMPLETE ===")
    print(f"Total cleaned assignment records: {len(cleaned)}")
    print(f"Total unique invigilators |I|: {len(invigilators_set)}")
    print(f"Total unique sessions |J|: {len(sessions_set)}")
    print(f"Total unique campuses |C|: {len(campuses_set)} ({campuses_set})")
    print(f"Preferences generated: {pref_payload['summary']['preferred_CS1_count']} CS1 vs {pref_payload['summary']['preferred_CS2_count']} CS2")
    print(f"Soft weights: {pref_payload['soft_weights']} (Location weight: {pref_payload['weight_location_preference']})")
    print(f"Baseline preference satisfaction: {baseline_eval['satisfaction_rate_percentage']}% ({baseline_eval['location_preference_violations']} violations)")
    print(f"Outputs written to:")
    print(f"  - {csv_path}")
    print(f"  - {pref_path}")
    print(f"  - {pkg_path}")

    return full_package


def main() -> None:
    parser = argparse.ArgumentParser(description="M2 W03-T2: Preprocessing and Simulated Preferences.")
    parser.add_argument(
        "--excel",
        type=Path,
        default=Path("data/Dataset_Anonymized_Invigilator_Assignment_Problem.xlsx"),
        help="Path to raw dataset Excel.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/generated"),
        help="Directory to save generated artifacts.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=287892112,
        help="Deterministic team seed.",
    )
    parser.add_argument(
        "--team-id",
        type=str,
        default="CO2011-261-CC-2353150",
        help="Canonical team ID.",
    )
    args = parser.parse_args()

    run_pipeline(
        excel_path=args.excel,
        output_dir=args.output_dir,
        seed=args.seed,
        team_id=args.team_id,
    )


if __name__ == "__main__":
    main()
