from dataclasses import dataclass
from typing import Any

@dataclass
class Problem:
    problem_id: str
    source: str
    title: str
    difficulty: str
    url: str
    topics: list[str]
    metadata: dict[str, Any]