def availability_constraint(i, j):
    # Busy(i,j) -> not Assign(i,j)
    return f"x_{i}_{j} = 0"


def overlap_constraint(i, j, k):
    # not Assign(i,j) OR not Assign(i,k)
    return f"x_{i}_{j} + x_{i}_{k} <= 1"