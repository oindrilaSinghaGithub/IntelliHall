"""
IntelliHall — AI Worker Recommendation Engine

Categorises complaints using keyword NLP heuristics, filters by specialization,
and ranks hall maintenance staff using a multi-factor score.
"""

from __future__ import annotations

from app.ai.utils import keyword_score, normalize_text
from app.models.enums import (
    ComplaintCategory,
    ComplaintPriority,
    WorkerAvailability,
    WorkerExperienceLevel,
    WorkerSpecialization,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.worker import Worker


# Keyword bags for specialization heuristics
_ELECTRICIAN_KEYWORDS = [
    ("light", 1.5), ("fan", 1.5), ("switch", 1.5), ("wiring", 2.0), ("socket", 1.5),
    ("power", 1.0), ("electricity", 2.0), ("geyser", 1.5), ("bulb", 1.5), ("shock", 2.0),
    ("spark", 2.0), ("fuse", 1.5), ("circuit", 2.0), ("short circuit", 2.5),
    ("live wire", 2.5), ("electrician", 3.0), ("electrical", 2.5), ("heater", 1.5)
]

_PLUMBER_KEYWORDS = [
    ("tap", 1.5), ("pipe", 1.5), ("leakage", 2.0), ("flush", 1.5), ("washroom", 1.5),
    ("toilet", 1.5), ("leak", 1.5), ("water", 1.0), ("drain", 1.5), ("basin", 1.5),
    ("clogging", 1.5), ("clog", 1.5), ("blockage", 1.5), ("plumbing", 2.5),
    ("plumber", 3.0), ("sewage", 2.0), ("tap dripping", 2.0), ("dripping", 1.5)
]

_CARPENTER_KEYWORDS = [
    ("door", 1.5), ("window", 1.5), ("lock", 1.5), ("handle", 1.0), ("hinge", 1.5),
    ("bolt", 1.5), ("almirah", 1.5), ("cabinet", 1.5), ("drawer", 1.5), ("key", 1.0),
    ("frame", 1.0), ("carpentry", 2.5), ("carpenter", 3.0), ("furniture", 2.0),
    ("table", 1.5), ("chair", 1.5), ("bed", 1.5), ("wooden", 1.5)
]

_CLEANING_KEYWORDS = [
    ("cleanliness", 2.0), ("dirty", 1.5), ("dust", 1.5), ("dusty", 1.5), ("sweep", 2.0),
    ("cleaning", 2.0), ("garbage", 2.0), ("trash", 2.0), ("rubbish", 2.0), ("waste", 1.5),
    ("litter", 1.5), ("housekeeping", 2.0), ("clean", 1.5), ("mess", 1.5), ("dirt", 1.5)
]

_NETWORK_KEYWORDS = [
    ("internet", 2.0), ("wifi", 2.0), ("network", 2.0), ("ethernet", 2.0), ("router", 2.0),
    ("cable", 1.0), ("connection", 1.0), ("offline", 1.5), ("slow internet", 2.0),
    ("port", 1.0), ("lan", 1.5), ("wi fi", 2.0), ("network staff", 3.0)
]

_CIVIL_KEYWORDS = [
    ("paint", 1.5), ("painting", 1.5), ("wall", 1.0), ("ceiling", 1.5), ("crack", 1.5),
    ("cracks", 1.5), ("plaster", 2.0), ("floor", 1.0), ("tile", 1.5), ("tiles", 1.5),
    ("concrete", 1.5), ("brick", 1.5), ("structural", 2.0), ("civil", 2.5),
    ("civil maintenance", 3.0), ("seep", 1.5), ("seepage", 2.0), ("cement", 1.5)
]

# Mapping from specialization enum → keyword bags
_SPECIALIZATION_BAGS = {
    WorkerSpecialization.ELECTRICIAN: _ELECTRICIAN_KEYWORDS,
    WorkerSpecialization.PLUMBER: _PLUMBER_KEYWORDS,
    WorkerSpecialization.CARPENTER: _CARPENTER_KEYWORDS,
    WorkerSpecialization.CLEANING_STAFF: _CLEANING_KEYWORDS,
    WorkerSpecialization.NETWORK_STAFF: _NETWORK_KEYWORDS,
    WorkerSpecialization.CIVIL_MAINTENANCE: _CIVIL_KEYWORDS,
}

# Base mapping from category → specialization
_CATEGORY_MAPPING = {
    ComplaintCategory.ELECTRICAL: WorkerSpecialization.ELECTRICIAN,
    ComplaintCategory.PLUMBING: WorkerSpecialization.PLUMBER,
    ComplaintCategory.CARPENTRY: WorkerSpecialization.CARPENTER,
    ComplaintCategory.CLEANLINESS: WorkerSpecialization.CLEANING_STAFF,
    ComplaintCategory.INTERNET: WorkerSpecialization.NETWORK_STAFF,
    ComplaintCategory.CIVIL: WorkerSpecialization.CIVIL_MAINTENANCE,
    ComplaintCategory.WATER: WorkerSpecialization.PLUMBER,
    ComplaintCategory.FURNITURE: WorkerSpecialization.CARPENTER,
}


class WorkerRecommender:
    """
    AI Recommendation engine for worker assignment.
    Ranks workers in a hall based on predicted specialization, availability,
    workload (active jobs), rating, and priority-experience level matching.
    """

    def predict_specialization(
        self, category: ComplaintCategory, title: str, description: str
    ) -> WorkerSpecialization:
        """Heuristically predict the target worker specialization."""
        combined = normalize_text(f"{title} {description}")

        # Compute keyword scores for each specialization
        scores: dict[WorkerSpecialization, float] = {
            spec: keyword_score(combined, bag)
            for spec, bag in _SPECIALIZATION_BAGS.items()
        }

        # Apply a base weight if category matches the specialization
        base_spec = _CATEGORY_MAPPING.get(category)
        if base_spec:
            scores[base_spec] += 5.0

        # Find the highest-scoring specialization
        winner = max(scores, key=lambda s: scores[s])

        # If no score was generated at all, fall back to base category specialization
        if scores[winner] == 0.0:
            return base_spec or WorkerSpecialization.ELECTRICIAN

        return winner

    def recommend_worker(
        self,
        category: ComplaintCategory,
        title: str,
        description: str,
        predicted_priority: ComplaintPriority,
        workers: list[Worker],
    ) -> dict[str, object]:
        """
        Rank workers and return the best recommendation.

        Parameters
        ----------
        category: ComplaintCategory
        title: str
        description: str
        predicted_priority: ComplaintPriority
        workers: list[Worker]
            List of all workers belonging to the complaint's hall.

        Returns
        -------
        dict
            ``{
                "recommended_worker": Worker | None,
                "recommendation_score": float,
                "recommendation_reason": str
            }``
        """
        # Predict target specialization
        target_spec = self.predict_specialization(category, title, description)

        # Filter workers: same specialization, not on leave
        candidates = [
            w for w in workers
            if w.specialization == target_spec and w.availability_status != WorkerAvailability.ON_LEAVE
        ]

        if not candidates:
            spec_label = target_spec.value.replace("_", " ").title()
            return {
                "recommended_worker": None,
                "recommendation_score": 0.0,
                "recommendation_reason": (
                    f"No suitable worker available.\n"
                    f"Suggested specialization: {spec_label}"
                ),
            }

        # Score and rank candidates
        ranked_candidates = []
        for w in candidates:
            # 1. Specialization Match: 50 points
            spec_score = 50.0

            # 2. Availability: 25 points if available, 10 if busy
            avail_score = 25.0 if w.availability_status == WorkerAvailability.AVAILABLE else 10.0

            # 3. Workload (active jobs): max(0, 15 - 3 * active_jobs)
            workload_score = max(0.0, 15.0 - (3.0 * w.active_jobs))

            # 4. Skill Rating: 10 * (skill_rating / 5)
            rating_score = 10.0 * (w.skill_rating / 5.0)

            # Base score
            base_score = spec_score + avail_score + workload_score + rating_score

            # 5. Experience Adjustments based on predicted priority
            exp_adjustment = 0.0
            if predicted_priority in (ComplaintPriority.CRITICAL, ComplaintPriority.HIGH):
                if w.experience_level == WorkerExperienceLevel.SENIOR:
                    exp_adjustment = 5.0
                elif w.experience_level == WorkerExperienceLevel.INTERMEDIATE:
                    exp_adjustment = 2.0
                elif w.experience_level == WorkerExperienceLevel.JUNIOR:
                    exp_adjustment = -2.0
            elif predicted_priority == ComplaintPriority.LOW:
                if w.experience_level == WorkerExperienceLevel.JUNIOR:
                    exp_adjustment = 5.0
                elif w.experience_level == WorkerExperienceLevel.INTERMEDIATE:
                    exp_adjustment = 2.0
                elif w.experience_level == WorkerExperienceLevel.SENIOR:
                    exp_adjustment = -2.0

            final_score = max(0.0, min(100.0, base_score + exp_adjustment))
            ranked_candidates.append((w, final_score))

        # Sort by final score in descending order
        ranked_candidates.sort(key=lambda item: item[1], reverse=True)
        best_worker, best_score = ranked_candidates[0]

        # Generate structured explanation bullets
        spec_label = target_spec.value.replace("_", " ").title()
        reason_bullets = [
            f"✓ Complaint category: {category.value.title()}",
            f"✓ Worker specialization matches ({spec_label})",
            f"✓ Available now" if best_worker.availability_status == WorkerAvailability.AVAILABLE else f"⚠ Currently busy ({best_worker.active_jobs} active jobs)",
            f"✓ Lowest workload ({best_worker.active_jobs} active complaints)" if best_worker.active_jobs == 0 else f"✓ Workload: {best_worker.active_jobs} active complaints",
            f"✓ Skill Rating: {best_worker.skill_rating:.1f}/5.0",
        ]

        # Add priority experience reason
        if predicted_priority in (ComplaintPriority.CRITICAL, ComplaintPriority.HIGH):
            if best_worker.experience_level == WorkerExperienceLevel.SENIOR:
                reason_bullets.append("✓ Senior experience preferred for high-priority complaint")
        elif predicted_priority == ComplaintPriority.LOW:
            if best_worker.experience_level == WorkerExperienceLevel.JUNIOR:
                reason_bullets.append("✓ Junior assignment preferred for low-priority complaint")

        explanation = "\n".join(reason_bullets)

        return {
            "recommended_worker": best_worker,
            "recommendation_score": round(best_score, 1),
            "recommendation_reason": explanation,
        }
