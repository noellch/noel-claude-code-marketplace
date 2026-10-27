def divide(a, b):
    if b == 0:
        raise ValueError("whole must not be zero")
    return a / b


def percent(part, whole):
    return round(divide(part, whole) * 100, 2)


def clamp(x, lo, hi):
    return max(lo, min(x, hi))
