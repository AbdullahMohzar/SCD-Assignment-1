import re
from app.providers.triage.base import TriageResult
from app.schemas.common import Category, Priority

# Added regional colloquial keywords for Pakistani municipal triage

class RuleBasedTriage:
    """Deterministic keyword fallback triage provider.

    Always available, never makes network calls, never fails.
    """

    name: str = "rules"

    KEYWORDS = {
        Category.WATER: [
            "water", "pipe", "pipeline", "leak", "leakage", "burst", "flooding", "flood",
            "fajr", "nal", "supply", "tanki", "motor", "drainage", "nullah", "seeping"
        ],
        Category.ELECTRICITY: [
            "electricity", "power", "bijli", "voltage", "wire", "wires", "transformer",
            "spark", "sparking", "tripping", "meter", "current", "shock", "blackout",
            "load shedding", "short circuit", "feeder"
        ],
        Category.SANITATION: [
            "garbage", "kachra", "waste", "trash", "gutter", "sewer", "sewage", "drain",
            "smell", "filth", "safai", "dump", "manhole", "overflowing", "sanitation"
        ],
        Category.ROADS: [
            "road", "sarak", "pothole", "potholes", "pit", "asphalt", "crater", "footpath",
            "pavement", "caved in", "broken road", "trench", "patchwork"
        ],
        Category.STREETLIGHTS: [
            "streetlight", "street light", "lamp", "pole light", "bulb", "dark", "andhera",
            "darkness", "street lamp", "pole"
        ],
    }

    HIGH_PRIORITY_TERMS = [
        "burst", "flood", "flooding", "emergency", "hazard", "fire", "spark", "sparking",
        "danger", "dangerous", "electrocution", "shock", "casualty", "ground floor",
        "entering house", "caved in", "open manhole", "high voltage", "urgent"
    ]

    LOW_PRIORITY_TERMS = [
        "minor", "flicker", "dim", "paint", "suggestion", "request", "slow", "delayed",
        "aesthetic", "small"
    ]

    async def triage(self, text: str, location: str) -> TriageResult:
        cleaned = text.lower()

        # Category matching by keyword count
        scores = {cat: 0 for cat in Category}
        for category, terms in self.KEYWORDS.items():
            for term in terms:
                if re.search(r"\b" + re.escape(term) + r"\b", cleaned):
                    scores[category] += 1

        best_category = max(scores, key=lambda k: scores[k])
        if scores[best_category] == 0:
            best_category = Category.OTHER
            confidence = 0.50
        else:
            confidence = min(0.60 + (scores[best_category] * 0.10), 0.95)

        # Priority determination
        is_high = any(re.search(r"\b" + re.escape(term) + r"\b", cleaned) for term in self.HIGH_PRIORITY_TERMS)
        is_low = any(re.search(r"\b" + re.escape(term) + r"\b", cleaned) for term in self.LOW_PRIORITY_TERMS)

        if is_high:
            priority = Priority.HIGH
        elif is_low and not is_high:
            priority = Priority.LOW
        else:
            priority = Priority.NORMAL

        # Summary generation (< 140 chars)
        first_sentence = text.strip().split(".")[0]
        summary = f"{best_category.value.capitalize()} issue at {location}: {first_sentence}"
        if len(summary) > 137:
            summary = summary[:134] + "..."

        return TriageResult(
            category=best_category,
            priority=priority,
            summary=summary,
            confidence=round(confidence, 2),
        )
# Sarim update: high priority for dangerous electrical wire sparking
