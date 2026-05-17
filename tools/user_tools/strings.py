import json
from typing import Annotated


def find_occurrences_in_string(
    string: Annotated[str, "The string to find the substrings in"],
    substring: Annotated[str, "The substring to find in the string"],
):
    """Find all occurrences of a substring in a string and return their indices."""
    indices = []
    start = 0
    while True:
        index = string.find(substring, start)
        if index == -1:
            break
        indices.append(index)
        start = index + len(substring)
    if len(indices) == 0:
        return "No occurrences found."
    return json.dumps(indices)
