from dataclasses import dataclass

@dataclass
class Problem:
    problem_id: str #problem_id
    source: str
    title: str
    difficulty: str
    url: str
    topics: list[str]
    metadata: dict