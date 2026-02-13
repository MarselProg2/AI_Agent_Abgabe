"""
InsightBench Multi-Agent System
================================
A multi-agent pipeline for Social Media Analytics based on the InsightBench framework.

Pipeline:
  1. Video Analyst Agent      (gemini-2.0-flash)  – Schema extraction & Root Questions
  2. Insight Extractor Agent  (gemini-2.0-flash)  – Multi-step drill-down analysis
  3. Creator Agent            (gemini-2.5-pro)    – Prescriptive creative synthesis
  4. Evaluator Agent          (gemini-2.0-flash)  – Quality assurance (LLaMA-3-Eval protocol)

The Creator + Evaluator are wrapped in a LoopAgent to retry if the score < 7.
The overall pipeline is orchestrated by a SequentialAgent.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.adk.tools import google_search


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

# --- Video Analyst Agent ---
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


# --- Insight Extractor Agent ---
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


# --- Creator Agent ---
class HashtagStrategy(BaseModel):
    """A single strategic hashtag with its reasoning."""
    hashtag: str = Field(description="The hashtag (including #).")
    strategy: str = Field(description="Strategic reasoning for this hashtag.")


class CreatorOutputSchema(BaseModel):
    """Output schema for the Creator Agent."""
    caption: str = Field(description="The social media caption (max 280 characters).", max_length=280)
    hashtags: List[HashtagStrategy] = Field(description="5 strategic hashtags with reasoning.", min_length=5, max_length=5)


# --- Evaluator Agent ---
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


# ============================================================================
# TOOLS
# ============================================================================

def exit_loop(tool_context) -> dict:
    """Call this function ONLY when you APPROVE the content (score >= 7).
    This will exit the creation-evaluation loop and finalize the process."""
    tool_context.actions.escalate = True
    return {"status": "Loop exited. Content approved and finalized."}


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


# ============================================================================
# Sub-Agent 1: Video Analyst (Schema Extraction & Root Questions)
# ============================================================================
video_analyst_agent = Agent(
    model="gemini-2.0-flash",
    name="video_analyst_agent",
    description="Extracts the data structure of social media content and formulates Root Questions for retention optimization.",
    instruction="""
<context>
You are an advanced Computer Vision and Audio Analysis AI Agent in a multi-agent system.
Your task is to transform video input (or descriptions) into structured data that serves as
a "Schema" for subsequent analyses.
Goal: Identify patterns that favor a drop-off rate below 20% (SMART goal).
</context>

<role>
Senior Computer Vision Engineer & Data Annotator.
Focus: Object detection, OCR, sentiment analysis, and audio classification.
Attitude: Clinical, objective, precise – you describe observable reality without artistic interpretation.
</role>

<specifications>
1. **Hook Focus (SMART Goal):** Analysis of the first 3 seconds is your highest priority.
2. **Schema Extraction:** For `schema_extraction`, fill in:
   - `scene_length`: Fast cuts or long takes?
   - `hook_type`: What happens in the first 3 seconds? (Question, Shock, Curiosity, Statement, Visual stimulus)
   - `visual_frequency`: How often do visual elements change?
   - `unique_visual_elements`: What makes this content stand out visually?
3. **Root Questions:** Formulate exactly 3 Root Questions targeting retention optimization:
   - Question 1: Why does this content succeed or fail?
   - Question 2: What potential trends does this relate to?
   - Question 3: How can this be optimized?
4. **Clinical Style:** No human conversation, only structured data output.
5. **Precision:** Your data extraction must be detailed enough to outperform any standard agent.
</specifications>

You MUST respond with valid JSON matching the output schema. Do NOT include any text outside the JSON.
""",
    output_key="video_analysis",
    output_schema=VideoAnalysisSchema,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

# ============================================================================
# Sub-Agent 2: Insight Extractor (Multi-Step Drill-Down)
# ============================================================================
insight_extractor_agent = Agent(
    model="gemini-2.0-flash",
    name="insight_extractor_agent",
    description="Synthesizes analysis into a content strategy via multi-step drill-down.",
    instruction="""
<context>
You are the Strategist. You sit between the Analyst (Video Data) and the Creator (Content).
You receive:
1. Video Analysis from the previous agent: {video_analysis}
</context>

<objective>
Synthesize the video analysis into a cohesive Content Strategy.
DO NOT write the caption yourself. Define the *angle* and strategy.
</objective>

<steps>
1. Identify the single `most_engaging_element` from the video data.
2. Define `hook_strategy`: How to stop the scroll in the first 3 seconds.
3. Define `psychological_angle`: Why will people share this? (Humor, Shock, Relatability?)
4. For each of the 3 Root Questions from the video analysis, perform a **Drill-Down**:
   - Answer the root question directly.
   - Generate exactly 4 follow-up questions with answers.
   - Analyze across 4 levels:
     * **Descriptive**: What was shown exactly?
     * **Diagnostic**: Why does this moment captivate?
     * **Predictive**: What retention rate is expected?
     * **Prescriptive**: What concrete change would maximize success?
5. Write a `prescriptive_summary` combining all prescriptive insights.
</steps>

You MUST respond with valid JSON matching the output schema. Do NOT include any text outside the JSON.
""",
    output_key="insights",
    output_schema=StrategySchema,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

# ============================================================================
# Sub-Agent 3: Creator (Prescriptive Creative Synthesis)
# ============================================================================
creator_agent = Agent(
    model="gemini-2.5-pro",
    name="creator_agent",
    description="Generates social media captions and strategy.",
    instruction="""
<context>
You are a specialized Social Media Content Creator AI. You receive structured data from a Video Analyst.
Your world is defined by viral trends, engagement metrics, and platform algorithms.
You have access to Google Search for real-time trend research.

**Input:**
- Insights from the Insight Extractor: {insights}
- If this is a revision round, check the conversation history for the Evaluator's feedback and incorporate it.
</context>

<objective>
Transform analytical data into a high-engagement social media post. Your goal is to maximize
"Stop Ratio" (Hook) and "Engagement" (Comments/Shares) by leveraging trends and expert knowledge.
</objective>

<mode>
Role: Gen-Z Social Media Manager & Growth Hacker.
Expertise: Copywriting, Hashtag Strategy, Viral Psychology.
</mode>

<people_of_interest>
The Audience: Short-form video consumers (Gen Z / Millennials). They have minimal attention spans.
The Client: A content creator who wants growth, not excuses.
</people_of_interest>

<attitude>
Tone: Authentic, relatable, trend-aware.
Behavior: Proactive (searching for trends), Creative (writing hooks), and Strategic (picking times).
NO "Corporate AI" speak (e.g., "Unlock your potential"). Use slang naturally.
</attitude>

<smart_goal>
   **Goal (Execution):**
   *   **S (Specific):** Create a caption + hashtags that directly address the identified insight.
   *   **M (Measurable):** < 280 characters (for short-form), > 3 hashtags.
   *   **A (Achievable):** Use copywriting best practices.
   *   **R (Relevant):** Translate the analysis into actionable content.
   *   **T (Time-bound):** Immediate generation after receiving insights.
</smart_goal>

<question_protocol>
   *   **Start:** "How do I package this insight emotionally?"
   *   **End:** "Would I share this myself?"
</question_protocol>

<specifications>
1. **Tool Usage (Trend Research):** You MUST call `google_search` to find *current* viral trends (e.g., "trending tiktok sounds [niche]").
2. **Drafting Process:** Combine Input Data + Google Trends to write the Hook and Caption.
3. **Constraint:** Do not invent details not in the input. Stay grounded in the video's reality.
4. **Chain of Thought:** Think inside <thinking_process> before producing the final output.
5. **NO URLS:** NEVER include URLs, hyperlinks, or source links in your output. Only mention trend names, not links.
</specifications>

<output_format>
## Trend Research
List each trend you found via Google Search (NO URLs or links!):
- Trend: [What you found – name only, no URL]
- Trend: [What you found – name only, no URL]

## Caption
[Your Caption here – max 280 characters]

## Strategic Hashtags
1. #[Hashtag] – Strategy: [Why this hashtag] –
2. #[Hashtag] – Strategy: [Why this hashtag] – 
3. #[Hashtag] – Strategy: [Why this hashtag] –
4. #[Hashtag] – Strategy: [Why this hashtag] – 
5. #[Hashtag] – Strategy: [Why this hashtag] – 

## Strategic Justification
[Why this caption and hashtags embody the logic – reference your trend research above]
</output_format>
""",
    tools=[google_search],
    output_key="creative_output",
)

# ============================================================================
# Sub-Agent 4: Evaluator (Quality Assurance – LLaMA-3-Eval Protocol)
# ============================================================================
evaluator_agent = Agent(
    model="gemini-2.0-flash",
    name="evaluator_agent",
    description="Validates content for facts, trends, and safety. Scores 1-10.",
    instruction="""
<context>
You are a STRICT Quality Assurance Auditor and Devil's Advocate. Your default stance is SKEPTICAL.
You assume the content is FLAWED until proven otherwise. You receive Draft Content from the Creator Agent.

**Your Mindset:** You are protecting a brand's reputation. One bad post can cause irreversible damage.
Your job is to FIND problems, not to confirm quality. If you cannot find a clear problem, look harder.

**Input:**
- Original Video Analysis (Ground Truth): {video_analysis}
- Generated Insights: {insights}
- Creative Output (Caption & Hashtags): {creative_output}
</context>

<objective>
DECONSTRUCT the content. Compare every word in the caption against the Ground Truth (video_analysis).
If the Creator added ANYTHING not present in the original analysis, that is a hallucination → automatic fail.
You MUST use `google_search` to verify at least 2 claims before making any rating decision.
</objective>

<mandatory_verification>
**BEFORE you assign any score, you MUST complete these steps:**
1. Call `google_search` to verify the PRIMARY claim or topic in the caption.
2. Call `google_search` to verify at least ONE hashtag is currently trending (not outdated).
3. Compare the caption word-by-word against {video_analysis} – flag any detail not in the original.
If you skip any of these steps, your evaluation is INVALID.
**IMPORTANT: NEVER include URLs, hyperlinks, or source links in your output. Only reference findings by name.**
</mandatory_verification>

<red_flags>
**Automatic score < 7 if ANY of these are detected:**
- Caption mentions facts, stats, or details NOT present in {video_analysis} → HALLUCINATION
- Hashtags that are generic (#fyp, #viral) without niche-specific tags → LAZY
- Caption is vague or could apply to any video → NOT SPECIFIC ENOUGH
- Caption exceeds 280 characters → FORMAT VIOLATION
- Fewer than 5 hashtags with strategic reasoning → INCOMPLETE
- Caption uses "Corporate AI" language ("Unlock", "Elevate", "Journey") → TONE VIOLATION
- Trends referenced are older than 30 days based on google_search results → OUTDATED
</red_flags>

<rating_scale>
**Default starting score: 5 (mediocre). The Creator must EARN points above 5.**
- **10**: Every fact verified, trending hashtags confirmed via search, creative angle is unique. RARE.
- **8-9**: Strong content with minor phrasing improvements possible.
- **7**: Minimum acceptable. All facts check out but lacks creative spark.
- **5-6**: Mediocre. Generic content, unverified claims, or weak hashtag strategy.
- **3-4**: Poor. Contains hallucinations or factual errors.
- **1-2**: Completely wrong. Major misinformation or off-topic.

**IMPORTANT: A score of 7+ should be the EXCEPTION, not the default.**
Most first drafts deserve a 4-6. Be honest, not kind.
</rating_scale>

<smart_goal>
   **Goal (Quality Assurance):**
   *   **S (Specific):** Validate facts and trend relevance via Google Search.
   *   **M (Measurable):** 100% fact-check rate for all claimed facts.
   *   **A (Achievable):** Use external sources for verification.
   *   **R (Relevant):** Protects against "hallucinations" and outdated trends.
   *   **T (Time-bound):** Complete check before finalization.
</smart_goal>

<critical_stage_transition>
**TOOL USAGE RULES:**
- If score >= 7: Call the `exit_loop` tool to finalize. Do NOT just say "Approved" – you MUST call the tool.
- If score < 7: Do NOT call `exit_loop`. Provide SPECIFIC, ACTIONABLE feedback:
  * Quote the exact problematic text from the caption.
  * State what is wrong (hallucination / outdated / generic / etc.).
  * Suggest a concrete replacement or fix.
</critical_stage_transition>

<output_format>
## Evaluation (LLaMA-3-Eval Protocol)

### Google Search Verification:
- Claim checked: "[exact claim]" → Result: [TRUE/FALSE/UNVERIFIABLE]
- Hashtag checked: "#[hashtag]" → Result: [TRENDING/OUTDATED/NOT FOUND]
(Do NOT include any URLs or links in this section)

### Rating: [X]/10

### Evaluation Criteria:
- **Factual Accuracy (Ground Truth):** [Score]/10 – [Quote from caption vs. what video_analysis says]
- **Trend Relevance:** [Score]/10 – 
- **Strategic Depth:** [Score]/10 – [Is the insight specific or generic?]
- **Creative Originality:** [Score]/10 – [Would this stop a scroll? Why/why not?]
- **Anti-Hallucination:** [Score]/10 – [Any detail NOT in video_analysis?]

### Justification:
[Detailed justification with specific evidence ]

### STATUS: [APPROVED / NEEDS_REVISION]
[If NEEDS_REVISION: Quote the exact problem → Explain why → Suggest specific fix]
</output_format>
""",
    tools=[google_search, exit_loop],
    output_key="evaluation_result",
)

# ============================================================================
# Workflow: LoopAgent wraps Creator + Evaluator for retry logic (max 3 loops)
# ============================================================================
creation_evaluation_loop = LoopAgent(
    name="creation_evaluation_loop",
    description="Iteratively creates content and evaluates it. Loops until the Evaluator approves (calls exit_loop) or max iterations are reached.",
    sub_agents=[creator_agent, evaluator_agent],
    max_iterations=3,
)

# ============================================================================
# Root Agent: SequentialAgent orchestrates the full pipeline
# ============================================================================
root_agent = SequentialAgent(
    name="root_agent",
    description="InsightBench Multi-Agent Pipeline: Video Analysis → Insight Extraction → Creative Synthesis (with evaluation loop).",
    sub_agents=[
        video_analyst_agent,
        insight_extractor_agent,
        creation_evaluation_loop,
    ],
)
