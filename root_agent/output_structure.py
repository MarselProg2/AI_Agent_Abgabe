"""
Pydantic Output Schemas for the InsightBench Multi-Agent System.
Each schema defines the structured output format for the corresponding agent.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Schema: Video Analyst Agent
# ============================================================================
class SchemaExtraction(BaseModel):
    """Extracted content structure from the video."""
    scene_length: str = Field(description="Scene length – Fast cuts or long takes?")
    hook_type: str = Field(description="Hook type – What happens in the first 3 seconds? (Question, Shock, Curiosity, Statement, Visual stimulus)")
    visual_frequency: str = Field(description="Visual frequency – How often do visual elements change?")
    unique_visual_elements: str = Field(description="Unique visual elements – What makes this content stand out visually?")


class VideoAnalysisSchema(BaseModel):
    """Output schema for the Video Analyst Agent."""
    schema_extraction: SchemaExtraction = Field(description="Extracted data structure of the content.")
    root_questions: List[str] = Field(description="Exactly 3 Root Questions targeting retention optimization.", min_length=3, max_length=3)


# ============================================================================
# Schema: Insight Extractor Agent
# ============================================================================
class AnalysisLevels(BaseModel):
    """The 4 analysis levels for each Root Question."""
    descriptive: str = Field(description="Descriptive: What was shown exactly?")
    diagnostic: str = Field(description="Diagnostic: Why does this moment captivate?")
    predictive: str = Field(description="Predictive: What retention rate is expected?")
    prescriptive: str = Field(description="Prescriptive: What change would maximize success?")


class FollowUpQuestion(BaseModel):
    """A follow-up question and its answer."""
    question: str = Field(description="The follow-up question.")
    answer: str = Field(description="The answer to the follow-up question.")


class RootQuestionAnalysis(BaseModel):
    """Complete analysis for a single Root Question."""
    root_question: str = Field(description="The Root Question being analyzed.")
    answer: str = Field(description="Direct answer to the Root Question.")
    follow_up_questions: List[FollowUpQuestion] = Field(description="4 Follow-up Questions with answers.", min_length=4, max_length=4)
    analysis_levels: AnalysisLevels = Field(description="Analysis across 4 levels.")


class StrategySchema(BaseModel):
    """Output schema for the Insight Extractor Agent."""
    most_engaging_element: str = Field(description="The single most engaging element identified.")
    hook_strategy: str = Field(description="How to stop the scroll in the first 3 seconds.")
    psychological_angle: str = Field(description="Why will people share this? (Humor, Shock, Relatability?)")
    root_question_analyses: List[RootQuestionAnalysis] = Field(description="Drill-down analysis for each Root Question.", min_length=3, max_length=3)
    prescriptive_summary: str = Field(description="Summary of all Prescriptive Insights.")


# ============================================================================
# Schema: Creator Agent
# ============================================================================
class HashtagStrategy(BaseModel):
    """A single strategic hashtag with its reasoning."""
    hashtag: str = Field(description="The hashtag (including #).")
    strategy: str = Field(description="Strategic reasoning for this hashtag.")


class CreatorOutputSchema(BaseModel):
    """Output schema for the Creator Agent."""
    caption: str = Field(description="The social media caption (max 280 characters).", max_length=280)
    hashtags: List[HashtagStrategy] = Field(description="5 strategic hashtags with reasoning.", min_length=5, max_length=5)


# ============================================================================
# Schema: Evaluator Agent
# ============================================================================
class EvaluationCriterion(BaseModel):
    """A single evaluation criterion with score and reasoning."""
    criterion: str = Field(description="Name of the criterion.")
    score: int = Field(description="Score for this criterion (1-10).", ge=1, le=10)
    reasoning: str = Field(description="Reasoning for the score.")


class EvaluationSchema(BaseModel):
    """Output schema for the Evaluator Agent."""
    overall_rating: int = Field(description="Overall rating from 1 to 10.", ge=1, le=10)
    criteria: List[EvaluationCriterion] = Field(
        description="Individual scores for: Factual Accuracy, Trend Relevance, Strategic Depth, Creative Originality, Anti-Hallucination.",
        min_length=5,
        max_length=5,
    )
    justification: str = Field(description="Detailed justification for the overall rating.")
    approved: bool = Field(description="True if score >= 7 (APPROVED), False if < 7 (NEEDS_REVISION).")
    feedback: Optional[str] = Field(default=None, description="Concrete improvement suggestions if NEEDS_REVISION.")
