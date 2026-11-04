"""Approval policy: turn a default probability into a decision."""

import json
from pathlib import Path


def load_policy(path):
    """Load the saved cut-off and review band."""
    return json.loads(Path(path).read_text())


def decide(probability, cutoff, review_margin):
    """Return 'Approve', 'Review', or 'Reject' for one probability."""
    if probability >= cutoff:
        return "Reject"
    if probability >= cutoff - review_margin:
        return "Review"
    return "Approve"