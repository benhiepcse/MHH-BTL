# Weekly checkpoints (one dated entry per week)
## week-01 (7-13 Sep)
- Progress:
- Per member: <StudentID Name> did ...
- 2452407 Pham Xuan Huy: Triển khai hàm mô hình hóa ràng buộc sức chứa (Cardinality constraints) cho ca thi trong logic_to_lp.py; phân tích cơ chế nén mệnh đề của LP so với CNF trong README (Req 1.3).
- 2353150 Vo Duy Thong: Introduce predicates, set and domain, write the hard-regulations (no double-booking, capacity, availability) in first-order formula (Req 1.1)
- 2452347 Lê Võ Nghĩa Hiệp : Participated in analyzing the Assignment Brief and Requirement 1.2, took ownership of W02-T4 — SAT Solver and Minimal UNSAT Core, and assumed responsibility for running the SAT/SMT solver, decoding models, and verifying the solver results.
- 2453210 Phan The Thong: Triển khai các ràng buộc Logic-to-LP cơ bản (Availability và Overlap constraints) trong `logic_to_lp.py`, mô hình hóa quy tắc cán bộ bận và các ca trùng thời gian thành ràng buộc tuyến tính (Req 1.3).

## week-02 (14-20 Sep)
- Progress: Triển khai và tích hợp Module 1 (Logic)
- Per member:
  - 2026-09-17 — 2453210 Phan Thế Thông: Implemented `m1_logic/cnf_encoder.py` and `m1_logic/verify_cnf.py` for CNF encoding of `Assign(i,j)`, availability, no-double-booking, and exactly-k constraints; verified toy SAT/UNSAT clause counts and real data slices with Z3 (Req 1.2, W02-T3).
  - 2453196 Nguyen Ngoc Thien: Implement Toy Instance (toy_instance.py) and extract real data slices from Excel (prepare_logic_data.py) to create deterministic m1_sat_slice.json and m1_unsat_slice.json based on the seed; build a mechanism for creating controlled and documented UNSAT cases (Req 1.2, W02-T2).
  - 2353150 Vo Duy Thong: Implement predicate_validator.py to check the syntactic errors of predicates.md (Req 1.1, W02-T1)
  - 2026-09-18 — 2452347 Le Vo Nghia Hiep: Completed W02-T4 for Requirement 1.2 by implementing the Z3 SAT/SMT execution pipeline, decoding and independently validating SAT assignments, extracting named UNSAT cores, minimizing them through deterministic deletion, and verifying subset-minimality using single-constraint removal checks. Generated and verified `data/generated/m1_results.json` on two toy and two real-data instances, obtaining 2 SAT, 2 UNSAT, and 0 UNKNOWN results.
- 2452407 Pham Xuan Huy: Hoàn thành Logic-to-LP bridge (logic_to_lp.py), lập bảng logic_to_lp_table.md, m1_logic/README.md và tích hợp thành công toàn bộ pipeline Module 1 vào run_all.py (Req 1.3).
## week-03 (21-27 Sep)
- Progress: Triển khai và tích hợp Module 2 (Linear and Integer Programming)
- Per member:
    - 2026-09-22 - 2353150 Vo Duy Thong: Completed W03-T1 schema analysis for the anonymized invigilator assignment dataset. Verified that the dataset contains 769 rows and 9 columns. Identified the main sets and attributes required for Module 2: invigilators, exam sessions, dates, start times, campuses and task types. Checked missing values, duplicate rows, repeated assignment pairs, and data types. Analyzed the structure and meaning of the $\text{MS Ca thi}$ (exam session code). Prepared the schema-analysis results and connected the extracted session/time information to the Requirement 1.3 no double-booking formulation. (Req 2.1, W03-T1)   
