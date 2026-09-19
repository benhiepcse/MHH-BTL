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
  - 2453196 Nguyen Ngoc Thien: Triển khai Toy Instance (toy_instance.py) và trích xuất lát cắt dữ liệu thật từ Excel (prepare_logic_data.py) tạo ra m1_sat_slice.json và m1_unsat_slice.json tất định theo seed; xây dựng cơ chế tạo ca UNSAT có kiểm soát và tài liệu hóa (Req 1.2, W02-T2).
  - 2353150 Vo Duy Thong: Implement predicate_validator.py to check the syntactic errors of predicates.md (Req 1.1, W02-T1)
  - 2026-09-18 — 2452347 Le Vo Nghia Hiep: Completed W02-T4 for Requirement 1.2 by implementing the Z3 SAT/SMT execution pipeline, decoding and independently validating SAT assignments, extracting named UNSAT cores, minimizing them through deterministic deletion, and verifying subset-minimality using single-constraint removal checks. Generated and verified `data/generated/m1_results.json` on two toy and two real-data instances, obtaining 2 SAT, 2 UNSAT, and 0 UNKNOWN results.
