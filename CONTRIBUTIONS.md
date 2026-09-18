# Contribution ledger (who did what) + signed % table

| Requirement | Primary owner (StudentID) | Reviewers |
|---|---|---|
| 1.1 - W02-T1 Predicate Specification and Formal Verification | 2353150 Vo Duy Thong | |
| 1.2 — W02-T2 Toy instance and real data slices | 2453196 Nguyen Ngoc Thien | 2452347 Le Vo Nghia Hiep |
| 1.2 — W02-T4 SAT solver and minimal UNSAT core | 2452347 Le Vo Nghia Hiep | TBD |

## Detailed Contribution Ledger

### 2453196 Nguyen Ngoc Thien — W02-T2

- Implemented `m1_logic/toy_instance.py` representing the smallest instance from the assignment brief with both SAT and UNSAT variants.
- Implemented `m1_logic/prepare_logic_data.py` to extract small, deterministic data slices from the Faculty Excel dataset.
- Used Python standard library (`zipfile`, `xml.etree.ElementTree`) to parse Excel data without external dependencies.
- Designed deterministic shift and invigilator sampling seeded by the team seed (`287892112`).
- Generated historically feasible SAT slice `data/generated/m1_sat_slice.json` preserving actual assignments.
- Generated controlled UNSAT slice `data/generated/m1_unsat_slice.json` with documented conflict rationale.
- Verified JSON schema compatibility with downstream CNF encoding (W02-T3) and SAT solver (W02-T4).

### 2452347 Le Vo Nghia Hiep — W02-T4

- Implemented `m1_logic/sat_solver.py`.
- Implemented `m1_logic/verify_unsat_core.py`.
- Integrated Z3 SAT/SMT execution with named constraints.
- Decoded SAT models into readable invigilator-shift assignments.
- Independently validated decoded SAT models against every CNF clause.
- Extracted and minimized named UNSAT cores.
- Verified subset-minimality using single-constraint removal checks.
- Generated and verified `data/generated/m1_results.json`.
- Tested two toy and two real-data instances, producing 2 SAT, 2 UNSAT,
  and 0 UNKNOWN results.

### 2353150 Vo Duy Thong - W02-T1
- Complete the sets $I$, $J$, $C$ and all necessary parameters.
- Write all hard regulations, including No double-booking, Capacity and Availability in first-order formula.  
- Verify the domain of each variable and quantifier.  
- Provide natural language explanations for every formula.  
- Implement a validator (predicate_validator.py) to detect basic formal/syntactic errors.

| Member (StudentID Name) | Contribution % | Signature |
|---|---|---|
