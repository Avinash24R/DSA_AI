/*
  Frontend contract with the LangGraph/FastAPI backend.

  Expected endpoints:

  GET  /api/agent/session/current
       -> {
            user: {name, level, streak, xp, accuracy},
            task: {
              problem_id, title, topic, subtopic, difficulty,
              url, estimated_minutes, attempt_number
            },
            skill: {score, solved, attempts, accuracy, topics: [...]}
          }

  POST /api/agent/session/{problem_id}/submit
       body:
       {
         "language": "cpp",
         "code": "..."
       }

       -> {
            "status": "queued" | "accepted" | "wrong_answer" | "error",
            "judge_result": {...},
            "next_action": "EVALUATE" | "END" | ...
          }

  IMPORTANT:
  The browser cannot automatically obtain a LeetCode/Codeforces judge_result
  just because the user opened an external URL. Your backend must either:
    1. run the submitted code through your own judge, or
    2. integrate with a judge/submission service and normalize its result.
*/

const API_BASE = "/api";

const demoState = {
  user: {
    name: "Arjun",
    level: "Beginner",
    streak: 7,
    xp: 1280,
    accuracy: 72
  },
  task: {
    problem_id: "local:test-1-easy",
    title: "Maximum Sum Subarray of Size K",
    topic: "Sliding Window",
    subtopic: "Fixed Window",
    difficulty: "Easy",
    url: "https://leetcode.com/problems/maximum-sum-subarray-of-size-k/",
    estimated_minutes: 20,
    attempt_number: 1
  },
  skill: {
    score: 42,
    solved: 23,
    attempts: 45,
    accuracy: 72
  }
};

let session = demoState;

document.addEventListener("DOMContentLoaded", async () => {
  restoreDraft();
  bindEvents();

  // Set true when the FastAPI endpoint is ready.
  const USE_BACKEND = true;

  if (USE_BACKEND) {
    await loadSession();
  } else {
    renderSession(session);
  }
});

function bindEvents() {
  document.getElementById("problemUrl").addEventListener("click", () => {
    const url = document.getElementById("problemUrl").href;
    if (!url || url === "#") {
      showStatus("No problem URL is available.", false);
    }
  });

  document.getElementById("saveDraftBtn").addEventListener("click", saveDraft);
  document.getElementById("submitBtn").addEventListener("click", submitSolution);

  document.getElementById("solutionCode").addEventListener("input", () => {
    localStorage.setItem("dsa_solution_draft", document.getElementById("solutionCode").value);
  });
}

async function loadSession() {
  try {
    const response = await fetch(`${API_BASE}/agent/session/current`, {
      credentials: "include"
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    session = await response.json();
    renderSession(session);
  } catch (error) {
    console.warn("Backend session unavailable. Showing UI demo data.", error);
    renderSession(demoState);
  }
}

function renderSession(data) {
  const user = data.user || {};
  const task = data.task || {};
  const skill = data.skill || {};

  setText("userName", user.name || "Student");
  setText("welcomeName", user.name || "Student");
  setText("userLevel", user.level || "Beginner");
  setText("levelPill", user.level || "Beginner");

  setText("streak", user.streak ?? 0);
  setText("xp", user.xp ?? 0);
  setText("accuracy", `${user.accuracy ?? 0}%`);
  setText("metricAccuracy", `${skill.accuracy ?? user.accuracy ?? 0}%`);

  setText("topicName", task.topic || "DSA");
  setText("subtopicName", task.subtopic || "Practice");
  setText("taskTitle", task.title || "Next DSA Problem");
  setText("taskTopic", task.subtopic || task.topic || "DSA");
  setText("estimatedTime", `${task.estimated_minutes ?? 20} min`);
  setText("attemptText", getAttemptText(task.attempt_number));

  const difficulty = task.difficulty || "Easy";
  const badge = document.getElementById("difficultyBadge");
  badge.textContent = difficulty;
  badge.className = `badge difficulty-${difficulty.toLowerCase()}`;

  const url = task.url || "#";
  document.getElementById("problemUrl").href = url;

  setText("skillScore", skill.score ?? 0);
  setText("solved", skill.solved ?? 0);
  setText("attempts", skill.attempts ?? 0);

  const goalSolved = Math.min(skill.solved ?? 0, 5);
  document.getElementById("goalProgress").style.width = `${goalSolved * 20}%`;
  setText("goalText", `${goalSolved} / 5 problems`);
}

function getAttemptText(number) {
  if (!number || number === 1) return "First attempt";
  return `Attempt ${number}`;
}

async function submitSolution() {
  const code = document.getElementById("solutionCode").value.trim();
  const language = document.getElementById("language").value;
  const problemId = session?.task?.problem_id;

  if (!code) {
    showStatus("Paste your solution into the notepad before submitting.", false);
    return;
  }

  if (!problemId) {
    showStatus("No active problem is available.", false);
    return;
  }

  const button = document.getElementById("submitBtn");
  button.disabled = true;
  button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Judging...';

  try {
    const response = await fetch(
      `${API_BASE}/agent/session/${encodeURIComponent(problemId)}/submit`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          language,
          code
        })
      }
    );

    if (!response.ok) {
      const body = await response.text();
      throw new Error(body || `HTTP ${response.status}`);
    }

    const result = await response.json();

    /*
      This is where your backend should have already updated / resumed
      the LangGraph state with judge_result.

      Example:
        judge_result = result.judge_result
        next_action = result.next_action
    */

    handleSubmissionResult(result);
  } catch (error) {
    console.error(error);
    showStatus(
      "Submission could not be sent. Check that the FastAPI submit endpoint is running.",
      false
    );
  } finally {
    button.disabled = false;
    button.innerHTML = '<i class="bi bi-send"></i> Submit Solution';
  }
}

function handleSubmissionResult(result) {
  const status = String(result.status || "").toLowerCase();

  if (status === "accepted") {
    showStatus(
      "Accepted. The judge result has been recorded and the agent can continue to evaluation.",
      true
    );
  } else if (status === "wrong_answer") {
    showStatus(
      "The judge returned Wrong Answer. The agent can now route the session to hint/retry.",
      false
    );
  } else {
    showStatus(
      `Judge result received: ${result.status || "processing"}.`,
      false
    );
  }
}

function saveDraft() {
  const code = document.getElementById("solutionCode").value;
  localStorage.setItem("dsa_solution_draft", code);
  showStatus("Draft saved locally in this browser.", true);
}

function restoreDraft() {
  const draft = localStorage.getItem("dsa_solution_draft");
  if (draft) {
    document.getElementById("solutionCode").value = draft;
  }
}

function showStatus(message, success) {
  const box = document.getElementById("submissionStatus");
  box.textContent = message;
  box.className = `status-box ${success ? "success" : "error"}`;
  box.classList.remove("d-none");
}

function showToast(message) {
  const toast = document.getElementById("appToast");
  toast.querySelector(".toast-body").textContent = message;
  bootstrap.Toast.getOrCreateInstance(toast).show();
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}
