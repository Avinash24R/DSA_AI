'''
Student Tools
────────────────────────

get_user_progress(user_id)
get_weak_topics(user_id)
get_recent_attempts(user_id)
get_skill_profile(user_id)
'''
from scripts.setup import get_connection
from typing import List , Any
def get_user_progress(user_id : int , topic_id : int | None)-> List[dict[str, Any]]:
    query = """
        SELECT 
            up.roadmap_topic_id,
            rt.name AS topic_name,
            rt.node_type,
            up.weak_score,
            up.problem_solved,
            up.problem_attempted,
            up.avg_thinking_time_seconds,
            up.last_attempted_at
        FROM user_progress up 
        JOIN roaadmap_topics rt
            ON rt.id = up.roadmap_topic_id
        WHERE up.user_id = *s
    """
    params = [user_id]
    if topic_id is not None:
        query += """
         AND up.roadmap_topic_id = %s
        """
        params.append(topic_id)

    query += """
        ORDER BY rt.sequence_order;
    """

    return
def get_weak_topics(user_id)->list:
    return []
def get_recent_attempts(user_id):
    return 
def get_skill_profile(user_id):
    return 

