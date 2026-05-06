"""IPTC Media Topics — first-level categories.

Reference: https://cv.iptc.org/newscodes/mediatopic/

Cada categoría se identifica por su **código IPTC oficial de 8 dígitos**
(``"01000000"``…``"17000000"``) y un **nombre canónico en español**.

Estos son los 17 Media Topics de primer nivel. La batería de smoke tests
del aula global (SMOKE-005) los espera presentes con este formato exacto
de ``id`` + ``name``.
"""

# code (str, 8 dígitos) → nombre español canónico (lowercase, como aparece
# en los smoke tests del profesor).
IPTC_CATEGORIES: dict[str, str] = {
    "01000000": "artes, cultura, entretenimiento y medios",
    "02000000": "policía y justicia",
    "03000000": "catástrofes y accidentes",
    "04000000": "economía, negocios y finanzas",
    "05000000": "educación",
    "06000000": "medio ambiente",
    "07000000": "salud",
    "08000000": "interés humano, animales, insólito",
    "09000000": "mano de obra",
    "10000000": "estilo de vida y tiempo libre",
    "11000000": "política",
    "12000000": "religión y creencias",
    "13000000": "ciencia y tecnología",
    "14000000": "sociedad",
    "15000000": "deportes",
    "16000000": "conflictos, guerras y paz",
    "17000000": "tiempo (meteorología)",
}

IPTC_CATEGORY_CODES: list[str] = list(IPTC_CATEGORIES.keys())


# Compatibilidad con el formato snake_case antiguo. Se usa para migrar
# datos existentes y aceptar payloads heredados durante la transición.
LEGACY_TO_OFFICIAL: dict[str, str] = {
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
}

# Categoría por defecto cuando se descarta ``uncategorized`` (SMOKE-004).
DEFAULT_FALLBACK_CODE = "14000000"


def _normalize_code(code: str | None) -> str:
    return (code or "").strip().lower()


def to_official_code(code: str | None) -> str:
    """Devuelve el código IPTC oficial (8 dígitos) para ``code``.

    Acepta tanto el código oficial como los códigos legacy snake_case
    o nombres en español. Si no hay match devuelve el input normalizado.
    """
    norm = _normalize_code(code)
    if norm in IPTC_CATEGORIES:
        return norm
    if norm in LEGACY_TO_OFFICIAL:
        return LEGACY_TO_OFFICIAL[norm]
    # match por nombre español
    for official, label in IPTC_CATEGORIES.items():
        if norm == label:
            return official
    return norm


def is_valid_iptc_category(code: str | None) -> bool:
    norm = _normalize_code(code)
    if norm in IPTC_CATEGORIES or norm in LEGACY_TO_OFFICIAL:
        return True
    return any(norm == label for label in IPTC_CATEGORIES.values())


def get_iptc_label(code: str | None) -> str:
    norm = _normalize_code(code)
    if norm in IPTC_CATEGORIES:
        return IPTC_CATEGORIES[norm]
    legacy = LEGACY_TO_OFFICIAL.get(norm)
    if legacy:
        return IPTC_CATEGORIES[legacy]
    return code or ""
