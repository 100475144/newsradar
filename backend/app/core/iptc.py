"""IPTC Media Topics — first-level categories.

Reference: https://cv.iptc.org/newscodes/mediatopic/
Only the 17 top-level subjects are included.
"""

IPTC_CATEGORIES: dict[str, str] = {
    "01000000": "Artes, cultura, entretenimiento y medios",
    "02000000": "Policía y justicia",
    "03000000": "Catástrofes y accidentes",
    "04000000": "Economía, negocios y finanzas",
    "05000000": "Educación",
    "06000000": "Medio ambiente",
    "07000000": "Salud",
    "08000000": "Interés humano, animales, insólito",
    "09000000": "Mano de obra",
    "10000000": "Estilo de vida y tiempo libre",
    "11000000": "Política",
    "11110000": "Sucesos",
    "12000000": "Religión y culto",
    "13000000": "Ciencia y tecnología",
    "14000000": "Sociedad",
    "15000000": "Deporte",
    "16000000": "Conflicto, guerra y paz",
    "17000000": "Meteorología",
}

# Mapping from legacy English slug to numeric IPTC code (used by seed_sources).
_LEGACY_TO_CODE: dict[str, str] = {
    "arts_culture_entertainment": "01000000",
    "crime_law_justice": "02000000",
    "disaster_accident": "03000000",
    "economy_business_finance": "04000000",
    "education": "05000000",
    "environment": "06000000",
    "health": "07000000",
    "human_interest": "08000000",
    "labour": "09000000",
    "lifestyle_leisure": "10000000",
    "politics": "11000000",
    "religion_belief": "12000000",
    "science_technology": "13000000",
    "society": "14000000",
    "sport": "15000000",
    "conflict_war_peace": "16000000",
    "weather": "17000000",
    "sucesos": "11110000",
}

IPTC_CATEGORY_CODES: list[str] = list(IPTC_CATEGORIES.keys())

# Set of valid category names (lowercased) for closed catalog enforcement.
IPTC_VALID_NAMES: set[str] = {name.lower() for name in IPTC_CATEGORIES.values()}


def legacy_code_to_iptc(legacy: str) -> str:
    """Convert a legacy English slug to the numeric IPTC code."""
    return _LEGACY_TO_CODE.get(legacy.strip().lower(), legacy)


def is_valid_iptc_category(code: str) -> bool:
    return code in IPTC_CATEGORIES


def is_valid_iptc_name(name: str) -> bool:
    """Check if a category name belongs to the closed IPTC catalog."""
    return name.strip().lower() in IPTC_VALID_NAMES


def get_iptc_label(code: str) -> str:
    return IPTC_CATEGORIES.get(code, code)
