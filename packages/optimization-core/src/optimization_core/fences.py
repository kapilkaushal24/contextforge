import re

FENCE_RE = re.compile(r"(```.*?```)", re.DOTALL)


def is_fenced_block(segment: str) -> bool:
    return segment.startswith("```") and segment.endswith("```") and len(segment) >= 6
