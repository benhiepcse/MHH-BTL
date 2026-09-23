# Contribution ledger (who did what) + signed % table

| Requirement | Primary owner (StudentID) | Reviewers |
|---|---|---|
| 1.1 — W02-T1 Predicate Specification and Formal Verification | 2353150 Vo Duy Thong | 2452407 Pham Xuan Huy |
| 1.2 — W02-T2 Toy instance and real data slices | 2453196 Nguyen Ngoc Thien | 2452347 Le Vo Nghia Hiep |
| 1.2 — W02-T3 CNF Encoding | 2453210 Phan Van Thong | 2453196 Nguyen Ngoc Thien |
| 1.2 — W02-T4 SAT solver and minimal UNSAT core | 2452347 Le Vo Nghia Hiep | 2353150 Vo Duy Thong |
| 1.3 — W02-T5 Logic-to-LP bridge & M1 Integration | 2452407 Pham Xuan Huy | 2453210 Phan Van Thong |

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
- Tested two toy and two real-data instances, producing 2 SAT, 2 UNSAT, and 0 UNKNOWN results.

### 2353150 Vo Duy Thong — W02-T1
- Complete the sets $I$, $J$, $C$ and all necessary parameters.
- Write all hard regulations, including No double-booking, Capacity and Availability in first-order formula.  
- Verify the domain of each variable and quantifier.  
- Provide natural language explanations for every formula.  
- Implement a validator (`predicate_validator.py`) to detect basic formal/syntactic errors.

### 2452407 Pham Xuan Huy — W02-T5
- Implemented `m1_logic/logic_to_lp.py` providing systematic mapping from propositional clauses/predicates to 0/1 linear (in)equalities.
- Formulated linear transformations for availability constraints ($x_{ij} = 0$), no-double-booking ($x_{ij} + x_{ik} \le 1$), and exact shift capacity ($\sum x_{ij} = k$).
- Authored `m1_logic/logic_to_lp_table.md` documenting formal FOL-to-ILP bridge rules and proving the clause explosion dilemma in pure CNF ($\binom{n}{k+1}$ clauses) versus compact 0/1 LP formulations.
- Authored `m1_logic/README.md` providing architectural overview and standalone execution guides for Module 1.
- Integrated the entire Module 1 pipeline (validation, data prep, CNF verify, SAT solve, UNSAT core check, LP bridge) into central entry point `run_all.py` under `--stage m1`.  

| Member (StudentID Name) | Contribution % | Signature |
|---|---|---|
| 2353150 Vo Duy Thong | 20% | Signed |
| 2453196 Nguyen Ngoc Thien | 20% | Signed |
| 2453210 Phan Van Thong | 20% | Signed |
| 2452347 Le Vo Nghia Hiep | 20% | Signed |
| 2452407 Pham Xuan Huy | 20% | Signed |

| Requirement | Primary owner (StudentID) | Reviewers |
|---|---|---|
| 2.1 — W03-T1 Evaluate Schema Data | 2453210 Phan The Thong | 

## Detailed Contribution Ledger  
### 2453210 Phan The Thong — W03-T1
- Analyzed the anonymized dataset schema: verified 769 rows and 9 columns; identified invigilators, sessions, dates, start times, campuses, and task types.  
- Checked missing values, duplicates, and data types; analyzed the structure and semantic meaning of the `MS Ca thi` code.
- Implemented `m2_ilp/data_loader.py` providing robust data loading, schema validation, and missing value imputation.
- Authored `m2_ilp/data_schema.md` detailing the schema report, core mathematical sets, baseline workload distribution, and implications for ILP formulation.
