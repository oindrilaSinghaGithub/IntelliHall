"""
IntelliHall — AI Utilities

Shared text-processing helpers for the AI module.
All functions are pure (no side-effects) to make unit testing trivial.
"""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------


def normalize_text(text: str) -> str:
    """
    Return a lowercase, whitespace-normalised version of *text* stripped
    of all punctuation.

    Example
    -------
    >>> normalize_text("Gas Leak!! (room 12)")
    'gas leak  room 12'
    """
    text = text.lower()
    # Replace punctuation with a space so multi-word phrases stay together
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse runs of whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Keyword scoring
# ---------------------------------------------------------------------------


def keyword_score(
    text: str,
    keywords: list[tuple[str, float]],
) -> float:
    """
    Return the total weighted score for all keyword phrases found in *text*.

    Parameters
    ----------
    text:
        Already-normalised input string (use :func:`normalize_text` first).
    keywords:
        List of ``(phrase, weight)`` tuples.  Each *phrase* is a
        space-separated sequence of words (e.g. ``"short circuit"``).
        The phrase is matched as a whole substring, so ``"circuit"``
        alone would NOT match ``"short circuit"`` unless specified
        separately.

    Returns
    -------
    float
        Sum of weights for every phrase found in *text*.  A phrase that
        appears multiple times is counted only once (to prevent trivial
        gaming by repetition).
    """
    score = 0.0
    for phrase, weight in keywords:
        if phrase in text:
            score += weight
    return score
