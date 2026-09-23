"""m2_ilp/data_loader.py
Requirement 2.1 — W03-T1: Phân tích schema dữ liệu (Data Schema Analysis)
Author: 2453210 Phan Thế Thông (TV1)

Nhiệm vụ W03-T1:
- Đọc đủ 769 dòng dữ liệu từ dataset Excel.
- Xác định invigilators (I), sessions (J), ngày, giờ, campus (C) và nhiệm vụ.
- Kiểm tra missing values, duplicate và kiểu dữ liệu.
- Xác định và giải mã ý nghĩa cấu trúc của MS Ca thi.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

# Standard console encoding configuration
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ============================================================
# Constant definitions for W03-T1
# ============================================================

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

WEEKDAY_VN = {
    0: "Thứ 2",
    1: "Thứ 3",
    2: "Thứ 4",
    3: "Thứ 5",
    4: "Thứ 6",
    5: "Thứ 7",
    6: "Chủ Nhật",
}


def json_safe(val: Any) -> Any:
    """Helper to ensure all objects are JSON-serializable."""
    if pd.isna(val):
        return None
    if isinstance(val, (pd.Timestamp, pd.Timedelta)):
        return val.isoformat()
    if hasattr(val, "item"):
        try:
            return val.item()
        except Exception:
            pass
    return val


def parse_time_minutes(time_str: Any) -> int | None:
    """Parse Vietnamese time format (e.g., '07g00', '18g15') or 'HH:MM' into minutes from midnight."""
    if pd.isna(time_str):
        return None
    s = str(time_str).strip().lower()
    m_vn = re.match(r"^(\d{1,2})g(\d{2})$", s)
    if m_vn:
        return int(m_vn.group(1)) * 60 + int(m_vn.group(2))
    m_std = re.match(r"^(\d{1,2}):(\d{2})$", s)
    if m_std:
        return int(m_std.group(1)) * 60 + int(m_std.group(2))
    return None


def extract_shift_number(desc: Any) -> int | None:
    """Extract shift number from text like 'Thứ 2, 18/05/2026, Ca 5: 18g15-20g45' -> 5."""
    if pd.isna(desc):
        return None
    m = re.search(r"\bCa\s*(\d+)\b", str(desc), flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


class DataLoader:
    """Loads, validates, and analyzes the Invigilator Assignment Problem (IAP) dataset."""

    def __init__(self, dataset_path: str | Path | None = None) -> None:
        if dataset_path is None:
            # Default dataset path relative to repository root
            base_dir = Path(__file__).resolve().parent.parent
            dataset_path = base_dir / "data" / "Dataset_Anonymized_Invigilator_Assignment_Problem.xlsx"
        self.dataset_path = Path(dataset_path).resolve()
        self._raw_df: pd.DataFrame | None = None

    def load_raw_data(self) -> pd.DataFrame:
        """Reads raw Excel data and validates presence and dimensions."""
        if self._raw_df is not None:
            return self._raw_df

        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {self.dataset_path}")

        excel = pd.ExcelFile(self.dataset_path)
        sheet_name = "Sheet1" if "Sheet1" in excel.sheet_names else excel.sheet_names[0]
        df = pd.read_excel(self.dataset_path, sheet_name=sheet_name)

        if len(df) != EXPECTED_ROWS:
            raise ValueError(
                f"[W03-T1 Error] Expected exactly {EXPECTED_ROWS} data rows, but read {len(df)}."
            )

        self._raw_df = df
        return self._raw_df

    def validate_schema(self, df: pd.DataFrame | None = None) -> dict[str, Any]:
        """Validates column names and row count against the specification."""
        if df is None:
            df = self.load_raw_data()

        actual_cols = [str(c) for c in df.columns]
        missing_cols = [c for c in EXPECTED_COLUMNS if c not in actual_cols]
        unexpected_cols = [c for c in actual_cols if c not in EXPECTED_COLUMNS]

        return {
            "row_count": int(len(df)),
            "expected_row_count": EXPECTED_ROWS,
            "row_count_valid": bool(len(df) == EXPECTED_ROWS),
            "col_count": int(len(df.columns)),
            "expected_col_count": EXPECTED_COLS,
            "col_count_valid": bool(len(df.columns) == EXPECTED_COLS),
            "actual_columns": actual_cols,
            "missing_columns": missing_cols,
            "unexpected_columns": unexpected_cols,
            "schema_valid": (
                len(df) == EXPECTED_ROWS
                and len(df.columns) == EXPECTED_COLS
                and not missing_cols
            ),
        }

    def check_data_quality(self, df: pd.DataFrame | None = None) -> dict[str, Any]:
        """Checks missing values, duplicates, and column data types."""
        if df is None:
            df = self.load_raw_data()

        missing_by_col = {str(k): int(v) for k, v in df.isna().sum().items()}
        total_missing = int(df.isna().sum().sum())

        full_duplicate_rows = int(df.duplicated().sum())

        # Check uniqueness of assignment pairs (invigilator i, session j)
        pair_dups_count = int(
            df.duplicated(subset=[COL_INVIGILATOR, COL_SHIFT_ID]).sum()
        )

        dtypes_info = {str(c): str(df[c].dtype) for c in df.columns}
        unique_counts = {str(c): int(df[c].nunique(dropna=True)) for c in df.columns}

        return {
            "missing_values_by_column": missing_by_col,
            "total_missing_cells": total_missing,
            "duplicate_full_rows": full_duplicate_rows,
            "duplicate_assignment_pairs": pair_dups_count,
            "dtypes": dtypes_info,
            "unique_counts": unique_counts,
        }

    def extract_sets(self, df: pd.DataFrame | None = None) -> dict[str, Any]:
        """Identifies and extracts core mathematical sets I, J, C, dates, times, and tasks."""
        if df is None:
            df = self.load_raw_data()

        invigilators_I = sorted(df[COL_INVIGILATOR].dropna().astype(str).unique().tolist())
        sessions_J = sorted(df[COL_SHIFT_ID].dropna().astype(str).unique().tolist())
        campuses_C = sorted(df[COL_CAMPUS].dropna().astype(str).unique().tolist())

        dates = sorted(
            pd.to_datetime(df[COL_DATE], errors="coerce")
            .dropna()
            .dt.strftime("%Y-%m-%d")
            .unique()
            .tolist()
        )

        start_times = sorted(df[COL_START_TIME].dropna().astype(str).unique().tolist())
        tasks = sorted(df[COL_TASK].dropna().astype(str).unique().tolist())

        return {
            "invigilators_I": invigilators_I,
            "count_I": len(invigilators_I),
            "sessions_J": sessions_J,
            "count_J": len(sessions_J),
            "campuses_C": campuses_C,
            "count_C": len(campuses_C),
            "dates": dates,
            "count_dates": len(dates),
            "start_times": start_times,
            "count_start_times": len(start_times),
            "tasks": tasks,
            "count_tasks": len(tasks),
        }

    def analyze_shift_code_meaning(self, df: pd.DataFrame | None = None) -> dict[str, Any]:
        """Determines and formally verifies the structure and semantic meaning of MS Ca thi."""
        if df is None:
            df = self.load_raw_data()

        session_records: list[dict[str, Any]] = []
        matching_date_count = 0
        matching_shift_count = 0
        multi_campus_count = 0

        for session_id, grp in df.groupby(COL_SHIFT_ID):
            s_id = str(session_id).strip()

            # Pattern: YYYYMMDD_K
            match = re.fullmatch(r"^(\d{8})_(\d+)$", s_id)
            code_date_str = match.group(1) if match else None
            code_shift_num = int(match.group(2)) if match else None

            # Actual date and shift info in group
            actual_dates = pd.to_datetime(grp[COL_DATE]).dt.strftime("%Y%m%d").unique()
            date_matches = bool(code_date_str and len(actual_dates) == 1 and code_date_str == actual_dates[0])
            if date_matches:
                matching_date_count += 1

            shift_descs = grp[COL_SHIFT_DESC].dropna().unique()
            extracted_shift_nums = {extract_shift_number(d) for d in shift_descs if extract_shift_number(d) is not None}
            shift_matches = bool(code_shift_num and code_shift_num in extracted_shift_nums)
            if shift_matches:
                matching_shift_count += 1

            campuses = sorted(grp[COL_CAMPUS].dropna().unique().tolist())
            if len(campuses) > 1:
                multi_campus_count += 1

            start_time = grp[COL_START_TIME].dropna().iloc[0] if not grp[COL_START_TIME].dropna().empty else None
            duration = grp[COL_DURATION].dropna().iloc[0] if not grp[COL_DURATION].dropna().empty else None
            staff_count = len(grp)

            session_records.append({
                "session_id": s_id,
                "code_date": code_date_str,
                "code_shift": code_shift_num,
                "date_matches": date_matches,
                "shift_matches": shift_matches,
                "start_time": str(start_time),
                "duration": int(duration) if duration is not None else None,
                "assigned_invigilators": staff_count,
                "campuses": campuses,
                "is_multi_campus": len(campuses) > 1,
            })

        total_sessions = len(session_records)

        return {
            "total_unique_sessions": total_sessions,
            "format_pattern": "YYYYMMDD_K (e.g. 20260518_5)",
            "date_part_matches_ngay": f"{matching_date_count}/{total_sessions}",
            "shift_number_matches_ca_thi": f"{matching_shift_count}/{total_sessions}",
            "multi_campus_sessions_count": multi_campus_count,
            "all_syntactically_valid": bool(matching_date_count == total_sessions and matching_shift_count == total_sessions),
            "meaning_summary": (
                "MS Ca thi là mã định danh duy nhất của một ca thi (time slot) trong toàn trường, "
                "được cấu tạo bởi 8 chữ số ngày thi (YYYYMMDD) nối với số thứ tự ca thi trong ngày (_K). "
                "Tại một MS Ca thi, trường tổ chức thi cho nhiều phòng đồng thời và có thể diễn ra "
                "ở cả hai cơ sở (Cơ sở 1 và Cơ sở 2)."
            ),
            "sessions_detail": session_records,
        }

    def get_imputed_data(self, df: pd.DataFrame | None = None) -> pd.DataFrame:
        """Returns a copy of the dataset with the 28 missing 'Thứ' and 'Cơ sở' values reconstructed."""
        if df is None:
            df = self.load_raw_data()

        clean_df = df.copy()

        # 1. Impute missing Cơ sở based on Nhiệm vụ prefix
        ltk_mask = clean_df[COL_CAMPUS].isna() & clean_df[COL_TASK].str.startswith("LTK_")
        clean_df.loc[ltk_mask, COL_CAMPUS] = "Cơ sở 1"

        dian_mask = clean_df[COL_CAMPUS].isna() & clean_df[COL_TASK].str.startswith("DiAn_")
        clean_df.loc[dian_mask, COL_CAMPUS] = "Cơ sở 2"

        # 2. Impute missing Thứ based on Ngày
        missing_weekday = clean_df[COL_WEEKDAY].isna()
        if missing_weekday.any():
            clean_df.loc[missing_weekday, COL_WEEKDAY] = clean_df.loc[missing_weekday, COL_DATE].dt.weekday.map(
                WEEKDAY_VN
            )

        return clean_df

    def run_full_analysis(self, output_dir: str | Path | None = None) -> dict[str, Any]:
        """Executes complete W03-T1 analysis and exports summary reports."""
        df = self.load_raw_data()
        schema_res = self.validate_schema(df)
        quality_res = self.check_data_quality(df)
        sets_res = self.extract_sets(df)
        shift_meaning_res = self.analyze_shift_code_meaning(df)

        report = {
            "task": "W03-T1 — Phân tích schema dữ liệu",
            "owner": "TV1 (2453210 Phan Thế Thông)",
            "schema_validation": schema_res,
            "data_quality": quality_res,
            "extracted_sets": sets_res,
            "shift_code_analysis": {
                "format_pattern": shift_meaning_res["format_pattern"],
                "total_unique_sessions": shift_meaning_res["total_unique_sessions"],
                "date_part_matches_ngay": shift_meaning_res["date_part_matches_ngay"],
                "shift_number_matches_ca_thi": shift_meaning_res["shift_number_matches_ca_thi"],
                "multi_campus_sessions_count": shift_meaning_res["multi_campus_sessions_count"],
                "all_syntactically_valid": shift_meaning_res["all_syntactically_valid"],
                "meaning_summary": shift_meaning_res["meaning_summary"],
            },
        }

        if output_dir:
            out_p = Path(output_dir).resolve()
            out_p.mkdir(parents=True, exist_ok=True)

            # Export JSON summary
            summary_path = out_p / "w03_t1_schema_summary.json"
            with summary_path.open("w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=json_safe)

            # Export detailed session table CSV
            sessions_df = pd.DataFrame(shift_meaning_res["sessions_detail"])
            sessions_df.to_csv(out_p / "sessions_extracted.csv", index=False, encoding="utf-8-sig")

            # Export clean/imputed dataset
            clean_df = self.get_imputed_data(df)
            clean_df.to_csv(out_p / "dataset_cleaned_imputed.csv", index=False, encoding="utf-8-sig")

        return report


def main() -> int:
    parser = argparse.ArgumentParser(description="W03-T1: Phân tích schema dữ liệu (IAP Dataset Loader)")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/Dataset_Anonymized_Invigilator_Assignment_Problem.xlsx"),
        help="Path to the Excel dataset",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/generated"),
        help="Output directory for generated reports",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output",
    )
    args = parser.parse_args()

    loader = DataLoader(args.dataset)
    results = loader.run_full_analysis(output_dir=args.output_dir)

    if not args.quiet:
        sq = results["schema_validation"]
        dq = results["data_quality"]
        st = results["extracted_sets"]
        sc = results["shift_code_analysis"]

        print("=" * 65)
        print("   W03-T1: PHÂN TÍCH SCHEMA DỮ LIỆU (DATA LOADER)")
        print("   Thành viên: TV1 (2453210 Phan Thế Thông)")
        print("=" * 65)
        print(f"1. Số dòng đọc được: {sq['row_count']} / {sq['expected_row_count']} (Khớp: {sq['row_count_valid']})")
        print(f"2. Số cột đọc được: {sq['col_count']} / {sq['expected_col_count']} (Khớp: {sq['col_count_valid']})")
        print("\n3. Các tập hợp cơ bản đã xác định:")
        print(f"   - Giám thị |I|      : {st['count_I']} cán bộ (CB001 -> CB073)")
        print(f"   - Ca thi |J|        : {st['count_J']} ca thi (MS Ca thi)")
        print(f"   - Cơ sở |C|         : {st['count_C']} cơ sở ({', '.join(st['campuses_C'])})")
        print(f"   - Ngày thi          : {st['count_dates']} ngày")
        print(f"   - Giờ thi (bắt đầu) : {st['count_start_times']} khung giờ ({', '.join(st['start_times'])})")
        print(f"   - Nhiệm vụ          : {st['count_tasks']} nhiệm vụ ({', '.join(st['tasks'])})")
        print("\n4. Kiểm tra chất lượng dữ liệu:")
        print(f"   - Tổng số ô missing : {dq['total_missing_cells']} (Thứ: 28, Cơ sở: 28; các cột khác: 0)")
        print(f"   - Số dòng trùng lặp : {dq['duplicate_full_rows']}")
        print(f"   - Trùng phân công   : {dq['duplicate_assignment_pairs']}")
        print("\n5. Phân tích ý nghĩa MS Ca thi:")
        print(f"   - Định dạng chuẩn   : {sc['format_pattern']}")
        print(f"   - Khớp cột Ngày     : {sc['date_part_matches_ngay']} ca thi")
        print(f"   - Khớp cột Ca thi   : {sc['shift_number_matches_ca_thi']} ca thi")
        print(f"   - Ca thi đa cơ sở   : {sc['multi_campus_sessions_count']} ca đồng thời tại CS1 và CS2")
        print(f"   - Đánh giá cú pháp  : {'HỢP LỆ HOÀN TOÀN (100%)' if sc['all_syntactically_valid'] else 'CÓ LỖI'}")
        print("-" * 65)
        print(f"[XUẤT KẾT QUẢ] Đã ghi báo cáo vào thư mục: {args.output_dir.resolve()}")
        print("=" * 65)

    return 0


if __name__ == "__main__":
    sys.exit(main())
