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