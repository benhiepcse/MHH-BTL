# Logic-to-LP Mapping Table (Requirement 1.3)

## 1. Mathematical Transformation Principles
All Boolean assignment literals $x_{ij} = Assign(i, j) \in \{0, 1\}$ are systematically mapped to linear (in)equalities:
- Positive literal $x \implies x \in \{0, 1\}$
- Negative literal $\neg x \implies 1 - x$
- General clause: $\bigvee_{p \in P} p \vee \bigvee_{n \in N} \neg n \implies \sum_{p \in P} p - \sum_{n \in N} n \ge 1 - |N|$

---

## 2. Core Rule Mapping Table

| Quy tắc (Rule Name) | Đặc tả Logic vị từ (FOL) | Dạng chuẩn hội (CNF) | Ràng buộc Tuyến tính nguyên (0/1 LP) | Đánh giá độ phức tạp |
| :--- | :--- | :--- | :--- | :--- |
| **Tính khả dụng** *(Availability)* | $\forall i, \forall j: Busy(i, j) \to \neg Assign(i, j)$ | $(\neg x_{ij})$ với mọi $(i, j)$ bận | $x_{ij} = 0$ | $1 \text{ clause} \iff 1 \text{ đẳng thức}$. |
| **Không trùng ca** *(No double-booking)* | $\forall i, \forall j \ne k: Overlap(j, k) \wedge Assign(i, j) \to \neg Assign(i, k)$ | $(\neg x_{ij} \vee \neg x_{ik})$ khi $Overlap(j, k) = 1$ | $x_{ij} + x_{ik} \le 1$ | $1 \text{ clause} \iff 1 \text{ BĐT}$. $\mathcal{O}(\|I\| \cdot \|J\|^2)$. |
| **Sức chứa đúng $k$** *(Exact Capacity $= k$)* | $\forall j: \exists^{=k} i \in I: Assign(i, j)$ | Tách thành At-least-$k$ và At-most-$k$ | $\sum_{i \in I} x_{ij} = k$ | **CNF bùng nổ tổ hợp** ($\binom{n}{k+1}$ clauses). **LP chỉ cần 1 phương trình**. |
| **Tối đa $k$ ca** *(At-most-$k$ load)* | $\forall i: \sum_{j} Assign(i, j) \le k$ | Binomial encoding: $\bigwedge_{S \subseteq J, \|S\|=k+1} \left(\bigvee_{j \in S} \neg x_{ij}\right)$ | $\sum_{j \in J} x_{ij} \le k$ | **CNF**: $\binom{\|J\|}{k+1}$ clauses. **LP**: 1 BĐT duy nhất. |

---

## 3. Clause Explosion vs. Linear Formulation Analysis
Khi quy mô bài toán tăng lên (ví dụ $n = 100$ cán bộ, ca thi cần $k = 2$ người):
- **Trong CNF**: Ràng buộc at-most-2 dạng binomial sinh ra $\binom{100}{3} = 161,700$ clauses cho mỗi ca thi.
- **Trong LP/ILP**: Thể hiện trực tiếp bằng một phương trình tuyến tính duy nhất: $\sum_{i=1}^{100} x_{ij} = 2$.
=> **Kết luận**: Ràng buộc đếm (cardinality constraints) đưa vào ILP tự nhiên và gọn hơn rất nhiều so với biểu diễn CNF thuần túy.