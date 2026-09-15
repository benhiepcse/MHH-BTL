# Weekly Meeting Minutes

## Meeting 01 — Week 01

### General Information

* Date: 13/09/2026
* Purpose: Review the Assignment Brief and assign tasks for Module 1.
* Team ID: `CO2011-261-CC-2353150`

### Attendance

| Student ID | Full Name         | Attendance |
| ---------: | ----------------- | ---------- |
|    2353150 | Võ Duy Thông      | Present    |
|    2453196 | Nguyễn Ngọc Thiện | Present    |
|    2453210 | Phan Thế Thông    | Present    |
|    2452347 | Lê Võ Nghĩa Hiệp  | Present    |
|    2452407 | Phạm Xuân Huy     | Present    |

### Topics Discussed

* Read and analyzed the Assignment Brief.
* Reviewed the project repository structure.
* Confirmed the Team ID as `CO2011-261-CC-2353150`.
* Confirmed the team seed as `287892112`.
* Analyzed Requirements 1.1, 1.2, and 1.3 of Module 1.
* Divided Module 1 into five tasks for the five team members.
* Identified the responsibilities and expected output files for each task.
* Identified the dependencies among the tasks.
* Developed a plan for completing Module 1 from 14/09/2026 to 20/09/2026.

### Decisions

1. Module 1 will be divided into five tasks, from W02-T1 to W02-T5.
2. Each team member will serve as the primary owner of one task.
3. Each member must commit their work using their individual Git identity.
4. All automatically generated results must be reproducible using `data/seed.txt`.
5. Module 1 must include at least one SAT instance and one UNSAT instance.
6. The SAT model must be decoded into a human-readable assignment.
7. The assignment returned by the solver must be verified against all hard constraints.
8. The UNSAT core must contain named constraints and must be checked for minimality.
9. Module 1 must be integrated into and executable through `run_all.py`.
10. All team members must review the results before creating the `m1` tag.

### Task Split for Week 02

| Task                                                     | Requirement | Primary Owner             | Expected Files                                                               |
| -------------------------------------------------------- | ----------- | ------------------------- | ---------------------------------------------------------------------------- |
| W02-T1 — Predicate Specification and Formal Verification | 1.1         | 2353150 Võ Duy Thông      | `predicates.md`, `predicate_validator.py`                                    |
| W02-T2 — Toy Instance and Real-Data Slice                | 1.2         | 2453196 Nguyễn Ngọc Thiện | `toy_instance.py`, `prepare_logic_data.py`, two JSON slices                  |
| W02-T3 — CNF Encoder                                     | 1.2         | 2453210 Phan Thế Thông    | `cnf_encoder.py`, `verify_cnf.py`                                            |
| W02-T4 — SAT Solver and Minimal UNSAT Core               | 1.2         | 2452347 Lê Võ Nghĩa Hiệp  | `sat_solver.py`, `verify_unsat_core.py`, `m1_results.json`                   |
| W02-T5 — Logic-to-LP Bridge and M1 Integration           | 1.3         | 2452407 Phạm Xuân Huy     | `logic_to_lp.py`, `logic_to_lp_table.md`, `m1_logic/README.md`, `run_all.py` |

### Task Dependencies

* Võ Duy Thông will complete the predicate definitions and first-order logic formulas to provide a consistent specification for the team.
* Nguyễn Ngọc Thiện will provide the toy instance and real-data slices.
* Phan Thế Thông will use the provided instances to develop the CNF encoder.
* Lê Võ Nghĩa Hiệp will receive the instances and encoded constraints, run the SAT/SMT solver, decode the resulting model, and verify the minimal UNSAT core.
* Phạm Xuân Huy will collect the results from the other four tasks and integrate the complete Module 1 pipeline.

### Week 02 Schedule

* Implementation: 14/09/2026–18/09/2026.
* Cross-review and integration: 19/09/2026.
* Final testing and documentation: 20/09/2026.
* Deadline for the `week-02` and `m1` tags: 23:59, 20/09/2026.

### Current Risks

* The tasks share common data, but the data contract has not yet been finalized.
* Boolean variable names and constraint names must be standardized before integration.
* W02-T4 depends on the outputs of W02-T2 and W02-T3.
* W02-T5 depends on the completed outputs of all preceding tasks.
* The team started late, so implementation must be completed before the review stage.

### Action Items

| Action                                             | Owner             | Deadline   | Status      |
| -------------------------------------------------- | ----------------- | ---------- | ----------- |
| Complete the predicate specification               | Võ Duy Thông      | 18/09/2026 | In progress |
| Create the toy instance and data slices            | Nguyễn Ngọc Thiện | 18/09/2026 | Not started |
| Develop the CNF encoder                            | Phan Thế Thông    | 18/09/2026 | Not started |
| Develop the SAT solver and verify the UNSAT core   | Lê Võ Nghĩa Hiệp  | 19/09/2026 | Not started |
| Complete the logic-to-LP bridge and M1 integration | Phạm Xuân Huy     | 20/09/2026 | In progress |
| Review and run the integrated tests                | All members       | 20/09/2026 | Not started |

### Next Meeting

* Proposed date: 19/09/2026
* Purpose: Review the five tasks and begin Module 1 integration.
