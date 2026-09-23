# Module 2 — Linear & Integer Programming (ILP)

Module 2 constructs, solves, and evaluates the 0/1 Integer Linear Programming (ILP) model for the Invigilator Assignment Problem (IAP) on real Faculty exam data.

## W03-T1 — Phân Tích Schema Dữ Liệu (Data Schema Analysis)

**Requirement:** 2.1  
**Primary owner:** TV1 — 2453210 Phan Thế Thông  

### Purpose

W03-T1 inspects and validates the raw anonymized dataset (`data/Dataset_Anonymized_Invigilator_Assignment_Problem.xlsx`), establishing ground-truth parameters, mathematical sets, and baseline characteristics for Module 2.

Key deliverables:
- `m2_ilp/data_loader.py`: Reusable data loader and schema validator.
- `m2_ilp/data_schema.md`: Comprehensive technical report on dataset schema, quality, and semantic mapping.
- `data/generated/w03_t1_schema_summary.json`: Serialized summary metrics.
- `data/generated/sessions_extracted.csv`: 65 extracted session records.
- `data/generated/dataset_cleaned_imputed.csv`: Preprocessed dataset with reconstructed missing values.

### Execution

Run the data loader and schema analyzer directly from the repository root:

```bash
python m2_ilp/data_loader.py
```

Optional arguments:
- `--dataset <path>`: Specify path to Excel dataset (defaults to `data/Dataset_Anonymized_Invigilator_Assignment_Problem.xlsx`).
- `--output-dir <path>`: Specify output folder for generated summaries (defaults to `data/generated`).
- `--quiet`: Run without console output.

### Summary of Dataset Dimensions & Extracted Sets

| Attribute | Verified Value | Description |
|---|:---:|---|
| Total Data Rows | **769** | Observed invigilator-session baseline assignments |
| Total Columns | **9** | Documented schema fields |
| Invigilators ($I$) | **73** | Cán bộ coi thi (`CB001` - `CB073`) |
| Sessions ($J$) | **65** | Exam sessions (`MS Ca thi`) |
| Campuses ($C$) | **2** | `Cơ sở 1` (LTK), `Cơ sở 2` (DiAn) |
| Distinct Exam Dates | **23** | From 2026-05-18 to 2026-06-13 |
| Distinct Start Times | **5** | `07g00`, `09g30`, `13g00`, `15g30`, `18g15` |
| Tasks / Roles | **6** | `DiAn_CBCT`, `LTK_CBCT`, `DiAn_Thư ký`, `LTK_Thư ký`, `LTK_Trưởng HĐ`, `DiAn_Trưởng HĐ` |
| Shift Duration | **150 min** | Fixed 2.5 hours per shift |
| Baseline Workload | **3 to 19** | Mean: 10.53 shifts/staff, Std: 2.22 |
