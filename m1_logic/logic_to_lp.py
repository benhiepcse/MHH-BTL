def availability_constraint(i, j):
    # Busy(i,j) -> not Assign(i,j)
    return f"x_{i}_{j} = 0"


def overlap_constraint(i, j, k):
    # not Assign(i,j) OR not Assign(i,k)
    return f"x_{i}_{j} + x_{i}_{k} <= 1"

def capacity_constraint(shift_j, invigilators, required_k):
    """
    Translates exact shift capacity into an LP equality constraint.
    In CNF: Requires combination of at-least-k and at-most-k (binomial clause explosion).
    In LP:  Represented compactly as a single linear equality: sum(x_ij) = k.
    """
    terms = [f"x_{i}_{shift_j}" for i in invigilators]
    return f"{' + '.join(terms)} = {required_k}"

def at_most_k_constraint(shift_j, invigilators, max_k):
    """
    Translates at-most-k invigilators constraint into an LP inequality: sum(x_ij) <= max_k.
    """
    terms = [f"x_{i}_{shift_j}" for i in invigilators]
    return f"{' + '.join(terms)} <= {max_k}"

"""
Logic-to-LP Bridge (CO2011 - Requirement 1.3)
Translates First-Order / CNF propositional constraints into 0/1 Linear Programming format.
"""

from typing import List

class LogicToLPBridge:
    def __init__(self):
        pass

    def clause_to_linear(self, positive_literals: List[str], negative_literals: List[str]) -> str:
        """
        Translates a CNF disjunctive clause into a 0/1 linear inequality:
        (p1 v p2 v ... v ~n1 v ~n2 ...) <=> sum(p) - sum(n) >= 1 - len(negatives)
        """
        terms = [f"+ {p}" for p in positive_literals] + [f"- {n}" for n in negative_literals]
        rhs = 1 - len(negative_literals)
        expr = " ".join(terms).strip()
        if expr.startswith("+ "):
            expr = expr[2:]
        return f"{expr} >= {rhs}"

    def availability_to_lp(self, invigilator_id: str, shift_id: str, is_busy: bool) -> str:
        """Busy(i, j) -> not Assign(i, j) <=> x_i_j = 0 when busy"""
        return f"x_{invigilator_id}_{shift_id} = 0" if is_busy else f"x_{invigilator_id}_{shift_id} <= 1"

    def no_double_booking_to_lp(self, invigilator_id: str, shift_j: str, shift_k: str) -> str:
        """Overlap(j, k) -> not (Assign(i, j) and Assign(i, k)) <=> x_i_j + x_i_k <= 1"""
        return f"x_{invigilator_id}_{shift_j} + x_{invigilator_id}_{shift_k} <= 1"

    def exact_capacity_to_lp(self, shift_id: str, invigilator_ids: List[str], capacity: int) -> str:
        """Exact capacity: sum(x_i_j) = capacity"""
        terms = [f"x_{i}_{shift_id}" for i in invigilator_ids]
        return f"{' + '.join(terms)} = {capacity}"

    def at_most_k_to_lp(self, shift_id: str, invigilator_ids: List[str], max_k: int) -> str:
        """sum(x_i_j) <= max_k"""
        terms = [f"x_{i}_{shift_id}" for i in invigilator_ids]
        return f"{' + '.join(terms)} <= {max_k}"

    def generate_toy_lp_model(self) -> List[str]:
        constraints = [
            "# Availability Constraints",
            self.availability_to_lp("CB1", "Morning", is_busy=True),
            "\n# Shift Capacity Constraints (Exact = 2)",
            self.exact_capacity_to_lp("Morning", ["CB1", "CB2", "CB3"], 2),
            self.exact_capacity_to_lp("Afternoon", ["CB1", "CB2", "CB3"], 2)
        ]
        return constraints

if __name__ == "__main__":
    import json
    import os

    bridge = LogicToLPBridge()
    constraints = bridge.generate_toy_lp_model()
    
    print("=== Logic-to-LP Constraints for Toy Instance ===")
    for c in constraints:
        print(c)
    
    # Xuất ra file JSON đầu ra theo yêu cầu của nhóm
    output_dir = "data/generated"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "logic_to_lp.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "module": "1.3",
            "description": "Linear 0/1 constraints generated from logic bridge for toy instance",
            "constraints": [c for c in constraints if not c.startswith("#") and c.strip()]
        }, f, indent=2)
        
    print(f"\n[SUCCESS] Exported LP constraints to: {output_path}")