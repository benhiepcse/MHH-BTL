# Báo Cáo Phân Tích Schema Dữ Liệu (W03-T1 — Data Schema Analysis)

**Mã nhiệm vụ:** W03-T1  
**Yêu cầu:** Requirement 2.1 — Khai phá và định nghĩa tham số, tập hợp từ dữ liệu thực tế  
**Thành viên phụ trách (TV1):** 2453210 — Phan Thế Thông  
**Module:** Module 2 — Linear & Integer Programming (ILP)  
**Tập tin thực thi:** `m2_ilp/data_loader.py`  
**Dataset nguồn:** `data/Dataset_Anonymized_Invigilator_Assignment_Problem.xlsx`

---

## 1. Mục tiêu và Phạm vi Nhiệm vụ W03-T1

Nhiệm vụ **W03-T1** thiết lập nền móng dữ liệu thực nghiệm cho toàn bộ Module 2 (Quy hoạch tuyến tính nguyên - ILP). Dựa trên phân công trong đề bài và kế hoạch tuần 3, TV1 thực hiện 4 mục tiêu cốt lõi:
1. **Đọc đủ 769 dòng:** Đọc toàn bộ 769 bản ghi phân công từ file dữ liệu thực tế ẩn danh, kiểm chứng kích thước và tính toàn vẹn của bảng dữ liệu.
2. **Xác định các tập hợp cơ bản:** Trích xuất danh sách giám thị ($I$), danh sách ca thi ($J$), ngày thi, giờ thi, cơ sở ($C$) và các loại nhiệm vụ.
3. **Kiểm tra chất lượng dữ liệu:** Rà soát toàn diện giá trị khuyết thiếu (missing values), dòng trùng lặp (duplicates), trùng lặp cặp phân công và kiểm định kiểu dữ liệu.
4. **Xác định ý nghĩa của mã `MS Ca thi`:** Phân tích cấu trúc định dạng của `MS Ca thi`, đối chiếu chéo với các cột thời gian/mô tả ca thi và rút ra ý nghĩa mô hình hóa cho bài toán ILP.

---

## 2. Đọc và Kiểm định Kích thước Dữ liệu

Tập lệnh `m2_ilp/data_loader.py` đã đọc trực tiếp trang tính `Sheet1` của file `Dataset_Anonymized_Invigilator_Assignment_Problem.xlsx`:

| Tiêu chí kiểm tra | Kế hoạch / Đề bài yêu cầu | Kết quả thực tế đo được | Đánh giá |
|:---|:---:|:---:|:---:|
| **Số dòng dữ liệu (Rows)** | Đúng 769 dòng dữ liệu (không tính header) | **769 dòng** | **ĐẠT (100%)** |
| **Số cột thuộc tính (Columns)** | 9 cột | **9 cột** | **ĐẠT (100%)** |
| **Trùng lặp toàn dòng** | 0 dòng | **0 dòng** | **ĐẠT** |
| **Trùng lặp cặp phân công $(i, j)$** | 0 cặp | **0 cặp** | **ĐẠT** |

Mỗi dòng dữ liệu tương ứng với một lượt phân công giám thị $i$ vào ca thi $j$ trong lịch thi thực tế của trường/khoa.

---

## 3. Bảng Phân Tích Chi Tiết 9 Thuộc Tính (Data Dictionary)

Dưới đây là đặc tả chi tiết của 9 cột thuộc tính trong tập dữ liệu:

| STT | Tên cột trong file | Kiểu dữ liệu (pandas) | Số giá trị duy nhất | Số ô thiếu (NaN) | Ý nghĩa nghiệp vụ và mô hình hóa |
|:---:|:---|:---:|:---:|:---:|:---|
| 1 | `Ca thi` | `object` (str) | 49 | 0 | Chuỗi mô tả đầy đủ: Thứ, Ngày/Tháng/Năm, Số ca thi và khoảng thời gian (VD: `Thứ 2, 18/05/2026, Ca 5: 18g15-20g45`). |
| 2 | `Ngày` | `datetime64[us]` | 23 | 0 | Ngày diễn ra ca thi (từ `2026-05-18` đến `2026-06-13`). |
| 3 | `GIỜ` | `object` (str) | 5 | 0 | Giờ bắt đầu ca thi định dạng giờ Việt Nam (`07g00`, `09g30`, `13g00`, `15g30`, `18g15`). |
| 4 | `MS Ca thi` | `object` (str) | 65 | 0 | **Mã định danh duy nhất của ca thi ($j \in J$)**. Có dạng `YYYYMMDD_K`. |
| 5 | `Nhiệm vụ` | `object` (str) | 6 | 0 | Vai trò và địa điểm phân công cụ thể của giám thị (kết hợp cơ sở + chức danh). |
| 6 | `MS của CÁN BỘ COI THI` | `object` (str) | 73 | 0 | **Mã định danh duy nhất của cán bộ coi thi ($i \in I$)** (từ `CB001` đến `CB073`). |
| 7 | `Thời gian` | `int64` | 1 | 0 | Thời lượng của một ca thi tính bằng phút (toàn bộ 769 dòng đều là **150 phút** = 2 giờ 30 phút). |
| 8 | `Thứ` | `object` (str) | 7 | 28 | Tên thứ trong tuần (`Thứ 2`, `Thứ 3`, ..., `Chủ Nhật`). Có 28 dòng bị trống. |
| 9 | `Cơ sở` | `object` (str) | 2 | 28 | Địa điểm cơ sở thi (`Cơ sở 1`, `Cơ sở 2`). Có 28 dòng bị trống. |

---

## 4. Xác Định Các Tập Hợp Cơ Bản Cho Bài Toán ILP

Từ 769 dòng dữ liệu, module đã trích xuất thành công các tập hợp toán học chuẩn tắc:

### 4.1. Tập Cán Bộ Coi Thi / Giám Thị ($I$)
- **Ký hiệu toán học:** $I = \{CB001, CB002, \dots, CB073\}$
- **Kích thước:** $|I| = 73$ cán bộ.
- **Vai trò:** Mỗi phần tử $i \in I$ đại diện cho một nhân sự coi thi có thể được điều động trong kỳ thi.

### 4.2. Tập Ca Thi / Phiên Thi ($J$)
- **Ký hiệu toán học:** $J = \{j_1, j_2, \dots, j_{65}\}$ tương ứng với 65 giá trị `MS Ca thi` duy nhất.
- **Kích thước:** $|J| = 65$ ca thi.
- **Vai trò:** Mỗi phần tử $j \in J$ đại diện cho một khung thời gian thi xác định trong kỳ thi cần được bố trí đủ số lượng giám thị.

### 4.3. Tập Cơ Sở Thi ($C$)
- **Ký hiệu toán học:** $C = \{c_1, c_2\}$ trong đó:
  - $c_1$: `Cơ sở 1` (Lý Thường Kiệt — ký hiệu `LTK`).
  - $c_2$: `Cơ sở 2` (Dĩ An — ký hiệu `DiAn`).
- **Kích thước:** $|C| = 2$.

### 4.4. Tập Ngày Thi và Khung Giờ Thi
- **Tập ngày thi:** Kỳ thi diễn ra trong **23 ngày** khác nhau, trải dài từ ngày `18/05/2026` đến `13/06/2026`.
- **Tập giờ bắt đầu:** Có **5 khung giờ bắt đầu chuẩn**:
  - `07g00` (Ca 1 sáng) — 117 lượt phân công.
  - `09g30` (Ca 2 sáng) — 230 lượt phân công.
  - `13g00` (Ca 3 chiều) — 310 lượt phân công.
  - `15g30` (Ca 4 chiều) — 85 lượt phân công.
  - `18g15` (Ca 5 tối) — 27 lượt phân công.
- **Thời lượng:** Cố định 150 phút cho tất cả các ca.

### 4.5. Tập Nhiệm Vụ Phân Công
Bộ dữ liệu gồm **6 loại nhiệm vụ** với cơ cấu số lượng cụ thể:
1. `DiAn_CBCT`: 430 lượt (Cán bộ coi thi tại Dĩ An - CS2).
2. `LTK_CBCT`: 286 lượt (Cán bộ coi thi tại Lý Thường Kiệt - CS1).
3. `DiAn_Thư ký`: 21 lượt (Thư ký điểm thi tại Dĩ An - CS2).
4. `LTK_Thư ký`: 14 lượt (Thư ký điểm thi tại Lý Thường Kiệt - CS1).
5. `LTK_Trưởng HĐ`: 10 lượt (Trưởng hội đồng thi tại Lý Thường Kiệt - CS1).
6. `DiAn_Trưởng HĐ`: 8 lượt (Trưởng hội đồng thi tại Dĩ An - CS2).
- **Tổng cộng:** $430 + 286 + 21 + 14 + 10 + 8 = 769$ lượt.

---

## 5. Kiểm Tra Chất Lượng Dữ Liệu (Data Quality)

### 5.1. Phân Tích Giá Trị Khuyết Thiếu (Missing Values)
- **Tổng số ô khuyết thiếu:** 56 ô trên toàn bộ ma trận dữ liệu ($769 \times 9 = 6921$ ô), chiếm tỷ lệ rất nhỏ (0.81%).
- **Các cột hoàn toàn không thiếu (0 missing, 100% đầy đủ):** `Ca thi`, `Ngày`, `GIỜ`, `MS Ca thi`, `Nhiệm vụ`, `MS của CÁN BỘ COI THI`, `Thời gian`.
- **Phân bổ giá trị thiếu:**
  - Cột `Thứ`: thiếu 28 giá trị (tại các dòng 741 đến 768).
  - Cột `Cơ sở`: thiếu 28 giá trị (chính xác cùng 28 dòng trên).
- **Đánh giá và Giải pháp Phục hồi (Imputation):**
  - Thiếu sót này do quá trình nhập liệu/kết xuất dữ liệu gốc để trống 2 cột phụ ở 28 dòng cuối.
  - **Khả năng phục hồi đạt 100% chính xác:**
    1. Giá trị `Cơ sở` được xác định hoàn toàn qua tiền tố của cột `Nhiệm vụ`: các dòng có nhiệm vụ bắt đầu bằng `LTK_` tương ứng với `Cơ sở 1` (15 dòng), các dòng bắt đầu bằng `DiAn_` tương ứng với `Cơ sở 2` (13 dòng).
    2. Giá trị `Thứ` được nội suy toán học chính xác từ cột `Ngày` (ví dụ: ngày `2026-06-08` là Thứ 2, `2026-06-13` là Thứ 7).
  - `DataLoader.get_imputed_data()` đã tự động xử lý chuẩn hóa mà không làm biến dạng dữ liệu gốc.

### 5.2. Kiểm Tra Tính Trùng Lặp (Duplicates)
- **Trùng lặp bản ghi toàn bộ:** 0 dòng trùng lặp.
- **Trùng lặp cặp phân công $(i, j)$:** 0 cặp.
  - Trong lịch thi thực tế, không có trường hợp một cán bộ $i$ bị ghi nhận phân công trùng 2 lần trong cùng một ca thi $j$.
  - 769 dòng phân công là 769 mối quan hệ $\text{Assign}(i, j) = 1$ độc lập.

---

## 6. Xác Định và Giải Mã Ý Nghĩa của `MS Ca thi`

### 6.1. Cấu Trúc Mã Hóa
Mã `MS Ca thi` tuân thủ quy tắc biểu thức chính quy (Regex):
$$\text{Pattern} = \texttt{\^{}(\textbackslash d\{8\})\_(\textbackslash d+)\$}$$
Ví dụ: `20260518_5`, `20260601_1`, `20260613_3`.

Cấu trúc gồm hai thành phần phân tách bởi dấu gạch dưới `_`:
1. **Phần ngày thi (`YYYYMMDD`):** 8 chữ số biểu diễn ngày diễn ra ca thi theo chuẩn ISO (Năm - Tháng - Ngày).
2. **Phần số thứ tự ca thi (`K`):** Chữ số biểu diễn số thứ tự của ca thi trong ngày hôm đó:
   - `1`: Ca 1 (buổi sáng, bắt đầu 07g00).
   - `2`: Ca 2 (buổi sáng, bắt đầu 09g30).
   - `3`: Ca 3 (buổi chiều, bắt đầu 13g00).
   - `4`: Ca 4 (buổi chiều, bắt đầu 15g30).
   - `5`: Ca 5 (buổi tối, bắt đầu 18g15).

### 6.2. Kiểm Chứng Cú Pháp và Tính Nhất Quán
Kiểm tra đối chiếu chéo trên toàn bộ 65 ca thi:
- **Khớp ngày thi (`code_date == Ngày`):** **65/65 ca thi (100%)**.
- **Khớp số ca (`code_shift in Ca thi`):** **65/65 ca thi (100%)**.
- **Tính nhất quán nội tại trong từng ca thi:** 100% các dòng cùng mã `MS Ca thi` đều có cùng `Ngày`, cùng `GIỜ` bắt đầu, và cùng `Thời gian` (150 phút).

### 6.3. Bản Chất Nghiệp Vụ Của `MS Ca thi` (Quan Trọng Đối Với ILP)
Một phát hiện nghiệp vụ đặc biệt quan trọng:
- `MS Ca thi` **không phải là mã của một phòng thi cụ thể**, mà là **mã định danh của một khung thời gian thi đồng thời toàn trường (Exam Time Slot / Session)**.
- Trong cùng một `MS Ca thi`:
  - Số lượng cán bộ cần phân công dao động từ **1 đến 35 cán bộ** (trung bình 11.83 cán bộ/ca) phụ thuộc vào quy mô số lượng phòng thi mở trong khung giờ đó.
  - **Tổ chức thi song song tại hai cơ sở:** Có **9 ca thi** trong dữ liệu diễn ra đồng thời ở cả Cơ sở 1 và Cơ sở 2.
- **Hệ quả mô hình hóa:**
  - Nếu mô hình hóa cấp ca thi: Biến quyết định cơ bản là $x_{ij} \in \{0, 1\}$ (cán bộ $i$ coi ca $j$). Sức chứa ca thi là một số nguyên $c_j \in [1, 35]$:
    $$\sum_{i \in I} x_{ij} = c_j \quad \forall j \in J$$
  - Nếu cần xét vị trí cơ sở hoặc phân chia tải theo cơ sở: Có thể chia nhỏ ca thi $j$ thành các phiên $(j, c)$ theo từng cơ sở, hoặc định nghĩa biến $x_{ijc} \in \{0, 1\}$.

---

## 7. Phân Tích Lịch Trình Thực Tế (Baseline Assignment)

Việc phân tích lịch phân công gốc trong dataset giúp xác định các thông số thực nghiệm (parameters) và chuẩn đối sánh (baseline) cần vượt qua trong Module 2:

### 7.1. Phân Phối Tải Công Việc Của Giám Thị (Workload Distribution)
- **Tổng số lượt phân công:** 769 lượt.
- **Số giám thị:** 73 cán bộ.
- **Tải trung bình ($\bar{w}$):** $\frac{769}{73} \approx 10.53$ ca/cán bộ.
- **Phân phối tải trong baseline:**
  - Tải thấp nhất: 3 ca.
  - Tải cao nhất: 19 ca.
  - Độ lệch chuẩn tải: $\sigma \approx 2.22$ ca.
  - Tứ phân vị: 25% làm $\le 9$ ca; 50% (trung vị) làm 11 ca; 75% làm $\le 12$ ca.
- **Nhận xét:** Lịch phân công thủ công ban đầu có sự chênh lệch đáng kể (từ 3 đến 19 ca, biên độ chênh lệch là 16 ca). Đây chính là mục tiêu tối ưu của Module 2: sử dụng hàm mục tiêu Min-Max Load hoặc Min $L_1$-Deviation để làm phẳng phân phối tải và đảm bảo tính công bằng (Fairness).

### 7.2. Đặc Trưng Không Di Chuyển Liên Cơ Sở Trong Cùng Một Ngày
- Phân tích 769 lượt phân công cho thấy: **Không có bất kỳ cán bộ nào bị phân công ở cả 2 cơ sở trong cùng một ngày** ($0$ trường hợp).
- Một cán bộ có thể coi tối đa tới 4 ca trong cùng một ngày (ví dụ `CB001` coi 4 ca liên tiếp vào ngày 13/06/2026), nhưng toàn bộ các ca này đều diễn ra tại cùng một cơ sở (`Cơ sở 1`).
- Đây là một ràng buộc thực tế tự nhiên cần được đưa vào mô hình ILP:
  $$\forall i \in I, \forall d \in D: \quad \text{Số lượng cơ sở phân công cho cán bộ } i \text{ trong ngày } d \le 1$$

### 7.3. Tính Chồng Lấn Thời Gian (Overlapping Sessions)
- Thời lượng mỗi ca là 150 phút (2h30). Các mốc thời gian trong ngày:
  - Ca 1: `07g00 - 09g30`
  - Ca 2: `09g30 - 12g00`
  - Ca 3: `13g00 - 15g30`
  - Ca 4: `15g30 - 18g00`
  - Ca 5: `18g15 - 20g45`
- Các ca liên tiếp (Ca 1 và Ca 2, hoặc Ca 3 và Ca 4) tiếp giáp nhau tại biên thời gian nhưng không có khoảng giao thời gian dương trong khoảng mở $(Start, End)$. Trong lịch thực tế, cùng một cán bộ có thể coi cả Ca 1 và Ca 2 liên tiếp tại cùng một cơ sở.
- Đối với các ca có khoảng giao thời gian thực sự, ràng buộc chống trùng lịch (No-double-booking) kế thừa từ Module 1 ($x_{ij} + x_{ik} \le 1$) luôn được kích hoạt.

---

## 8. Kết Luận và Hướng Dẫn Tích Hợp Cho Module 2

Kết quả phân tích schema từ **W03-T1** cung cấp đầy đủ thông số đầu vào cho các tác vụ tiếp theo của Module 2:
1. **Module nạp dữ liệu chuẩn (`m2_ilp/data_loader.py`):** Cung cấp API trực tiếp cho các thành viên trong nhóm gọi hàm `DataLoader().load_raw_data()`, `extract_sets()`, `get_imputed_data()`.
2. **Xác lập không gian biến quyết định:**
   - Biến nhị phân: $x_{ij} \in \{0, 1\}$ với $i \in I$ ($|I| = 73$) và $j \in J$ ($|J| = 65$), tổng cộng $73 \times 65 = 4745$ biến nhị phân tiềm năng.
3. **Các ràng buộc cứng (Hard Constraints) sẵn sàng xây dựng:**
   - Ràng buộc đủ sức chứa ca thi: $\sum_{i \in I} x_{ij} = c_j \quad \forall j \in J$.
   - Ràng buộc không trùng ca chồng lấn: $x_{ij} + x_{ik} \le 1 \quad \forall (j, k) \in \text{Overlap}$.
   - Ràng buộc đồng nhất cơ sở theo ngày (Same-campus per day).
4. **Hàm mục tiêu công bằng (Fairness Objective):** Đã có các chỉ số baseline (Max load = 19, Std = 2.22) để kiểm chứng nghiệm của bộ giải ILP (OR-Tools / PuLP) vượt trội so với baseline.
