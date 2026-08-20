"""
Graph routing helpers for the DSA agent.

The routing functions return keys used by `StateGraph.add_conditional_edges`.
"""

from langgraph.graph import END


def route_after_evaluation(state):
    """
    Return the `next_action` value set by `evaluate_answer` so the
    graph's conditional edge mapping can route to the appropriate node.
    """
    return state.get("next_action", "HINT_RETRY")


def route_after_hint(state):
    return "wait_for_user"
