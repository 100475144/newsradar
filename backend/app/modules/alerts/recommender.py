"""Proponer sugerencias para ampliar la alerta"""

from collections import OrderedDict


RELATED_TERMS = {
    "bitcoin": [
        "btc",
        "cryptocurrency",
        "crypto",
        "blockchain",
        "digital currency",
    ],
    "ai": [
        "artificial intelligence",
        "machine learning",
        "llm",
        "automation",
        "neural networks",
    ],
    "covid": [
        "coronavirus",
        "pandemic",
        "public health",
        "vaccination",
        "epidemic",
    ],
}


def suggest_expanded_keywords(keyword: str) -> list[str]:
    keyword = keyword.strip().lower()

    suggestions = RELATED_TERMS.get(keyword, [])

    if not suggestions:
        base = keyword.replace("-", " ").replace("_", " ")
        candidates = [
            f"{base} news",
            f"{base} updates",
            f"{base} topic",
        ]
        suggestions = candidates

    unique = list(OrderedDict.fromkeys(item.strip() for item in suggestions if item.strip()))
    return unique[:10]
