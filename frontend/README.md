# DSA AI Tutor Frontend

Minimal Bootstrap + HTML/CSS/JS frontend for the LangGraph DSA tutor.

## Files

- `index.html` - page structure and Bootstrap CDN
- `styles.css` - application styling
- `app.js` - UI state, API calls, submission flow

## Backend API contract

### GET `/api/agent/session/current`

Return:

```json
{
  "user": {
    "name": "Arjun",
    "level": "Beginner",
    "streak": 7,
    "xp": 1280,
    "accuracy": 72
  },
  "task": {
    "problem_id": "leetcode:123",
    "title": "Maximum Sum Subarray of Size K",
    "topic": "Sliding Window",
    "subtopic": "Fixed Window",
    "difficulty": "Easy",
    "url": "https://leetcode.com/...",
    "estimated_minutes": 20,
    "attempt_number": 1
  },
  "skill": {
    "score": 42,
    "solved": 23,
    "attempts": 45,
    "accuracy": 72
  }
}
```

### POST `/api/agent/session/{problem_id}/submit`

Request:

```json
{
  "language": "cpp",
  "code": "#include <bits/stdc++.h> ..."
}
```

The backend should:
1. Validate the active LangGraph session.
2. Run the code through your judge.
3. Build `judge_result`.
4. Resume/continue the LangGraph workflow.
5. Return the normalized result to the frontend.

Example response:

```json
{
  "status": "accepted",
  "judge_result": {
    "status": "Accepted",
    "accepted": true,
    "runtime_ms": 10,
    "memory_kb": 4096,
    "tests_passed": 10,
    "tests_total": 10
  },
  "next_action": "EVALUATE"
}
```

## Important architecture issue

Opening an external LeetCode/Codeforces URL does NOT give your backend the platform's judge result automatically.

The cleanest architecture is:

Browser -> FastAPI -> Code Judge -> `judge_result` -> LangGraph -> Evaluation -> PostgreSQL

If you want users to submit directly on LeetCode/Codeforces, you need a supported integration/API or another mechanism to obtain the result. Otherwise, use your own code-execution/judge service for the Submit button.
