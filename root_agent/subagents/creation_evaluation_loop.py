"""
Sub-Agent: Creation-Evaluation Loop
LoopAgent wrapping Creator + Evaluator for retry logic (max 3 iterations).
"""

from google.adk.agents import LoopAgent
from root_agent.subagents.creator_agent import creator_agent
from root_agent.subagents.evaluator_agent import evaluator_agent


creation_evaluation_loop = LoopAgent(
    name="creation_evaluation_loop",
    description="Iteratively creates content and evaluates it. Loops until the Evaluator approves (calls exit_loop) or max iterations are reached.",
    sub_agents=[creator_agent, evaluator_agent],
    max_iterations=3,
)
