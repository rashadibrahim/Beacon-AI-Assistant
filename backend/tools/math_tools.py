"""Mathematical operation tools."""
from langchain.tools import tool


@tool
def add_numbers(x: float, y: float) -> float:
    """Add two numbers together."""
    return x + y


@tool
def multiply_numbers(x: float, y: float) -> float:
    """Multiply two numbers together."""
    return x * y


@tool
def subtract_numbers(x: float, y: float) -> float:
    """Subtract two numbers."""
    return x - y


@tool
def divide_numbers(x: float, y: float) -> float:
    """Divide two numbers."""
    return x / y
