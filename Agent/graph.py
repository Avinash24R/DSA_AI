from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver

from Agent.state import DSAState
from Agent.nodes import (
    load_student,
    evaluate_skill,
    select_topic,
    teach_topic,
    prepare_problem_node,
    select_problem_node,
    present_problem,
    wait_for_user,
    evaluate_answer,
    hint_retry,
    update_progress_node,
)
from Agent.edges import route_after_evaluation

def create_graph():
    graph = StateGraph(DSAState)

    graph.add_node("load_student", load_student)
    graph.add_node("evaluate_skill", evaluate_skill)
    graph.add_node("select_topic", select_topic)
    graph.add_node("teach_topic", teach_topic)
    graph.add_node("prepare_problems" , prepare_problem_node)
    graph.add_node("select_problem", select_problem_node)
    graph.add_node("present_problem", present_problem)
    graph.add_node("wait_for_user", wait_for_user)
    graph.add_node("evaluate_answer", evaluate_answer)
    graph.add_node("hint_retry", hint_retry)
    graph.add_node("update_progress", update_progress_node)

    graph.add_edge(START, "load_student")
    graph.add_edge("load_student", "evaluate_skill")
    graph.add_edge("evaluate_skill", "select_topic")
    graph.add_edge("select_topic", "teach_topic")
    graph.add_edge("teach_topic", "prepare_problems")
    graph.add_edge("prepare_problems", "select_problem")
    graph.add_edge("select_problem", "present_problem")
    graph.add_edge("present_problem", "wait_for_user")
    graph.add_edge("wait_for_user", "evaluate_answer")

    graph.add_conditional_edges(
        "evaluate_answer",
        route_after_evaluation,
        {
            "HINT_RETRY": "hint_retry",
            "UPDATE_PROGRESS": "update_progress",
        },
    )

    graph.add_edge("hint_retry", "wait_for_user")

    graph.add_edge("update_progress", "load_student")

    return graph.compile(checkpointer=InMemorySaver())
graph=create_graph()