# Đặc tả Mô hình Toán học Quy hoạch Nguyên Tuyến tính (ILP Model Specification)

**Mã học phần:** CO2011 — Cấu trúc Rời rạc / Mô hình hóa Toán học (Discrete Structures / Mathematical Modeling)  
**Học kỳ:** HK261  
**Module:** Module 2 — Linear and Integer Programming (ILP)  
**Nhiệm vụ (Task):** `W03-T3` — Sets, Parameters và Decision Variables  
**Thành viên chịu trách nhiệm:** Phan The Thong (MSSV: 2453210)  
**Tập tin đặc tả:** `m2_ilp/model_spec.md`  
**Mã nguồn triển khai:** `m2_ilp/variables.py`  

---

## 1. Giới thiệu và Bối cảnh Bài toán (Problem Overview)

Trong bài toán **Phân công Cán bộ Coi thi (Invigilator Assignment Problem - IAP)**, mục tiêu trọng tâm của Module 2 là chuyển hóa mô hình đặc tả logic mệnh đề / vị từ từ Module 1 thành mô hình **Quy hoạch Nguyên Tuyến tính (Integer Linear Programming - ILP)** hoàn chỉnh. 

Mô hình hướng tới việc:
1. **Thỏa mãn 100% các ràng buộc cứng (Hard Constraints):**
   - Đảm bảo đúng và đủ số lượng giám thị cho mỗi ca thi (Demand / Capacity).
   - Tuyệt đối không phân công cán bộ vào các ca thi bị trùng / giao thoa thời gian (No Double-Booking).
   - Tuyệt đối không phân công cán bộ vào ca thi mà cán bộ đó bận (Availability).
2. **Tối ưu hóa tính công bằng (Fairness Optimization):**
   - Phân bổ số lượng ca thi giữa các cán bộ đồng đều nhất có thể, tránh tình trạng quá tải cục bộ.
   - Để giữ mô hình ở dạng **ILP** (tránh dạng phi tuyến MIQP do phương sai bậc hai), bài toán sử dụng mô hình tuyến tính hóa công bằng cực tiểu hóa tải tối đa (**Min-Max Fairness**: $\min t$ với $t \ge w_i, \forall i$).
3. **Giảm thiểu vi phạm ràng buộc mềm (Soft Constraints Minimization):**
   - Tối đa hóa mức độ hài lòng về địa điểm / cơ sở làm việc mong muốn của từng cán bộ (Location Preference), giảm chi phí đi lại giữa các cơ sở.

Để xây dựng mô hình toán học chuẩn tắc, tài liệu này đặc tả tường minh 3 thành phần cốt lõi:
- **Tập hợp (Sets):** $I, J, C$.
- **Tham số (Parameters):** $\text{demand}, \text{availability}, \text{overlap}, \text{campus}$.
- **Biến quyết định (Decision Variables):** $x_{ij}, w_i, t$ kèm định nghĩa kiểu dữ liệu (**Binary**, **Integer**, **Continuous**).

---

## 2. Định nghĩa các Tập hợp (Sets Definition)

Ký hiệu các tập hợp cơ bản của bài toán:

### 2.1. Tập hợp Cán bộ Coi thi: $I$ (Invigilators Set)
- **Ký hiệu toán học:** $I = \{1, 2, \dots, |I|\}$ hoặc tập các định danh $I = \{\text{CB001}, \text{CB002}, \dots, \text{CB073}\}$.
- **Chỉ số phần tử:** $i \in I$.
- **Ý nghĩa:** Tập hợp tất cả các cán bộ, giảng viên, nhân viên đủ điều kiện tham gia công tác coi thi trong kỳ thi.
- **Quy mô dữ liệu thực nghiệm:** $|I| = 73$ cán bộ (trích xuất từ bộ dữ liệu thực tế tại `Dataset_Anonymized_Invigilator_Assignment_Problem.xlsx`).
- **Thuộc tính liên kết của mỗi cán bộ $i \in I$:**
  - $\text{id}_i$: Mã định danh duy nhất (ví dụ: `CB001`).
  - $\text{pref}_i \in C$: Cơ sở / địa điểm ưu tiên đăng ký làm việc (được tạo giả lập từ seed nhóm `287892112` ở W03-T2).

### 2.2. Tập hợp Ca thi / Buổi thi: $J$ (Exam Sessions / Shifts Set)
- **Ký hiệu toán học:** $J = \{1, 2, \dots, |J|\}$ hoặc tập các mã ca thi $J = \{\text{sid}_1, \text{sid}_2, \dots, \text{sid}_{65}\}$.
- **Chỉ số phần tử:** $j, k \in J$.
- **Ý nghĩa:** Tập hợp toàn bộ các ca thi độc lập cần bố trí nhân sự giám sát trong suốt kỳ thi.
- **Quy mô dữ liệu thực nghiệm:** $|J| = 65$ ca thi.
- **Thuộc tính liên kết của mỗi ca thi $j \in J$:**
  - $\text{id}_j$: Mã ca thi (ví dụ: `20260518_1`, `20260518_2`, ...).
  - $\text{date}_j$: Ngày diễn ra ca thi (định dạng `YYYY-MM-DD`).
  - $\text{start\_time}_j, \text{end\_time}_j$: Thời gian bắt đầu và kết thúc ca thi (định dạng `HH:MM`).
  - $\text{duration}_j$: Thời lượng làm bài (tính bằng phút, ví dụ: 60, 90, 120, 150 phút).
  - $\text{weekday}_j$: Thứ trong tuần (ví dụ: Thứ 2, Thứ 3,...).
  - $\text{campus}_j \in C$: Cơ sở tổ chức ca thi.
  - $\text{demand}_j$: Số lượng cán bộ yêu cầu cho ca thi $j$.

### 2.3. Tập hợp Cơ sở / Địa điểm Thi: $C$ (Campuses Set)
- **Ký hiệu toán học:** $C = \{\text{"Cơ sở 1"}, \text{"Cơ sở 2"}\}$ (hoặc viết tắt $C = \{\text{CS1}, \text{CS2}\}$).
- **Chỉ số phần tử:** $c \in C$.
- **Ý nghĩa:** Không gian địa lý các cơ sở đào tạo của nhà trường nơi diễn ra các ca thi:
  - **Cơ sở 1 (CS1):** 268 Lý Thường Kiệt, Quận 10, TP.HCM.
  - **Cơ sở 2 (CS2):** Khu đô thị ĐHQG-HCM, Dĩ An, Bình Dương.
- **Quy mô dữ liệu thực nghiệm:** $|C| = 2$.
- **Đặc trưng:** Hai cơ sở cách xa nhau về khoảng cách địa lý (~25 km), do đó một cán bộ không thể di chuyển tức thời giữa hai cơ sở trong cùng một khoảng thời gian ngắn; đồng thời cán bộ có xu hướng ưu tiên làm việc tại cơ sở gần nơi cư trú.

### 2.4. Các Tập hợp Phụ trợ (Derived / Auxiliary Sets)
- **Tập các cặp ca thi xung đột thời gian $\mathcal{O}$ (Overlap Session Pairs):**
  $$\mathcal{O} = \{(j, k) \in J \times J \mid j < k \land \text{Overlap}(j, k) = \text{True}\}$$
- **Tập ca thi diễn ra tại cơ sở $c \in C$:**
  $$J_c = \{j \in J \mid \text{campus}_j = c\}, \quad \text{sao cho } \bigcup_{c \in C} J_c = J \text{ và } J_{c_1} \cap J_{c_2} = \emptyset \; (\forall c_1 \neq c_2)$$

---

## 3. Định nghĩa các Tham số Mô hình (Parameters Definition)

Các tham số đầu vào được tính toán tiền xử lý từ dữ liệu thô và cấu hình bài toán:

### 3.1. Nhu cầu Nhân sự Ca thi: $\text{demand}_j$ ($d_j$)
- **Ký hiệu toán học:** $d_j$ hoặc $\text{demand}_j$, với mỗi $j \in J$.
- **Kiểu dữ liệu:** Số nguyên dương ($\mathbb{Z}^+$).
- **Ý nghĩa:** Số lượng cán bộ coi thi tối thiểu / chính xác bắt buộc phải bố trí để giám sát ca thi $j$.
- **Nguồn dữ liệu thực nghiệm:** Được xác định từ số lượng phòng thi / số lượt phân công trong dữ liệu lịch sử của ca $j$. Tổng nhu cầu trên toàn bộ kỳ thi:
  $$\sum_{j \in J} d_j = 769 \text{ lượt cán bộ coi thi}$$
- **Ràng buộc tương ứng trong mô hình:**
  $$\sum_{i \in I} x_{ij} = d_j, \quad \forall j \in J$$

### 3.2. Tính Khả dụng của Cán bộ: $\text{availability}_{ij}$ ($a_{ij}$)
- **Ký hiệu toán học:** $a_{ij}$ hoặc $\text{avail}_{ij}$, với mỗi $i \in I, j \in J$.
- **Kiểu dữ liệu:** Nhị phân ($a_{ij} \in \{0, 1\}$).
- **Ý nghĩa:** Thể hiện việc cán bộ $i$ có sẵn sàng / rảnh rỗi để nhận ca thi $j$ hay không:
  $$a_{ij} = \begin{cases} 1 & \text{nếu cán bộ } i \text{ khả dụng (rảnh) tại ca } j \\ 0 & \text{nếu cán bộ } i \text{ không khả dụng (bận: } \text{Busy}(i, j) = \text{True}) \end{cases}$$
- **Liên hệ với Module 1 (Logic):**
  Trong Module 1, quy tắc bất biến là $\text{Busy}(i, j) \implies \neg \text{Assign}(i, j)$. Khi chuyển sang ILP, tham số này trực tiếp giới hạn:
  $$x_{ij} \le a_{ij}, \quad \forall i \in I, \forall j \in J$$
  *(Trong cài đặt thực tế của solver, nếu $a_{ij} = 0$, ta có thể cố định $x_{ij} = 0$ hoặc loại bỏ hoàn toàn biến $x_{ij}$ khỏi bài toán để thu gọn không gian tìm kiếm).*

### 3.3. Quan hệ Trùng lặp Thời gian: $\text{overlap}_{jk}$ ($o_{jk}$)
- **Ký hiệu toán học:** $o_{jk}$ hoặc ma trận đối xứng $\mathbf{O} \in \{0, 1\}^{|J| \times |J|}$.
- **Kiểu dữ liệu:** Nhị phân ($o_{jk} \in \{0, 1\}$).
- **Định nghĩa toán học:** Cho hai ca thi $j, k \in J$ có khoảng thời gian lần lượt là $[s_j, e_j)$ và $[s_k, e_k)$ cùng ngày $\text{date}_j = \text{date}_k$:
  $$o_{jk} = \begin{cases} 1 & \text{nếu } j \neq k \land \max(s_j, s_k) < \min(e_j, e_k) \\ 0 & \text{ngược lại} \end{cases}$$
- **Tính chất toán học:**
  - Phi phản xạ (Irreflexive): $o_{jj} = 0, \quad \forall j \in J$.
  - Đối xứng (Symmetric): $o_{jk} = o_{kj}, \quad \forall j, k \in J$.
- **Ý nghĩa mô hình (No Double-Booking):**
  Một cán bộ không thể xuất hiện đồng thời tại hai ca thi có khoảng thời gian giao nhau:
  $$x_{ij} + x_{ik} \le 1, \quad \forall i \in I, \; \forall (j, k) \in J \times J \text{ với } o_{jk} = 1 \text{ và } j < k$$

### 3.4. Thuộc tính Cơ sở và Sở thích Địa điểm: $\text{campus}_j$, $\text{pref}_i$, $p_{ij}$
- **$\text{campus}_j \in C$:** Cơ sở tổ chức ca thi $j$. Có thể biểu diễn bằng ma trận chỉ thị vị trí:
  $$\text{loc}_{jc} = \begin{cases} 1 & \text{nếu ca } j \text{ diễn ra tại cơ sở } c \in C \\ 0 & \text{ngược lại} \end{cases}$$
- **$\text{pref}_i \in C$:** Cơ sở ưu tiên đã đăng ký của cán bộ $i$.
- **Ma trận phạt không đúng cơ sở ưu tiên $p_{ij}$ (Unfavorable Location Penalty Matrix):**
  $$p_{ij} = \begin{cases} 0 & \text{nếu } \text{campus}_j = \text{pref}_i \\ 1.0 & \text{nếu } \text{campus}_j \neq \text{pref}_i \end{cases}$$
- **Trọng số phạt sở thích địa điểm:** $w_{\text{location}} = 1.28$ (xác định từ W03-T2 thông qua seed nhóm `287892112`).
- **Tổng điểm phạt vị trí:**
  $$\text{Penalty}_{\text{location}} = w_{\text{location}} \cdot \sum_{i \in I} \sum_{j \in J} p_{ij} \cdot x_{ij}$$

### 3.5. Bảng Tổng hợp Tham số Mô hình

| Tên tham số | Ký hiệu | Kiểu dữ liệu | Miền giá trị | Ý nghĩa nghiệp vụ |
|---|:---:|:---:|:---:|---|
| **Demand** | $d_j$ | Integer | $\mathbb{Z}^+$ | Số cán bộ coi thi bắt buộc cho ca $j$ |
| **Availability** | $a_{ij}$ | Binary | $\{0, 1\}$ | Cán bộ $i$ rảnh ($1$) hay bận ($0$) ở ca $j$ |
| **Overlap** | $o_{jk}$ | Binary | $\{0, 1\}$ | Hai ca $j$ và $k$ có trùng giờ thi hay không |
| **Campus** | $\text{campus}_j$ | Categorical | $C$ | Cơ sở tổ chức ca thi $j$ (CS1 hoặc CS2) |
| **Preferred Campus** | $\text{pref}_i$ | Categorical | $C$ | Cơ sở mong muốn của cán bộ $i$ |
| **Location Penalty** | $p_{ij}$ | Continuous | $\{0.0, 1.0\}$ | Hệ số phạt nếu phân công trái cơ sở ưu tiên |
| **Soft Weight (Loc)** | $w_{\text{loc}}$ | Continuous | $\mathbb{R}^+$ ($1.28$) | Trọng số phạt vi phạm sở thích cơ sở trong hàm mục tiêu |

---

## 4. Định nghĩa các Biến Quyết định (Decision Variables)

Để xây dựng bài toán ILP, ba nhóm biến quyết định chính được định nghĩa rõ ràng về kiểu dữ liệu, cận chặn và ý nghĩa nghiệp vụ:

### 4.1. Biến Phân công Cán bộ: $x_{ij}$
- **Ký hiệu toán học:** $x_{ij}, \quad \forall i \in I, \; \forall j \in J$.
- **Kiểu dữ liệu (Variable Type): BINARY ($\{0, 1\}$ hoặc $\mathbb{B}$)**.
- **Miền giá trị:** $x_{ij} \in \{0, 1\}$.
- **Cận (Bounds):** $\text{LB} = 0, \; \text{UB} = 1$.
- **Số lượng biến:** $|I| \times |J| = 73 \times 65 = 4{,}745$ biến.
- **Ý nghĩa:**
  $$x_{ij} = \begin{cases} 1 & \text{nếu cán bộ } i \text{ được phân công coi thi ca } j \\ 0 & \text{nếu cán bộ } i \text{ không được phân công coi thi ca } j \end{cases}$$
- **Giải thích kiểu dữ liệu:** Đây là biến quyết định cốt lõi (decision variable). Bản chất của việc phân công là quyết định "có" hoặc "không", mang tính rời rạc tuyệt đối nên bắt buộc phải là biến **Binary**.

### 4.2. Biến Khối lượng Công việc (Workload): $w_i$
- **Ký hiệu toán học:** $w_i, \quad \forall i \in I$.
- **Kiểu dữ liệu (Variable Type): INTEGER ($\mathbb{Z}_{\ge 0}$)**.
- **Miền giá trị:** $w_i \in \{0, 1, 2, \dots, |J|\}$.
- **Cận (Bounds):** $\text{LB} = 0, \; \text{UB} = |J| = 65$ (hoặc cận thực tế $\text{UB} = \max_j d_j$).
- **Số lượng biến:** $|I| = 73$ biến.
- **Phương trình liên kết:**
  $$w_i = \sum_{j \in J} x_{ij}, \quad \forall i \in I$$
- **Ý nghĩa:** Tổng số ca thi mà cán bộ $i$ đảm nhận trong toàn bộ kỳ thi.
- **Giải thích kiểu dữ liệu:**
  - Về mặt bản chất toán học: $w_i$ là số lượng ca thi đếm được, là tổng các biến nhị phân $x_{ij}$, do đó $w_i$ là một đại lượng nguyên không âm (**Integer**).
  - Về mặt giải thuật tối ưu (Solver implementation): Khi $x_{ij} \in \{0, 1\}$, ràng buộc đẳng thức $w_i - \sum_{j \in J} x_{ij} = 0$ tự động ép $w_i$ nhận giá trị nguyên ở bất kỳ nghiệm nguyên nào của $x_{ij}$. Trong solver, ta có thể khai báo $w_i$ là **Integer** (đúng ngữ nghĩa) hoặc **Continuous** (để giảm kích thước không gian nhánh cây Branch & Bound mà không làm mất tính nguyên của nghiệm). Ở mức đặc tả mô hình, kiểu chuẩn tắc là **Integer**.

### 4.3. Biến Tải Tối đa (Maximum Load): $t$
- **Ký hiệu toán học:** $t$ (Minimax fairness auxiliary variable).
- **Kiểu dữ liệu (Variable Type): CONTINUOUS ($\mathbb{R}_{\ge 0}$) hoặc INTEGER ($\mathbb{Z}_{\ge 0}$)**.
- **Miền giá trị:** $t \in [0, |J|]$.
- **Cận (Bounds):** $\text{LB} = \lceil \frac{\sum_j d_j}{|I|} \rceil = \lceil \frac{769}{73} \rceil = 11, \; \text{UB} = |J| = 65$.
- **Số lượng biến:** $1$ biến đơn lẻ.
- **Hệ bất đẳng thức liên kết:**
  $$t \ge w_i, \quad \forall i \in I \iff t - \sum_{j \in J} x_{ij} \ge 0, \quad \forall i \in I$$
- **Ý nghĩa:** Biến chặn trên của khối lượng công việc của tất cả các cán bộ coi thi ($t \ge \max_{i \in I} w_i$).
- **Vai trò trong Hàm mục tiêu Min-Max:**
  Khi bài toán tối thiểu hóa $t$ ($\min t$), do ràng buộc $t \ge w_i$ với mọi $i$, nghiệm tối ưu của $t$ sẽ chính xác bằng tải lớn nhất:
  $$t^* = \max_{i \in I} w_i^*$$
  Việc này giúp tuyến tính hóa độ phân tán khối lượng công việc mà không làm bùng nổ hàm mục tiêu bậc hai (như phương sai $\sum (w_i - \bar{w})^2$), duy trì mô hình thuộc lớp bài toán quy hoạch nguyên tuyến tính (ILP).
- **Giải thích kiểu dữ liệu:**
  - Mặc dù giá trị tối ưu của $t$ tại nghiệm nguyên của bài toán sẽ là một số nguyên (do mọi $w_i \in \mathbb{Z}$), biến $t$ có thể được khai báo là **Continuous** ($\mathbb{R}_{\ge 0}$). Khai báo Continuous cho biến minimax là kỹ thuật tiêu chuẩn trong ILP vì:
    1. Giảm số lượng biến nguyên phải phân nhánh trong thuật toán Branch-and-Cut / Branch-and-Bound.
    2. Cải thiện tốc độ giải bài toán quy hoạch tuyến tính nới lỏng (LP relaxation) tại các nút của cây tìm kiếm.

---

## 5. Bảng Tổng hợp Phân loại Biến Quyết định

| Tên biến | Ký hiệu | Kiểu dữ liệu (Type) | Cận dưới (LB) | Cận trên (UB) | Số lượng biến | Mục đích trong mô hình |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **Assignment** | $x_{ij}$ | **Binary** | $0$ | $1$ | $4{,}745$ | Quyết định phân công cán bộ $i$ coi ca $j$ |
| **Workload** | $w_i$ | **Integer** | $0$ | $65$ | $73$ | Đếm tổng số ca thi của cán bộ $i$ |
| **Maximum Load** | $t$ | **Continuous** / **Integer** | $11$ | $65$ | $1$ | Đại diện cho tải cao nhất phục vụ Min-Max Fairness |

---

## 6. Mô hình Toán học Tổng quát (Mathematical Formulation)

Dựa trên các tập hợp, tham số và biến quyết định đã định nghĩa ở trên, mô hình ILP tổng thể cho Module 2 được thiết lập như sau:

### 6.1. Hàm Mục tiêu (Objective Function)
Kết hợp giữa tính công bằng tải (Min-Max Fairness) và giảm thiểu vi phạm sở thích địa điểm (Location Preference Penalty):

$$\min \quad Z = t + \lambda \sum_{i \in I} \sum_{j \in J} p_{ij} \cdot x_{ij}$$

Trong đó:
- $t$: Tải tối đa giữa các cán bộ (thành phần công bằng chính).
- $\lambda$: Trọng số cân bằng đa mục tiêu (ví dụ $\lambda = \frac{w_{\text{location}}}{|I| \cdot |J|} = \frac{1.28}{4745} \approx 0.00027$, nhằm đảm bảo ưu tiên bậc nhất là công bằng tải, sau đó mới tối ưu hóa địa điểm).

### 6.2. Các Ràng buộc Cứng (Hard Constraints)

1. **Ràng buộc Đáp ứng Đủ Sức chứa / Nhu cầu Ca thi (Demand Satisfaction):**
   Mỗi ca thi $j$ phải có chính xác $d_j$ cán bộ được phân công:
   $$\sum_{i \in I} x_{ij} = d_j, \quad \forall j \in J$$

2. **Ràng buộc Tính Khả dụng (Availability / Not Busy):**
   Cán bộ không thể được phân công vào ca thi mà họ bị bận ($a_{ij} = 0$):
   $$x_{ij} \le a_{ij}, \quad \forall i \in I, \forall j \in J$$

3. **Ràng buộc Chống Trùng Ca thi (No Double-Booking for Overlapping Shifts):**
   Một cán bộ không thể nhận hai ca thi có thời gian giao nhau:
   $$x_{ij} + x_{ik} \le 1, \quad \forall i \in I, \forall (j, k) \in J \times J \text{ sao cho } o_{jk} = 1 \text{ và } j < k$$

4. **Ràng buộc Xác định Workload:**
   Liên kết biến $w_i$ với các biến phân công $x_{ij}$:
   $$w_i = \sum_{j \in J} x_{ij}, \quad \forall i \in I$$

5. **Ràng buộc Tuyến tính hóa Min-Max Load:**
   Ép biến $t$ phải lớn hơn hoặc bằng tải của mọi cán bộ:
   $$t \ge w_i, \quad \forall i \in I \iff t - \sum_{j \in J} x_{ij} \ge 0, \quad \forall i \in I$$

### 6.3. Ràng buộc Miền Giá trị Biến (Domain Constraints)
$$x_{ij} \in \{0, 1\}, \quad \forall i \in I, \forall j \in J$$
$$w_i \in \mathbb{Z}_{\ge 0}, \quad \forall i \in I$$
$$t \ge 0 \quad (t \in \mathbb{R}_{\ge 0})$$

---

## 7. Mối liên kết với Module 1 và Kế hoạch Tích hợp

- **Kế thừa từ Module 1:**
  - Logic mệnh đề $\text{Assign}(i, j) \leftrightarrow x_{ij} = 1$.
  - Mệnh đề $\text{Busy}(i, j) \implies \neg \text{Assign}(i, j)$ được chuyển hóa thành $x_{ij} \le a_{ij}$.
  - Ràng buộc trùng ca $\forall i \forall j \forall k (\text{Overlap}(j, k) \land \text{Assign}(i, j) \implies \neg \text{Assign}(i, k))$ chuyển hóa trực tiếp thành bất đẳng thức $x_{ij} + x_{ik} \le 1$.
  - Ràng buộc sức chứa chính xác $k$ người ($\text{Exactly-k}$) trong Module 1 gây bùng nổ số lượng mệnh đề CNF (binomial clause explosion $\binom{n}{k}$), nhưng trong Module 2 được biểu diễn gọn gàng bằng duy nhất một phương trình tuyến tính $\sum_i x_{ij} = d_j$.
- **Chuyển giao cho các Task tiếp theo của Module 2:**
  - `W03-T4`: Cài đặt các ràng buộc cứng (Hard Constraints) vào bộ giải PuLP / OR-Tools dựa trên các biến từ `m2_ilp/variables.py`.
  - `W03-T5`: Cài đặt hàm mục tiêu (Min-Max fairness + penalty), giải bài toán và đánh giá hiệu năng so với baseline.
