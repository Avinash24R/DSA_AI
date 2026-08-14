'''
START
  ↓
load_student
  ↓
evaluate_skill
  ↓
select_topic
  ↓
teach_topic
  ↓
select_problem
  ↓
present_problem
  ↓
WAIT FOR USER
  ↓
evaluate_answer
  ↓
 ┌───────────────┐
 │               │
correct         wrong
 │               │
 │            hint/retry
 │               │
 └───────┬───────┘
         ↓
update_progress
         ↓
END
'''