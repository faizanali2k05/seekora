from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParsedPage:
    url: str
    title: str
    content: str
    content_hash: str
