# Predicate Specification
## Sets & Domains
### Sets
- $I$: set of invigilators, who are responsible for supervising the exam at the specific shifts
- $J$: set of shifts
- $C$: $\\{Cơ \\, sở \\, 1, Cơ \\, sở \\, 2\\}$
### Domains
- $\\{i_1, i_2, \dots, i_n\\} \in I$: invigilators parameters  
- $\\{j_1, j_2, \dots, j_m\\} \in J$: shifts parameters  
- $\\{c_1, c_2, \dots, c_p\\} \in C$: campuses parameters  
- $r(j)$: the required number of invigilators for shift $j$
- **duration(j)**: the duration of shift $j$
- **start(j)**: the starting time of shift $j$
- **date(j)**: the date of shift $j$
## Predicates
- **Assign(i, j)** - $i \in I$, $j \in J$. $Assign(i, j) \in {\text{True}, \text{False}}$: Evaluates to $\text{True}$ if invigilator $i$ is assigned at shift $j$, and $\text{False}$ if invigilator $i$ isn't assigned at shift $j$ 
- **Busy(i, j)** - parameters: $i \in I$, $j \in J$. $Busy(i, j) \in {\text{True}, \text{False}}$: Evaluates to $\text{True}$ if invigilator $i$ is busy at shift $j$, and $\text{False}$ if invigilator $i$ is's busy at shift $j$. 
- **Overlap(j, k)** - parameters: $j \in J$, $k \in J$. $Overlap(j, k) \in {\text{True}, \text{False}}$: Evaluates to $\text{True}$ if shift $j$ and shift $k$ are overlapped to each other, and $\text{False}$ if shift $j$ and shift $k$ aren't overlapped to each other.
  * Overlap is symmetric and irreflexive
    * Symmetric: $\forall j, k \in J (Overlap(j, k) \leftrightarrow Overlap(k, j))$
    * Irreflexive: $\forall j \in J (\neg Overlap(j, j))$ 
- **AtCampus(j, c)** - parameters: $j \in J$, $c \in C$. $AtCampus(j, c) \in {\text{True}, \text{False}}$: Evaluates to $\text{True}$ if shift $j$ is occured at campus $c$, and $\text{False}$ if shift $j$ isn't occured at campus $c$.
- **Prefer(i, c)** - parameters: $i \in I$, $c \in C$. $Prefer(i, c) \in {\text{True}, \text{False}}$: Evaluates to $\text{True}$ if invigilator $i$ is preferred to work at campus $c$, and ${\text{False}}$ if invigilator $i$ isn't preferred working at campus $c$.
## Hard regulations  
- **No double-booking**: $\forall i \in I, \forall j, k \in J ((j \neq k) \land Assign(i, j) \land Overlap(j, k) \rightarrow \neg Assign(i, k))$
  * Meaning: If an invigilator $i$ is assigned to shift $j$, shift $j$ and shift $k$ are overlapped to each other (shift $j$ and shift $k$ are different from each other), then invigilator $i$ can't be assigned to shift $k$
- **Availability**: $\forall i \in I, \forall j \in J (Busy(i, j) \rightarrow \neg Assign(i, j))$
  * Meaning: If an invigilator $i$ is busy at shift $j$, then invigilator $i$ can't be assigned at shift $j$
- **Capacity**: For every shift $j$, exactly $r(j)$ invigilators are assigned to shift $j$
  * I separate "Exact Capacity of $r(j)$" into two parts: "At least $r(j)$ invigilators" and "At most $r(j)$ invigilators"  
  * **At least $r(j)$ invigilators**: $$\forall j \in J, \exists i_1, i_2, \dots, i_{r(j)} \in I \left( \left( \bigwedge_{1 \le a < b \le  {r(j)}} i_a \neq i_b \right) \land \left( \bigwedge_{m=1}^{r(j)} Assign(i_m, j) \right) \right)$$  
    * Meaning: There exist $r(j)$ distinct invigilators who are assigned to shift $j$  
  * **At most $r(j)$ invigilators**: $$\forall j \in J, \forall i_1, i_2, \dots, i_{r(j)+1} \in I \left( \left( \bigwedge_{m=1}^{r(j)+1} Assign(i_m, j) \right) \rightarrow \left( \bigvee_{1 \le a < b \le {r(j)+1}} i_a = i_b \right) \right)$$  
    * Meaning: If you pick any $r(j) + 1$ invigilators who are assigned to shift $j$, at least two of them must actually be the same person.
## Formal Syntax Rules  
### Operator and Expression Grammar  
- **Binary Operators** ($\land$, $\lor$, $\rightarrow$, $\leftrightarrow$, $=$, $!=$):  
  * Must be preceded by a term/predicate closing or closing parenthesis ')'.  
  * Must be followed by a term/predicate opening, opening parenthesis '(', or a unary operator.
- **Unary Operators** ('NOT', $\neg$):
  * Cannot be followed immediately by a binary operator or a closing parenthesis.
- **Quantifiers** ($\forall$, $\exists$):
  * Must be followed by a valid domain variable.
  * May include an optimal domain constraint ($\in I$).  

