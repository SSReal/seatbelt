def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


def subtract(a: int, b: int) -> int:
    """Subtract the second number from the first."""
    return a - b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b


def divide(a: int, b: int) -> float:
    """Divide the first number by the second."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b
