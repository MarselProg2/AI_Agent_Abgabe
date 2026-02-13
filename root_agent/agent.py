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

from google.adk.agents import SequentialAgent
from root_agent.subagents import (
    video_analyst_agent,
    insight_extractor_agent,
    creation_evaluation_loop,
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
