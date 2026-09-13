# Weekly Meeting Minutes

## Meeting 01 — Week 01

### General Information

- Date: 13/09/2026
- Purpose: Review the Assignment Brief and assign Module 1 tasks.
- Team ID: `CO2011-261-CC-2353150`

### Attendance

| Student ID | Full name | Attendance |
|---:|---|---|
| 2353150 | Võ Duy Thông | Present |
| 2453196 | Nguyễn Ngọc Thiện | Present |
| 2453210 | Phan Thế Thông | Present |
| 2452347 | Lê Võ Nghĩa Hiệp | Present |
| 2452407 | Phạm Xuân Huy | Present |

### Topics Discussed

- Đọc và phân tích Assignment Brief.
- Kiểm tra cấu trúc repository của dự án.
- Xác nhận Team ID là `CO2011-261-CC-2353150`.
- Xác nhận team seed là `287892112`.
- Phân tích Requirements 1.1, 1.2 và 1.3 của Module 1.
- Chia Module 1 thành năm nhiệm vụ cho năm thành viên.
- Xác định trách nhiệm và file đầu ra của từng nhiệm vụ.
- Xác định quan hệ phụ thuộc giữa các nhiệm vụ.
- Lên kế hoạch hoàn thành Module 1 từ 14/09/2026 đến 20/09/2026.

### Decisions

1. Module 1 được chia thành năm nhiệm vụ W02-T1 đến W02-T5.
2. Mỗi thành viên chịu trách nhiệm chính cho một nhiệm vụ.
3. Mỗi thành viên phải tự commit bằng Git identity cá nhân.
4. Tất cả kết quả sinh tự động phải tái lập được từ `data/seed.txt`.
5. Module 1 phải có ít nhất một trường hợp SAT và một trường hợp UNSAT.
6. SAT model phải được giải mã thành assignment dễ đọc.
7. Assignment do solver trả về phải được kiểm tra lại với các hard constraints.
8. UNSAT core phải có tên và được kiểm tra tính tối thiểu.
9. Module 1 phải được tích hợp và chạy thông qua `run_all.py`.
10. Các thành viên phải review kết quả trước khi tạo tag `m1`.

### Task Split for Week 02

| Task | Requirement | Primary owner | Expected files |
|---|---|---|---|
| W02-T1 — Predicate Specification and Formal Verification | 1.1 | 2353150 Võ Duy Thông | `predicates.md`, `predicate_validator.py` |
| W02-T2 — Toy Instance and Real-data Slice | 1.2 | 2453196 Nguyễn Ngọc Thiện | `toy_instance.py`, `prepare_logic_data.py`, two JSON slices |
| W02-T3 — CNF Encoder | 1.2 | 2453210 Phan Thế Thông | `cnf_encoder.py`, `verify_cnf.py` |
| W02-T4 — SAT Solver and Minimal UNSAT Core | 1.2 | 2452347 Lê Võ Nghĩa Hiệp | `sat_solver.py`, `verify_unsat_core.py`, `m1_results.json` |
| W02-T5 — Logic-to-LP Bridge and M1 Integration | 1.3 | 2452407 Phạm Xuân Huy | `logic_to_lp.py`, `logic_to_lp_table.md`, `m1_logic/README.md`, `run_all.py` |

### Task Dependencies

- Võ Duy Thông hoàn thiện predicates và FOL để nhóm sử dụng thống nhất.
- Nguyễn Ngọc Thiện cung cấp toy instance và data slices.
- Phan Thế Thông sử dụng instance để xây dựng CNF encoder.
- Lê Võ Nghĩa Hiệp nhận instance và encoded constraints để chạy SAT/SMT, giải mã model và kiểm tra minimal UNSAT core.
- Phạm Xuân Huy thu thập kết quả của bốn task trước và tích hợp toàn bộ Module 1.

### Week 02 Schedule

- Implementation: 14/09/2026–18/09/2026.
- Cross-review and integration: 19/09/2026.
- Final testing and documentation: 20/09/2026.
- Deadline for `week-02` and `m1`: 23:59, 20/09/2026.

### Current Risks

- Các task sử dụng chung dữ liệu nhưng chưa hoàn thiện data contract.
- Tên biến Boolean và tên constraint phải được thống nhất trước khi tích hợp.
- W02-T4 phụ thuộc vào đầu ra của W02-T2 và W02-T3.
- W02-T5 phụ thuộc vào kết quả hoàn chỉnh của các task trước.
- Nhóm bắt đầu muộn nên cần hoàn thành implementation trước ngày review.

### Action Items

| Action | Owner | Deadline | Status |
|---|---|---|---|
| Hoàn thiện predicate specification | Võ Duy Thông | 18/09/2026 | In progress |
| Tạo toy instance và data slices | Nguyễn Ngọc Thiện | 18/09/2026 | Not started |
| Xây dựng CNF encoder | Phan Thế Thông | 18/09/2026 | Not started |
| Xây dựng SAT solver và kiểm tra UNSAT core | Lê Võ Nghĩa Hiệp | 19/09/2026 | Not started |
| Hoàn thiện logic-to-LP và tích hợp M1 | Phạm Xuân Huy | 20/09/2026 | In progress |
| Review và chạy kiểm thử tích hợp | All members | 20/09/2026 | Not started |

### Next Meeting

- Proposed date: 19/09/2026
- Purpose: Review the five tasks and begin Module 1 integration.