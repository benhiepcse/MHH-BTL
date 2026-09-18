# Contribution ledger (who did what) + signed % table

| Requirement | Primary owner (StudentID) | Reviewers |
|---|---|---|
| 1.1 | | |
| 1.2 — W02-T4 SAT solver and minimal UNSAT core | 2452347 Le Vo Nghia Hiep | TBD |

## Detailed Contribution Ledger

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

| Member (StudentID Name) | Contribution % | Signature |
|---|---|---|
