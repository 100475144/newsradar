"""Proponer entre 3 y 10 sinónimos o palabras relacionadas para ampliar la alerta."""

from collections import OrderedDict

# Diccionario amplio de términos relacionados organizado por dominio.
# Para cualquier keyword, se busca coincidencia parcial en las claves.
RELATED_TERMS: dict[str, list[str]] = {
    # Technology / Science
    "bitcoin": ["btc", "cryptocurrency", "crypto", "blockchain", "digital currency", "mining", "ethereum"],
    "crypto": ["cryptocurrency", "bitcoin", "blockchain", "defi", "digital assets", "web3"],
    "ai": ["artificial intelligence", "machine learning", "deep learning", "llm", "neural networks", "automation"],
    "artificial intelligence": ["ai", "machine learning", "deep learning", "neural networks", "chatbot", "automation"],
    "machine learning": ["ai", "deep learning", "neural networks", "data science", "algorithms", "model training"],
    "cybersecurity": ["hacking", "data breach", "malware", "ransomware", "phishing", "encryption"],
    "5g": ["telecommunications", "mobile network", "wireless", "spectrum", "connectivity"],
    "quantum": ["quantum computing", "qubit", "superposition", "quantum mechanics", "encryption"],
    "robotics": ["automation", "drones", "autonomous", "manufacturing", "ai"],
    "software": ["programming", "development", "code", "engineering", "applications"],
    "cloud": ["cloud computing", "aws", "azure", "saas", "infrastructure"],
    "startup": ["entrepreneurship", "venture capital", "funding", "innovation", "tech company"],
    # Health
    "covid": ["coronavirus", "pandemic", "sars-cov-2", "vaccination", "public health", "epidemic"],
    "vaccine": ["vaccination", "immunization", "booster", "pandemic", "public health"],
    "mental health": ["depression", "anxiety", "therapy", "wellbeing", "psychology", "stress"],
    "cancer": ["oncology", "tumor", "chemotherapy", "diagnosis", "treatment", "research"],
    "diabetes": ["insulin", "blood sugar", "glucose", "chronic disease", "metabolism"],
    "nutrition": ["diet", "obesity", "food", "health", "vitamins", "supplements"],
    # Politics / Society
    "elections": ["voting", "polls", "campaign", "candidates", "democracy", "ballots"],
    "climate": ["climate change", "global warming", "emissions", "carbon", "environment", "sustainability"],
    "immigration": ["migration", "refugees", "asylum", "border", "visa", "deportation"],
    "war": ["conflict", "military", "troops", "ceasefire", "peace", "invasion"],
    "terrorism": ["extremism", "attack", "security", "radicalization", "counterterrorism"],
    "human rights": ["civil rights", "freedom", "equality", "discrimination", "justice"],
    "corruption": ["bribery", "fraud", "scandal", "transparency", "accountability"],
    # Economy / Business
    "inflation": ["prices", "cost of living", "monetary policy", "interest rates", "economy"],
    "recession": ["economic downturn", "gdp", "unemployment", "crisis", "contraction"],
    "stock market": ["shares", "trading", "wall street", "dow jones", "nasdaq", "investor"],
    "oil": ["petroleum", "opec", "crude", "energy", "barrel", "fuel"],
    "trade": ["tariffs", "exports", "imports", "sanctions", "commerce", "supply chain"],
    "real estate": ["housing", "mortgage", "property", "rent", "construction"],
    # Environment
    "pollution": ["emissions", "contamination", "air quality", "waste", "toxic"],
    "deforestation": ["forests", "amazon", "logging", "biodiversity", "conservation"],
    "renewable energy": ["solar", "wind", "clean energy", "sustainability", "green"],
    "earthquake": ["seismic", "tremor", "magnitude", "tectonic", "disaster"],
    "flood": ["flooding", "hurricane", "storm", "rain", "disaster", "evacuation"],
    # Sports
    "football": ["soccer", "fifa", "premier league", "champions league", "match", "goal"],
    "olympics": ["olympic games", "medal", "athlete", "ioc", "competition", "sport"],
    "tennis": ["grand slam", "wimbledon", "atp", "wta", "match", "tournament"],
    "basketball": ["nba", "court", "playoffs", "dunk", "league"],
    "formula 1": ["f1", "grand prix", "racing", "circuit", "driver", "fia"],
    # Arts / Culture
    "cinema": ["film", "movie", "director", "oscar", "box office", "premiere"],
    "music": ["concert", "album", "artist", "grammy", "streaming", "song"],
    "literature": ["book", "novel", "author", "publisher", "bestseller", "reading"],
    "theater": ["theatre", "play", "musical", "stage", "performance", "broadway"],
    # Education
    "university": ["college", "higher education", "campus", "degree", "academic", "research"],
    "education": ["school", "learning", "teaching", "curriculum", "students", "teachers"],
}


def suggest_expanded_keywords(keyword: str) -> list[str]:
    """Return 3-10 related terms for the given keyword."""
    keyword = keyword.strip().lower()

    # Exact match first
    suggestions = RELATED_TERMS.get(keyword, [])

    # Partial match if no exact match
    if not suggestions:
        for key, terms in RELATED_TERMS.items():
            if keyword in key or key in keyword:
                suggestions = terms
                break

    # Fallback: generate generic related terms
    if not suggestions:
        base = keyword.replace("-", " ").replace("_", " ")
        suggestions = [
            f"{base} news",
            f"{base} latest",
            f"{base} updates",
            f"{base} report",
            f"{base} analysis",
        ]

    unique = list(OrderedDict.fromkeys(item.strip() for item in suggestions if item.strip()))
    # Ensure between 3 and 10
    return unique[:10]
