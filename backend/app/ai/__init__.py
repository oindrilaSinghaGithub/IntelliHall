"""IntelliHall — AI Module

Provides AI/heuristic services for the IntelliHall complaint domain.

Current capabilities
--------------------
- **Priority Prediction** : :class:`~app.ai.priority_predictor.PriorityPredictor`
  Analyses complaint title + description and returns a suggested priority level
  with a confidence score.  Uses a weighted keyword-scoring engine that can be
  swapped for an ML model without changing the public API.

Future capabilities (planned)
------------------------------
- Duplicate Complaint Detection
- Maintenance Category Prediction
"""

from app.ai.priority_predictor import PriorityPredictor

__all__ = ["PriorityPredictor"]
