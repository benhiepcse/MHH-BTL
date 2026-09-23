# W03-T1 Schema Analysis Report

## 1. Task coverage

| W03-T1 task | Implemented? | Output |
|---|---|---|
| Read all 769 data rows | **True** | Row-count validation |
| Identify invigilators, sessions, dates, times, campus and tasks | **Yes** | Sets + session table |
| Check missing values, duplicates and data types | **Yes** | Data-quality report |
| Determine the meaning of a shift code | **Yes** | `MS Ca thi` parsing + consistency checks |

## 2. Dataset size and columns

- Data rows read: **769** (expected 769)
- Columns read: **9** (expected 9)
- Schema valid: **True**

| Column | Meaning |
|---|---|
| `Ca thi` | Human-readable shift description |
| `Ngày` | Exam date |
| `GIỜ` | Start time |
| `MS Ca thi` | Session/shift identifier `j` |
| `Nhiệm vụ` | Assignment task/role |
| `MS của CÁN BỘ COI THI` | Invigilator identifier `i` |
| `Thời gian` | Duration in minutes |
| `Thứ` | Weekday label |
| `Cơ sở` | Campus recorded on the assignment row |

## 3. Extracted sets

- `I` invigilators: **73**
- `J` sessions (`MS Ca thi`): **65**
- `C` non-missing campuses: **2**
- Distinct dates: **23**
- Distinct start times: **5**
- Distinct tasks: **6**

## 4. Assignment relation

Each data row records an observed baseline assignment. The ILP variable `x_ij` is not a raw column. It is indexed by an invigilator `i` from `I` and a session `j` from `J`.

- Unique observed `(invigilator, session)` pairs: **769**

## 5. Data quality

- Total missing cells: **56**
- Full duplicate rows: **0**
- Extra rows repeating an existing `(invigilator, session)` pair: **0**
- Distinct duplicated `(invigilator, session)` pairs: **0**

### Missing values

| Column | Missing values |
|---|---:|
| `Ca thi` | 0 |
| `Ngày` | 0 |
| `GIỜ` | 0 |
| `MS Ca thi` | 0 |
| `Nhiệm vụ` | 0 |
| `MS của CÁN BỘ COI THI` | 0 |
| `Thời gian` | 0 |
| `Thứ` | 28 |
| `Cơ sở` | 28 |

### Data types

| Column | pandas dtype |
|---|---|
| `Ca thi` | `str` |
| `Ngày` | `datetime64[us]` |
| `GIỜ` | `str` |
| `MS Ca thi` | `str` |
| `Nhiệm vụ` | `str` |
| `MS của CÁN BỘ COI THI` | `str` |
| `Thời gian` | `int64` |
| `Thứ` | `str` |
| `Cơ sở` | `str` |

## 6. Meaning of `MS Ca thi`

The code tests the observed pattern `YYYYMMDD_shiftNumber`. For example, `20260518_5` is parsed as date part `20260518` and shift number `5`.

- Codes whose encoded date matches `Ngày`: **65/65** sessions
- Codes whose shift number appears in the `Ca N` description: **65/65** sessions
- Sessions with internally consistent dates: **65/65**
- Sessions with internally consistent start times: **65/65**
- Sessions with internally consistent durations: **65/65**

Therefore the code does not merely infer the meaning from the column name. It checks the structure of the code against the date and shift information already present in the dataset.

## 7. Time interval and overlap

`End Time` is a derived value, not a raw dataset column:

`End Time = GIỜ + Thời gian (minutes)`

The derived start/end interval is used to calculate `Overlap(j,k)`. This relation is then translated through Requirement 1.3 into the no-double-booking inequality.

- Detected overlapping session pairs: **0**
- Sessions recorded with more than one campus: **9**

## 8. Requirement 1.3 bridge

For every real-data overlap pair `(j,k)` and every invigilator `i`, the bridge generates:

`x_i_j + x_i_k <= 1`

- Generated no-double-booking constraints: **0**
- Availability constraint status: not generated: no explicit Busy(i,j)/availability field in dataset
- Exact-capacity status: not generated: no explicit required-capacity field in dataset
- At-most-k status: not generated: max-load k is not a dataset field

The script intentionally does not invent Busy(i,j), required capacity r(j), or a maximum-load k when the raw dataset does not contain such fields.

## 9. Files generated

- `session_schema.csv`
- `assignment_pairs.csv`
- `W03_T1_schema_report.md`
