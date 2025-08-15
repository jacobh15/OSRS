import numpy as np
from scipy.stats import multinomial


def _valid(m, t, i, j, c, remaining):
    if remaining > 0:
        if i == j:
            yield from _valid(m, t, i, j + 1, c, remaining)
        elif j < len(c):
            for allocate in range(remaining + 1):
                c[j] += allocate
                yield from _valid(m, t, i, j + 1, c, remaining - allocate)
                c[j] -= allocate
    else:
        yield c.copy()


def valid(m, t, i):
    c = np.zeros(len(t) + 1, dtype=int)
    c[:-1] = t
    c[i] -= 1
    remaining = m - 1 - np.sum(c)
    
    yield from _valid(m, t, i, 0, c, remaining)


def prob(m, t, p):
    s = 0
    for i in range(len(t)):
        term = 0
        for c in valid(m, t, i):
            term += multinomial.pmf(c, m - 1, p)
        s += p[i] * term
    return s
