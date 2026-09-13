# m1_logic — see the assignment brief section for this module.


## Logic-to-LP Bridge (M1.3)
This module begins translating the hard constraints defined in the logic specification into linear constraints over binary assignment variables
### Basic Constraints

- Availability constraint: If invigilator `i` busy during session `j`, they cannot be assigned to that session
- Overlap constraint: If sessions `j` and `k` overlap, the same invigilator cannot be assigned to both sessions at the same time
These constraints will later be extended and used as part of the ILP model in Module 2