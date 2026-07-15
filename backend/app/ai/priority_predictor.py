"""
IntelliHall — Priority Predictor

Provides a heuristic rule-based implementation of :class:`PriorityPredictor`
that analyses the complaint title and description to suggest a priority level
and a confidence score.

Design contract
---------------
- Input : ``title: str``, ``description: str``
- Output: ``{"priority": "low|medium|high|critical", "confidence": float}``
- The caller (ComplaintService) must NOT contain any scoring logic.
- Replacing this heuristic with an ML model requires only swapping this file;
  the public interface (``predict``) stays unchanged.

Scoring approach
----------------
Each priority level has a bag of ``(keyword_phrase, weight)`` tuples.
The combined title+description text is scored against every bag.
The bag with the highest total score wins.  Confidence is computed as:

    confidence = winner_score / total_score   (when total_score > 0)
    confidence = 0.50                          (when no keyword matched)

This guarantees a minimum confidence of 0.50 for the default fallback (medium)
and values approaching 1.0 when the text heavily matches one category.
"""

from __future__ import annotations

from app.ai.utils import keyword_score, normalize_text
from app.models.enums import ComplaintPriority

# ---------------------------------------------------------------------------
# Keyword bags
# Each entry is (phrase, weight).
# Higher weight = stronger signal.
# Phrases are matched against normalised text (lowercase, no punctuation).
# ---------------------------------------------------------------------------

_CRITICAL_KEYWORDS: list[tuple[str, float]] = [
    ("gas leak", 3.0),
    ("gas leakage", 3.0),
    ("fire", 2.5),
    ("spark", 2.0),
    ("short circuit", 3.0),
    ("electric shock", 3.0),
    ("smoke", 2.0),
    ("water leakage near electricity", 3.5),
    ("electrical flooding", 3.0),
    ("live wire", 3.0),
    ("explosion", 3.5),
    ("flooding", 2.0),
    ("severe flood", 2.5),
    ("burning smell", 2.5),
    ("fire hazard", 3.0),
    ("power failure entire", 2.0),
]

_HIGH_KEYWORDS: list[tuple[str, float]] = [
    ("major leakage", 2.5),
    ("ceiling collapse", 3.0),
    ("ceiling cracked", 2.0),
    ("main gate broken", 2.5),
    ("sewage overflow", 2.5),
    ("sewage", 2.0),
    ("broken pipe", 2.0),
    ("burst pipe", 2.5),
    ("no water supply", 2.5),
    ("water supply cut", 2.0),
    ("severe damage", 2.0),
    ("roof leak", 2.0),
    ("structural damage", 2.5),
    ("collapsed", 2.5),
    ("major damage", 2.0),
    ("whole floor affected", 2.5),
]

_MEDIUM_KEYWORDS: list[tuple[str, float]] = [
    ("fan not working", 1.5),
    ("tube light fused", 1.5),
    ("tube light not working", 1.5),
    ("light not working", 1.5),
    ("light fused", 1.5),
    ("water heater", 1.5),
    ("tap dripping", 1.5),
    ("tap leaking", 1.5),
    ("door lock broken", 1.5),
    ("door lock", 1.0),
    ("window broken", 1.5),
    ("toilet blocked", 1.5),
    ("drain blocked", 1.5),
    ("flush not working", 1.5),
    ("switch not working", 1.5),
    ("socket not working", 1.5),
    ("power cut", 1.0),
    ("water leakage", 1.5),
    ("minor leakage", 1.0),
    ("refrigerator", 1.0),
    ("ac not working", 1.5),
    ("air conditioner", 1.0),
    ("internet not working", 1.0),
    ("wifi not working", 1.0),
    ("noisy pipe", 1.0),
]

_LOW_KEYWORDS: list[tuple[str, float]] = [
    ("paint", 1.0),
    ("painting", 1.0),
    ("wall paint", 1.0),
    ("peeling", 1.0),
    ("cleanliness", 1.0),
    ("dirty", 1.0),
    ("dust", 1.0),
    ("dusty", 1.0),
    ("stain", 1.0),
    ("graffiti", 1.0),
    ("cosmetic", 1.0),
    ("furniture arrangement", 1.0),
    ("cleaning", 1.0),
    ("sweep", 1.0),
    ("rubbish", 1.0),
    ("garbage", 1.0),
    ("minor repair", 0.5),
    ("suggestion", 0.5),
    ("improvement", 0.5),
]

# Mapping from priority enum value → its keyword bag
_PRIORITY_BAGS: dict[ComplaintPriority, list[tuple[str, float]]] = {
    ComplaintPriority.CRITICAL: _CRITICAL_KEYWORDS,
    ComplaintPriority.HIGH: _HIGH_KEYWORDS,
    ComplaintPriority.MEDIUM: _MEDIUM_KEYWORDS,
    ComplaintPriority.LOW: _LOW_KEYWORDS,
}

# Default priority when no keyword matches at all
_DEFAULT_PRIORITY = ComplaintPriority.MEDIUM
_DEFAULT_CONFIDENCE = 0.50


# ---------------------------------------------------------------------------
# PriorityPredictor
# ---------------------------------------------------------------------------


class PriorityPredictor:
    """
    Heuristic complaint-priority predictor.

    Usage
    -----
    ::

        predictor = PriorityPredictor()
        result = predictor.predict(
            title="Gas leak in bathroom",
            description="Strong smell of gas near the geysers.",
        )
        # result == {"priority": "critical", "confidence": 0.93}

    The class is stateless, so a single instance can be shared across
    requests without thread-safety concerns.
    """

    def predict(self, title: str, description: str) -> dict[str, object]:
        """
        Predict the priority for a complaint.

        Parameters
        ----------
        title:
            Short summary entered by the student.
        description:
            Detailed description of the issue.

        Returns
        -------
        dict
            ``{"priority": ComplaintPriority, "confidence": float}``
            where *priority* is a :class:`~app.models.enums.ComplaintPriority`
            instance and *confidence* is in the range ``[0.50, 1.00]``.
        """
        # Combine and normalise input text
        combined = normalize_text(f"{title} {description}")

        # Score each priority level
        scores: dict[ComplaintPriority, float] = {
            priority: keyword_score(combined, bag)
            for priority, bag in _PRIORITY_BAGS.items()
        }

        total_score = sum(scores.values())

        if total_score == 0.0:
            # No keywords matched — fall back to MEDIUM with minimum confidence
            return {
                "priority": _DEFAULT_PRIORITY,
                "confidence": _DEFAULT_CONFIDENCE,
            }

        # Pick the highest-scoring priority
        winner = max(scores, key=lambda p: scores[p])
        raw_confidence = scores[winner] / total_score

        # Clamp to [0.50, 1.00] — we never go below 50 % even with sparse matches
        confidence = max(0.50, min(1.0, raw_confidence))

        return {
            "priority": winner,
            "confidence": round(confidence, 4),
        }
