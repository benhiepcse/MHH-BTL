# Predicate Specification
## Sets/Domains
- $I$: invigilators, who are responsible for supervising the exam at the specific shifts
- $J$: shifts
- $C$: campus
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
- **Capacity**: I separate "Exact Capacity of $k$" into two parts: "At least $k$ invigilators" and "At most $k$ invigilators"  
  * **At least $k$ invigilators**: $$\forall j \in J, \exists i_1, i_2, \dots, i_k \in I \left( \left( \bigwedge_{1 \le a < b \le k} i_a \neq i_b \right) \land \left( \bigwedge_{m=1}^{k} Assign(i_m, j) \right) \right)$$  
    * Meaning: There exist $k$ distinct invigilators who are assigned to shift $j$  
  * **At most $k$ invigilators**: $$\forall j \in J, \forall i_1, i_2, \dots, i_{k+1} \in I \left( \left( \bigwedge_{m=1}^{k+1} Assign(i_m, j) \right) \rightarrow \left( \bigvee_{1 \le a < b \le k+1} i_a = i_b \right) \right)$$  
    * Meaning: If you pick any $k + 1$ invigilators who are assigned to shift $j$, at least two of them must actually be the same person. 

