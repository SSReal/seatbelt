from typing import Annotated


def sample_function(name: Annotated[str, "The name of the person to greet"]):
    """Greet someone by name."""
    return f"Hello, {name}!"
