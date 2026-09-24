from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

EXPECTED_ROWS = 769         
EXPECTED_COLS = 9

COL_SHIFT_DESC = "Ca thi"
COL_DATE = "Ngày"
COL_START_TIME = "GIỜ"
COL_SHIFT_ID = "MS Ca thi"
COL_TASK = "Nhiệm vụ"
COL_INVIGILATOR = "MS của CÁN BỘ COI THI"
COL_DURATION = "Thời gian"
COL_WEEKDAY = "Thứ"
COL_CAMPUS = "Cơ sở"

EXPECTED_COLUMNS = [
    COL_SHIFT_DESC,
    COL_DATE,
    COL_START_TIME,
    COL_SHIFT_ID,
    COL_TASK,
    COL_INVIGILATOR,
    COL_DURATION,
    COL_WEEKDAY,
    COL_CAMPUS,
]

ROOT = Path(__file__).resolve().parent
if (ROOT / "m1_logic").exists():
    sys.path.insert(0, str(ROOT))

LogicToLPBridge = None
BRIDGE_IMPORT_ERROR = None

try:
    from m1_logic.logic_to_lp import LogicToLPBridge  
except ImportError as exc:
    BRIDGE_IMPORT_ERROR = str(exc)
    try:
        from logic_to_lp import LogicToLPBridge  
    except ImportError as exc2:
        BRIDGE_IMPORT_ERROR = f"m1_logic.logic_to_lp: {exc}; logic_to_lp: {exc2}"

def json_safe(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def first_non_null(series: pd.Series) -> Any:
    non_null = series.dropna()
    return non_null.iloc[0] if not non_null.empty else None


def parse_start_time(value: Any):
    if pd.isna(value):
        return None

    text = str(value).strip()

    match = re.fullmatch(r"(\d{1,2})g(\d{2})", text, flags=re.IGNORECASE)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return pd.Timestamp(f"2000-01-01 {hour:02d}:{minute:02d}").time()

    match = re.fullmatch(r"(\d{1,2}):(\d{2})", text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return pd.Timestamp(f"2000-01-01 {hour:02d}:{minute:02d}").time()

    return None


def extract_shift_number(text: Any) -> int | None:
    if pd.isna(text):
        return None
    match = re.search(r"\bCa\s*(\d+)\b", str(text), flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def parse_shift_code(code: Any) -> tuple[str | None, int | None]:
    if pd.isna(code):
        return None, None

    match = re.fullmatch(r"(\d{8})_(\d+)", str(code).strip())
    if not match:
        return None, None

    return match.group(1), int(match.group(2))


def series_unique_non_null(series: pd.Series) -> int:
    return int(series.dropna().nunique())

def read_dataset(file_path: str) -> pd.DataFrame:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    excel = pd.ExcelFile(path)
    sheet_name = "Input" if "Input" in excel.sheet_names else excel.sheet_names[0]
    return pd.read_excel(path, sheet_name=sheet_name)


def validate_schema(df: pd.DataFrame) -> dict[str, Any]:
    actual_columns = [str(c) for c in df.columns]
    missing_required = [c for c in EXPECTED_COLUMNS if c not in actual_columns]
    unexpected_columns = [c for c in actual_columns if c not in EXPECTED_COLUMNS]

    return {
        "row_count": int(len(df)),
        "expected_row_count": EXPECTED_ROWS,
        "row_count_matches": bool(len(df) == EXPECTED_ROWS),
        "column_count": int(len(df.columns)),
        "expected_column_count": EXPECTED_COLS,
        "column_count_matches": bool(len(df.columns) == EXPECTED_COLS),
        "actual_columns": actual_columns,
        "required_columns_missing": missing_required,
        "unexpected_columns": unexpected_columns,
        "schema_valid": (
            len(df) == EXPECTED_ROWS
            and len(df.columns) == EXPECTED_COLS
            and not missing_required
        ),
    }


def data_quality_report(df: pd.DataFrame) -> dict[str, Any]:
    missing = df.isna().sum()
    duplicate_full_rows = int(df.duplicated().sum())

    type_info = {str(c): str(df[c].dtype) for c in df.columns}
    unique_counts = {
        str(c): int(df[c].nunique(dropna=True)) for c in df.columns
    }

    duplicate_assignment_extra_rows = int(
        df.duplicated(
            subset=[COL_INVIGILATOR, COL_SHIFT_ID],
            keep="first",
        ).sum()
    )

    duplicate_assignment_pair_count = int(
        df.loc[
            df.duplicated(
                subset=[COL_INVIGILATOR, COL_SHIFT_ID],
                keep=False,
            ),
            [COL_INVIGILATOR, COL_SHIFT_ID],
        ].drop_duplicates().shape[0]
    )

    return {
        "missing_values_by_column": {str(k): int(v) for k, v in missing.items()},
        "total_missing_cells": int(missing.sum()),
        "duplicate_full_rows": duplicate_full_rows,
        "duplicate_assignment_extra_rows": duplicate_assignment_extra_rows,
        "duplicate_assignment_pair_count": duplicate_assignment_pair_count,
        "dtypes": type_info,
        "unique_values_by_column": unique_counts,
    }

def extract_sets(df: pd.DataFrame) -> dict[str, list[Any]]:
    return {
        "invigilators_I": sorted(
            df[COL_INVIGILATOR].dropna().astype(str).unique().tolist()
        ),
        "sessions_J": sorted(
            df[COL_SHIFT_ID].dropna().astype(str).unique().tolist()
        ),
        "campuses_C": sorted(
            df[COL_CAMPUS].dropna().astype(str).unique().tolist()
        ),
        "dates": sorted(
            pd.to_datetime(df[COL_DATE], errors="coerce")
            .dropna()
            .dt.strftime("%Y-%m-%d")
            .unique()
            .tolist()
        ),
        "start_times": sorted(
            df[COL_START_TIME].dropna().astype(str).unique().tolist()
        ),
        "tasks": sorted(
            df[COL_TASK].dropna().astype(str).unique().tolist()
        ),
    }

def build_assignment_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    A row is an observed baseline assignment record, not an ILP variable by itself.

    The pair:
        invigilator = i
        MS Ca thi   = j
    represents the observed relation Assign(i,j) = 1 in the baseline.
    """
    assignments = (
        df[[COL_INVIGILATOR, COL_SHIFT_ID]]
        .dropna()
        .drop_duplicates()
        .rename(
            columns={
                COL_INVIGILATOR: "invigilator_id",
                COL_SHIFT_ID: "session_id",
            }
        )
    )

    return assignments.sort_values(
        ["session_id", "invigilator_id"]
    ).reset_index(drop=True)

def build_session_table(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for session_id, group in df.groupby(COL_SHIFT_ID, dropna=False):
        if pd.isna(session_id):
            continue

        date_value = first_non_null(group[COL_DATE])
        start_text = first_non_null(group[COL_START_TIME])
        duration_value = first_non_null(group[COL_DURATION])
        desc_value = first_non_null(group[COL_SHIFT_DESC])

        date_series = pd.to_datetime(group[COL_DATE], errors="coerce").dropna()
        start_series = group[COL_START_TIME].dropna().astype(str)
        duration_series = pd.to_numeric(group[COL_DURATION], errors="coerce").dropna()
        desc_shift_numbers = {
            x for x in group[COL_SHIFT_DESC].dropna().map(extract_shift_number)
            if x is not None
        }

        start_date = pd.to_datetime(date_value, errors="coerce") if date_value is not None else pd.NaT
        start_time = parse_start_time(start_text)
        duration = pd.to_numeric(
            pd.Series([duration_value]), errors="coerce"
        ).iloc[0]

        start_dt = pd.NaT
        end_dt = pd.NaT
        if not pd.isna(start_date) and start_time is not None:
            start_dt = pd.Timestamp.combine(start_date.date(), start_time)
            if not pd.isna(duration):
                end_dt = start_dt + pd.to_timedelta(float(duration), unit="m")

        campuses = sorted(group[COL_CAMPUS].dropna().astype(str).unique().tolist())
        tasks = sorted(group[COL_TASK].dropna().astype(str).unique().tolist())
        invigilators = sorted(group[COL_INVIGILATOR].dropna().astype(str).unique().tolist())

        code_date, code_shift = parse_shift_code(session_id)
        actual_date = start_date.strftime("%Y%m%d") if not pd.isna(start_date) else None

        date_consistent = len(date_series.dt.strftime("%Y-%m-%d").unique()) <= 1
        time_consistent = len(start_series.unique()) <= 1
        duration_consistent = len(duration_series.unique()) <= 1
        description_shift_consistent = len(desc_shift_numbers) <= 1

        rows.append(
            {
                "session_id": str(session_id),
                "shift_description": None if pd.isna(desc_value) else str(desc_value),
                "date": start_date.strftime("%Y-%m-%d") if not pd.isna(start_date) else None,
                "start_time": None if start_time is None else start_time.strftime("%H:%M"),
                "duration_minutes": None if pd.isna(duration) else float(duration),
                "end_time": None if pd.isna(end_dt) else end_dt.strftime("%H:%M"),
                "start_datetime": None if pd.isna(start_dt) else start_dt.isoformat(),
                "end_datetime": None if pd.isna(end_dt) else end_dt.isoformat(),
                "campuses": "; ".join(campuses),
                "campus_count": len(campuses),
                "tasks": "; ".join(tasks),
                "task_count": len(tasks),
                "baseline_invigilator_count": len(invigilators),
                "code_date_part": code_date,
                "code_shift_number": code_shift,
                "description_shift_numbers": "; ".join(map(str, sorted(desc_shift_numbers))),
                "code_date_matches_dataset_date": bool(
                    code_date is not None
                    and actual_date is not None
                    and code_date == actual_date
                ),
                "code_shift_matches_description": bool(
                    code_shift is not None
                    and bool(desc_shift_numbers)
                    and code_shift in desc_shift_numbers
                ),
                "date_consistent_within_session": date_consistent,
                "start_time_consistent_within_session": time_consistent,
                "duration_consistent_within_session": duration_consistent,
                "description_shift_consistent_within_session": description_shift_consistent,
            }
        )

    return pd.DataFrame(rows).sort_values("session_id").reset_index(drop=True)

def find_overlapping_sessions(session_df: pd.DataFrame) -> pd.DataFrame:
    """Find unordered session pairs whose intervals overlap."""
    records: list[dict[str, Any]] = []
    valid = session_df.dropna(
        subset=["start_datetime", "end_datetime"]
    ).copy()
    valid = valid.sort_values("start_datetime").reset_index(drop=True)

    for i in range(len(valid)):
        a = valid.iloc[i]
        a_start = pd.Timestamp(a["start_datetime"])
        a_end = pd.Timestamp(a["end_datetime"])

        for j in range(i + 1, len(valid)):
            b = valid.iloc[j]
            b_start = pd.Timestamp(b["start_datetime"])
            b_end = pd.Timestamp(b["end_datetime"])

            # Half-open intervals: [start, end)
            if b_start >= a_end:
                break

            if max(a_start, b_start) < min(a_end, b_end):
                records.append(
                    {
                        "session_j": a["session_id"],
                        "session_k": b["session_id"],
                        "j_start": a["start_datetime"],
                        "j_end": a["end_datetime"],
                        "k_start": b["start_datetime"],
                        "k_end": b["end_datetime"],
                    }
                )

    return pd.DataFrame(records)

def generate_logic_to_lp_outputs(
    invigilators: list[str],
    overlaps: pd.DataFrame,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "bridge_available": LogicToLPBridge is not None,
        "bridge_import_error": BRIDGE_IMPORT_ERROR,
        "no_double_booking_constraint_count": 0,
        "no_double_booking_constraints": [],
        "availability_status": (
            "not generated: no explicit Busy(i,j)/availability field in dataset"
        ),
        "capacity_status": (
            "not generated: no explicit required-capacity field in dataset"
        ),
        "at_most_k_status": (
            "not generated: max-load k is not a dataset field"
        ),
    }

    if LogicToLPBridge is None or overlaps.empty:
        return result

    bridge = LogicToLPBridge()
    constraints: list[str] = []

    for _, row in overlaps.iterrows():
        for invigilator_id in invigilators:
            constraints.append(
                bridge.no_double_booking_to_lp(
                    invigilator_id,
                    str(row["session_j"]),
                    str(row["session_k"]),
                )
            )

    result["no_double_booking_constraint_count"] = len(constraints)
    result["no_double_booking_constraints"] = constraints
    return result

def write_markdown_report(
    output_path: Path,
    schema: dict[str, Any],
    quality: dict[str, Any],
    sets: dict[str, list[Any]],
    assignment_df: pd.DataFrame,
    session_df: pd.DataFrame,
    overlaps: pd.DataFrame,
    lp_info: dict[str, Any],
) -> None:
    code_date_match = int(
        session_df["code_date_matches_dataset_date"].sum()
    ) if not session_df.empty else 0
    code_shift_match = int(
        session_df["code_shift_matches_description"].sum()
    ) if not session_df.empty else 0

    date_consistency_ok = int(
        session_df["date_consistent_within_session"].sum()
    ) if not session_df.empty else 0
    time_consistency_ok = int(
        session_df["start_time_consistent_within_session"].sum()
    ) if not session_df.empty else 0
    duration_consistency_ok = int(
        session_df["duration_consistent_within_session"].sum()
    ) if not session_df.empty else 0

    multi_campus_sessions = int(
        (session_df["campus_count"] > 1).sum()
    ) if not session_df.empty else 0

    lines = [
        "# W03-T1 Schema Analysis Report",
        "",
        "## 1. Task coverage",
        "",
        "| W03-T1 task | Implemented? | Output |",
        "|---|---|---|",
        f"| Read all 769 data rows | **{schema['row_count_matches']}** | Row-count validation |",
        "| Identify invigilators, sessions, dates, times, campus and tasks | **Yes** | Sets + session table |",
        "| Check missing values, duplicates and data types | **Yes** | Data-quality report |",
        "| Determine the meaning of a shift code | **Yes** | `MS Ca thi` parsing + consistency checks |",
        "",
        "## 2. Dataset size and columns",
        "",
        f"- Data rows read: **{schema['row_count']}** (expected {EXPECTED_ROWS})",
        f"- Columns read: **{schema['column_count']}** (expected {EXPECTED_COLS})",
        f"- Schema valid: **{schema['schema_valid']}**",
        "",
        "| Column | Meaning |",
        "|---|---|",
        f"| `{COL_SHIFT_DESC}` | Human-readable shift description |",
        f"| `{COL_DATE}` | Exam date |",
        f"| `{COL_START_TIME}` | Start time |",
        f"| `{COL_SHIFT_ID}` | Session/shift identifier `j` |",
        f"| `{COL_TASK}` | Assignment task/role |",
        f"| `{COL_INVIGILATOR}` | Invigilator identifier `i` |",
        f"| `{COL_DURATION}` | Duration in minutes |",
        f"| `{COL_WEEKDAY}` | Weekday label |",
        f"| `{COL_CAMPUS}` | Campus recorded on the assignment row |",
        "",
        "## 3. Extracted sets",
        "",
        f"- `I` invigilators: **{len(sets['invigilators_I'])}**",
        f"- `J` sessions (`MS Ca thi`): **{len(sets['sessions_J'])}**",
        f"- `C` non-missing campuses: **{len(sets['campuses_C'])}**",
        f"- Distinct dates: **{len(sets['dates'])}**",
        f"- Distinct start times: **{len(sets['start_times'])}**",
        f"- Distinct tasks: **{len(sets['tasks'])}**",
        "",
        "## 4. Assignment relation",
        "",
        "Each data row records an observed baseline assignment. The ILP variable `x_ij` is not a raw column. It is indexed by an invigilator `i` from `I` and a session `j` from `J`.",
        "",
        f"- Unique observed `(invigilator, session)` pairs: **{len(assignment_df)}**",
        "",
        "## 5. Data quality",
        "",
        f"- Total missing cells: **{quality['total_missing_cells']}**",
        f"- Full duplicate rows: **{quality['duplicate_full_rows']}**",
        f"- Extra rows repeating an existing `(invigilator, session)` pair: **{quality['duplicate_assignment_extra_rows']}**",
        f"- Distinct duplicated `(invigilator, session)` pairs: **{quality['duplicate_assignment_pair_count']}**",
        "",
        "### Missing values",
        "",
        "| Column | Missing values |",
        "|---|---:|",
    ]

    for column, count in quality["missing_values_by_column"].items():
        lines.append(f"| `{column}` | {count} |")

    lines += [
        "",
        "### Data types",
        "",
        "| Column | pandas dtype |",
        "|---|---|",
    ]

    for column, dtype in quality["dtypes"].items():
        lines.append(f"| `{column}` | `{dtype}` |")

    lines += [
        "",
        "## 6. Meaning of `MS Ca thi`",
        "",
        "The code tests the observed pattern `YYYYMMDD_shiftNumber`. For example, `20260518_5` is parsed as date part `20260518` and shift number `5`.",
        "",
        f"- Codes whose encoded date matches `Ngày`: **{code_date_match}/{len(session_df)}** sessions",
        f"- Codes whose shift number appears in the `Ca N` description: **{code_shift_match}/{len(session_df)}** sessions",
        f"- Sessions with internally consistent dates: **{date_consistency_ok}/{len(session_df)}**",
        f"- Sessions with internally consistent start times: **{time_consistency_ok}/{len(session_df)}**",
        f"- Sessions with internally consistent durations: **{duration_consistency_ok}/{len(session_df)}**",
        "",
        "Therefore the code does not merely infer the meaning from the column name. It checks the structure of the code against the date and shift information already present in the dataset.",
        "",
        "## 7. Time interval and overlap",
        "",
        "`End Time` is a derived value, not a raw dataset column:",
        "",
        "`End Time = GIỜ + Thời gian (minutes)`",
        "",
        "The derived start/end interval is used to calculate `Overlap(j,k)`. This relation is then translated through Requirement 1.3 into the no-double-booking inequality.",
        "",
        f"- Detected overlapping session pairs: **{len(overlaps)}**",
        f"- Sessions recorded with more than one campus: **{multi_campus_sessions}**",
        "",
        "## 8. Requirement 1.3 bridge",
        "",
        "For every real-data overlap pair `(j,k)` and every invigilator `i`, the bridge generates:",
        "",
        "`x_i_j + x_i_k <= 1`",
        "",
        f"- Generated no-double-booking constraints: **{lp_info['no_double_booking_constraint_count']}**",
        f"- Availability constraint status: {lp_info['availability_status']}",
        f"- Exact-capacity status: {lp_info['capacity_status']}",
        f"- At-most-k status: {lp_info['at_most_k_status']}",
        "",
        "The script intentionally does not invent Busy(i,j), required capacity r(j), or a maximum-load k when the raw dataset does not contain such fields.",
        "",
        "## 9. Files generated",
        "",
        "- `schema_summary.json`",
        "- `session_schema.csv`",
        "- `assignment_pairs.csv`",
        "- `overlap_pairs.csv`",
        "- `logic_bridge_no_double_booking.txt`",
        "- `W03_T1_schema_report.md`",
    ]

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def analyze_dataset(
    file_path: str,
    output_dir: str = "data/generated",
) -> dict[str, Any]:
    df = read_dataset(file_path)

    schema = validate_schema(df)
    if schema["required_columns_missing"]:
        raise ValueError(
            "Required columns are missing: "
            + ", ".join(schema["required_columns_missing"])
        )

    if len(df) != EXPECTED_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_ROWS} data rows, but read {len(df)}. "
            "Check the workbook/sheet before continuing."
        )

    quality = data_quality_report(df)
    sets = extract_sets(df)
    assignment_df = build_assignment_table(df)
    session_df = build_session_table(df)
    overlaps = find_overlapping_sessions(session_df)

    lp_info = generate_logic_to_lp_outputs(
        sets["invigilators_I"],
        overlaps,
    )

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    summary = {
        "task_coverage": {
            "read_769_rows": True,
            "identify_invigilators": True,
            "identify_sessions": True,
            "identify_dates": True,
            "identify_times": True,
            "identify_campuses": True,
            "identify_tasks": True,
            "check_missing_values": True,
            "check_duplicates": True,
            "check_dtypes": True,
            "determine_shift_code_meaning": True,
        },
        "schema": schema,
        "quality": quality,
        "sets": {
            "I_count": len(sets["invigilators_I"]),
            "J_count": len(sets["sessions_J"]),
            "C_count": len(sets["campuses_C"]),
            "date_count": len(sets["dates"]),
            "start_time_count": len(sets["start_times"]),
            "task_count": len(sets["tasks"]),
            "I_values": sets["invigilators_I"],
            "J_values": sets["sessions_J"],
            "C_values": sets["campuses_C"],
            "date_values": sets["dates"],
            "start_time_values": sets["start_times"],
            "task_values": sets["tasks"],
        },
        "assignment_pair_count": len(assignment_df),
        "overlap_pair_count": len(overlaps),
        "logic_to_lp": {
            "bridge_available": lp_info["bridge_available"],
            "bridge_import_error": lp_info["bridge_import_error"],
            "no_double_booking_constraint_count": lp_info[
                "no_double_booking_constraint_count"
            ],
            "availability_status": lp_info["availability_status"],
            "capacity_status": lp_info["capacity_status"],
            "at_most_k_status": lp_info["at_most_k_status"],
        },
    }

    with (out / "schema_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=json_safe)

    assignment_df.to_csv(
        out / "assignment_pairs.csv",
        index=False,
        encoding="utf-8-sig",
    )
    session_df.to_csv(
        out / "session_schema.csv",
        index=False,
        encoding="utf-8-sig",
    )
    overlaps.to_csv(
        out / "overlap_pairs.csv",
        index=False,
        encoding="utf-8-sig",
    )

    with (out / "logic_bridge_no_double_booking.txt").open(
        "w", encoding="utf-8"
    ) as f:
        f.write("# Requirement 1.3: No-double-booking LP constraints\n")
        f.write(
            f"Count: {lp_info['no_double_booking_constraint_count']}\n\n"
        )
        for constraint in lp_info["no_double_booking_constraints"]:
            f.write(constraint + "\n")

    write_markdown_report(
        out / "W03_T1_schema_report.md",
        schema,
        quality,
        sets,
        assignment_df,
        session_df,
        overlaps,
        lp_info,
    )

    print("=== W03-T1 SCHEMA ANALYSIS ===")
    print(f"Rows: {len(df)} / expected {EXPECTED_ROWS}")
    print(f"Columns: {len(df.columns)} / expected {EXPECTED_COLS}")
    print(f"Invigilators |I|: {len(sets['invigilators_I'])}")
    print(f"Sessions |J|: {len(sets['sessions_J'])}")
    print(f"Campuses |C|: {len(sets['campuses_C'])}")
    print(f"Dates: {len(sets['dates'])}")
    print(f"Start times: {len(sets['start_times'])}")
    print(f"Tasks: {len(sets['tasks'])}")
    print(f"Unique baseline assignments (i,j): {len(assignment_df)}")
    print(f"Missing cells: {quality['total_missing_cells']}")
    print(f"Full duplicate rows: {quality['duplicate_full_rows']}")
    print(f"Repeated assignment extra rows: {quality['duplicate_assignment_extra_rows']}")
    print(f"Overlapping session pairs: {len(overlaps)}")
    print(
        "Req 1.3 no-double-booking constraints: "
        f"{lp_info['no_double_booking_constraint_count']}"
    )
    print(f"Output directory: {out.resolve()}")

    return summary


if __name__ == "__main__":
    default_path = "data/Dataset_Anonymized_Invigilator_Assignment_Problem.xlsx"
    input_path = sys.argv[1] if len(sys.argv) >= 2 else default_path
    analyze_dataset(input_path)
