def divide(a, b):
    return a / b


def percent(part, whole):
    return divide(part, whole) * 100


def clamp(x, lo, hi):
    return max(lo, min(x, hi))
