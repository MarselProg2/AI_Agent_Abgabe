"""
Tool: calculate_engagement
Calculates a weighted engagement rate and provides a qualitative assessment.
"""

from typing import Dict, Any


def calculate_engagement(likes: int, comments: int, shares: int, saves: int, reach: int) -> Dict[str, Any]:
    """
    Calculates a weighted engagement rate and provides a qualitative assessment.

    Formula: ((Likes * 1) + (Comments * 2) + (Shares * 3) + (Saves * 3)) / Reach * 100

    Args:
        likes: Number of likes.
        comments: Number of comments.
        shares: Number of shares.
        saves: Number of saves.
        reach: Total reach or unique views.

    Returns:
        dict: A dictionary containing the numeric 'rate', a string 'assessment', and 'details'.
    """
    if reach == 0:
        return {
            "rate": 0.0,
            "assessment": "Error (Zero Reach)",
            "details": "Reach cannot be zero."
        }

    weighted_interactions = (likes * 1) + (comments * 2) + (shares * 3) + (saves * 3)
    score = (weighted_interactions / reach) * 100

    assessment = "Needs Optimization"
    if score > 10:
        assessment = "Viral Potential! 🔥"
    elif score > 5:
        assessment = "Good Performance 👍"

    return {
        "rate": round(score, 2),
        "assessment": assessment,
        "details": f"Weighted Score: {score:.2f}% (Likes: {likes}, Comments: {comments}, Shares: {shares}, Saves: {saves})"
    }
