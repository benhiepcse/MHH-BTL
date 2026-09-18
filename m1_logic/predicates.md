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
- **Prefer(i, c)** - parameters: $i \in I$, $c \in C$. $Prefer(i, c) \in \\{\text{True}, \text{False}\\}$: Evaluates to $\text{True}$ if invigilator $i$ is preferred to work at campus $c$, and ${\text{False}}$ if invigilator $i$ isn't preferred working at campus $c$.
## Hard regulations  
- **No double-booking**:  
  * **First - order formula**:
        $\forall i \in I, \forall j, k \in J ((j \neq k) \land Assign(i, j) \land Overlap(j, k) \rightarrow \neg Assign(i, k))$
  * **Meaning**: If an invigilator $i$ is assigned to shift $j$, shift $j$ and shift $k$ are overlapped to each other (shift $j$ and shift $k$ are different from each other), then invigilator $i$ can't be assigned to shift $k$
- **Availability**:  
  * **First-order formula**:
        $\forall i \in I, \forall j \in J (Busy(i, j) \rightarrow \neg Assign(i, j))$
  * **Meaning**: If an invigilator $i$ is busy at shift $j$, then invigilator $i$ can't be assigned at shift $j$
- **Capacity**:
  * **First-order formula**:
       $\forall j \in J |\\{i \in I : Assign(i, j)\\}| = r(j)$.
  * **Meaning**: For every shift $j$, the number of invigilators $i$ assigned to that shift is exactly $r(j)$.  
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

