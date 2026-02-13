"""
Tool: exit_loop
Exits the Creator-Evaluator LoopAgent when content is approved (score >= 7).
"""


def exit_loop(tool_context) -> dict:
    """Call this function ONLY when you APPROVE the content (score >= 7).
    This will exit the creation-evaluation loop and finalize the process."""
    tool_context.actions.escalate = True
    return {"status": "Loop exited. Content approved and finalized."}
