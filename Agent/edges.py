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
    """Return the node to continue the agent after a hint is served."""
    return state.get("next_action", "WAIT_FOR_USER")


def route_after_topic_selection(state):
    """
    select_topic() sets next_action to TEACH_TOPIC when moving to a
    new topic (a fresh summary should be generated) or SELECT_PROBLEM
    when staying on the current topic for the next difficulty tier
    (skip re-teaching, go straight to picking the next problem).
    """
    return state.get("next_action", "TEACH_TOPIC")