# Design decisions (your own words)
Record, per module, WHY you chose each objective, constraint, DFA, and dynamical direction, and what you rejected.


## Module 1 — W02-T2 Toy Instance and Real-Data Slices

**Requirement:** 1.2
**Decision owner:** 2453196 Nguyen Ngoc Thien

### Separate toy instance from real data slices

I implemented `toy_instance.py` as an independent script strictly reproducing
the smallest instance described in the Assignment Brief (CB1, CB2, CB3 across
Morning and Afternoon shifts).

I rejected embedding the toy instance directly into the Excel extraction
pipeline because the toy instance serves as a zero-dependency ground-truth
baseline for unit-testing the CNF encoder and SAT solver before touching the
full dataset.

### Filter moderate-capacity shifts for the logic slice

In `prepare_logic_data.py`, I filtered candidates to shifts requiring 1 to 5
invigilators before sampling.

I chose this range because Module 1 encodes exact capacity into CNF using
binomial expansion (O(n^(k+1)) clauses). Real shifts with 15–32 invigilators
would cause combinatorial clause explosion, making SAT solving impractical.
I rejected including large shifts in Module 1, deferring them to Module 2 where
ILP handles cardinality in a single linear equality.

### Parse Excel via standard library instead of third-party libraries

I implemented the Excel reader using Python's built-in `zipfile` and
`xml.etree.ElementTree` modules rather than requiring `pandas` or `openpyxl`.

I chose this to make data preparation completely lightweight and self-contained,
guaranteeing that `prepare_logic_data.py` executes out-of-the-box on any clean
environment without dependency mismatches.

### Enforce 100% reproducibility via the team seed

I isolated all random choices (shift selection and non-assigned busy staff
assignment) inside `random.Random(seed)` initialized with the team seed
(`287892112`).

I rejected non-deterministic selection or manual cherry-picking because the
course grading relies on clean reproduction from `data/seed.txt`.

### Engineer UNSAT via systematic capacity-availability starvation

For the UNSAT slice (`m1_unsat_slice.json`), I selected target shift
`20260601_1` (capacity = 1) and marked all available invigilators in the slice
as busy during that shift, leaving 0 available staff for a shift needing 1.

I chose this explicit starvation mechanism because it creates a minimal,
mathematically undeniable conflict between exact capacity and availability
constraints. I rejected arbitrary data corruptions without clear rationale
because they obscure the minimal UNSAT core verification needed in W02-T4.


## Module 1 — W02-T4 SAT Solver and Minimal UNSAT Core

**Requirement:** 1.2
**Decision owner:** 2452347 Le Vo Nghia Hiep

### Use Z3 with named CNF constraints

I used Z3 because W02-T4 requires both SAT model generation and named UNSAT
core extraction. Each CNF constraint is tracked by its original name so that
an UNSAT core can be reported in a readable form and traced back to the input
instance.

I rejected returning only an SAT/UNSAT status because it would not satisfy the
requirements for readable assignments, named UNSAT cores, or verification
evidence.

### Independently validate SAT assignments

After Z3 returns SAT, the Boolean model is decoded into readable
invigilator-shift assignments. The decoded assignment is then checked against
every CNF clause independently of the solver result.

This additional validation was chosen to detect errors in model decoding or
result serialization. I rejected relying only on Z3's SAT status because that
would not verify that the exported assignment still satisfies every
constraint.

### Use deletion-based UNSAT core minimization

The initial named UNSAT core returned by Z3 is minimized deterministically.
Each constraint is removed in turn, and the remaining constraints are checked
again. A constraint is permanently removed when the remaining subset is still
UNSAT.

I chose this method because it is straightforward, reproducible, and suitable
for the provided toy and real-data slices. I rejected claiming a globally
minimum-cardinality core because deletion-based minimization guarantees only
subset-minimality.

### Verify subset-minimality separately

The verification script checks that the complete candidate core is UNSAT and
that removing any single constraint makes the remaining subset SAT. It also
checks that every reported constraint name exists in the original CNF input.

I kept verification separate from core generation so that the generated result
can be independently checked instead of trusting the solver pipeline alone.

### Treat UNKNOWN as a failed verification

Any UNKNOWN result is recorded and causes the complete-suite validation or
UNSAT-core verification to fail.

I chose this conservative behavior because UNKNOWN does not prove either SAT
or UNSAT and therefore cannot support a correctness claim.

### Store reproducible evidence in JSON

The final results are stored in `data/generated/m1_results.json`, including
instance metadata, SAT assignments, assignment validation, named UNSAT cores,
minimality checks, seed, team ID, and summary counts.

JSON was selected because it is machine-readable, deterministic, and suitable
for later integration with the Module 1 runner and report.


## Module 2 — W03-T1 Data Schema Analysis

**Requirement:** 2.1  
**Decision owner:** 2453210 Phan The Thong 

### Strictly validate 769 rows and schema integrity

I enforced a hard assertion that `m2_ilp/data_loader.py` must read exactly 769
data rows and 9 columns. If the row count diverges, execution halts immediately
with an informative exception.

I chose this strict check because downstream ILP parameters (such as shift
demands $c_j$ and invigilator loads $w_i$) depend on exact aggregation over the
769 baseline assignments. Tolerating partial or extra rows would invisibly
corrupt the baseline comparison.

### Mathematically reconstruct missing values rather than dropping rows

The dataset contains 28 missing values in both `Thứ` (Weekday) and `Cơ sở`
(Campus) across rows 741–768.

I rejected dropping these rows or filling them with arbitrary placeholders.
Instead, I reconstructed `Cơ sở` from the prefix of the `Nhiệm vụ` column
(`LTK_` -> `Cơ sở 1`, `DiAn_` -> `Cơ sở 2`) and reconstructed `Thứ` directly from
the ISO calendar date in `Ngày`. This ensures 100% deterministic, sound data
recovery without losing any of the 769 assignments.

### Treat `MS Ca thi` as exam time slots rather than single exam rooms

Through semantic analysis of `MS Ca thi`, I proved that the code pattern
`YYYYMMDD_K` represents a synchronized campus-wide exam time slot. Each shift
demands up to 35 invigilators across multiple examination rooms and can operate
concurrently across both campuses (observed in 9 distinct sessions).

I rejected modeling each row as an individual shift because multiple invigilators
cooperate within the same `MS Ca thi`. In the ILP model, this establishes the
demand equation $\sum_{i \in I} x_{ij} = c_j$, where $c_j$ is the aggregate
capacity of session $j$.

