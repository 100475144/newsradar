"""IPTC Media Topics — first-level categories.

Reference: https://cv.iptc.org/newscodes/mediatopic/
Only the 17 top-level subjects are included.
"""

IPTC_CATEGORIES: dict[str, str] = {
    "arts_culture_entertainment": "Arts, Culture and Entertainment",
    "crime_law_justice": "Crime, Law and Justice",
    "disaster_accident": "Disaster and Accident",
    "economy_business_finance": "Economy, Business and Finance",
    "education": "Education",
    "environment": "Environment",
    "health": "Health",
    "human_interest": "Human Interest",
    "labour": "Labour",
    "lifestyle_leisure": "Lifestyle and Leisure",
    "politics": "Politics",
    "religion_belief": "Religion and Belief",
    "science_technology": "Science and Technology",
    "society": "Society",
    "sport": "Sport",
    "conflict_war_peace": "Conflict, War and Peace",
    "weather": "Weather",
}

IPTC_CATEGORY_CODES: list[str] = list(IPTC_CATEGORIES.keys())


def is_valid_iptc_category(code: str) -> bool:
    return code in IPTC_CATEGORIES


def get_iptc_label(code: str) -> str:
    return IPTC_CATEGORIES.get(code, code)
