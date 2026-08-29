const API_BASE = "/api";
let session = null;

document.addEventListener("DOMContentLoaded", async () => {
  restoreDraft();
  bindEvents();
  await loadSession();
});

async function ensureSession() {
  // Try stored thread_id first
  const stored = localStorage.getItem("dsa_thread_id");
  if (stored) return stored;

  // Try to create/start a session on the backend (non-blocking fallback to demo)
  try {
    const res = await fetch(`${API_BASE}/agent/session/start?user_id=1`, {
      method: "POST",
    });

    if (res.ok) {
      const body = await res.json();
      const threadId = body.thread_id || body.get?.("thread_id") || body["thread_id"];
      if (threadId) {
        localStorage.setItem("dsa_thread_id", threadId);
        return threadId;
      }
    }
  } catch (e) {
    // ignore and fallback to demo
    console.warn("Could not start session on backend, falling back to demo", e);
  }

  // final fallback
  localStorage.setItem("dsa_thread_id", "guest");
  return "guest";
}

function bindEvents() {

  document.getElementById("saveDraftBtn").addEventListener("click", saveDraft);
  document.getElementById("submitBtn").addEventListener("click", submitSolution);

  document.getElementById("solutionCode").addEventListener("input", () => {
    localStorage.setItem("dsa_solution_draft", document.getElementById("solutionCode").value);
  });
}

async function loadSession() {
  try {
    setAgentStatus("Loading agent session...");
    const threadId = await ensureSession();

    // Prefer the thread-specific endpoint
    let response = await fetch(`${API_BASE}/agent/session/${encodeURIComponent(threadId)}/current`);

    // If not found or backend can't provide, fall back to demo endpoint
    if (!response.ok) {
      response = await fetch(`${API_BASE}/agent/session/current`);
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    session = await response.json();
    renderSession(session);
    setAgentStatus("Ready for submissioin")
  } catch (error) {
    console.error("Backend session unavailable. Showing UI demo data.", error);
    setAgentStatus("backend unavailable")
    showToast("Could not load agent session")
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
  const problemLink = document.getElementById("problemUrl").href = url;
  problemLink.href = url;

  setText("skillScore", skill.score ?? 0);
  setText("solved", skill.solved ?? 0);
  setText("attempts", skill.attempts ?? 0);

  const solved = skill.solved ?? 0;
  const goal = Math.min(solved, 5);
  document.getElementById("goalProgress").style.width = `${goal * 20}%`;
  setText("goalText", goal);
}

function getAttemptText(number) {
  if (!number || number === 1) return "First attempt";
  return `Attempt ${number}`;
}

async function submitSolution() {
  const code = document.getElementById("solutionCode").value.trim();
  const language = document.getElementById("language").value;
  const threadId = session?.thread_id || session?.task?.thread_id || "guest";

  const problemId = session?.task?.problem_id || session?.task?.current_problem_id || null;

  if (!code) {
    showToast("Write your solution first.");
    return;
  }

  if (!problemId) {
    showToast("No active problem.");
    return;
  }


  const button = document.getElementById("submitBtn");
  button.disabled = true;
  button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Judging...';
  setAgentStatus(
        "Submitting solution..."
  );
  try {
    const response = await fetch(
      `${API_BASE}/agent/session/${encodeURIComponent(threadId)}/submit`,
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

    handleSubmissionResult(result);
  } catch (error) {
    console.error(error);
    showToast(error.message)
    setAgentStatus(
            "Submission failed"
        );
  } finally {
    button.disabled = false;
    button.innerHTML = '<i class="bi bi-send"></i> Submit Solution';
  }
}

function handleSubmissionResult(result) {
  console.log(
        "Agent result:",
        result
  );
  const status = String(result.status || "").toLowerCase();
  const judge = result.judge_result || {};
  const judgeCard = document.getElementById("judgeCard");
  judgeCard.classList.remove(
        "d-none"
    );
  const statusElement = document.getElementById("judgeStatus");
  statusElement.textContent = formatStatus(status);
  setText(
        "runtime",
        judge.runtime_ms != null
            ? `${judge.runtime_ms} ms`
            : "-"
    );
  setText(
        "memory",
        judge.memory_kb != null
            ? `${judge.memory_kb} KB`
            : "-"
    );
  if (judge.tests_passed != null && judge.tests_total != null) {
        setText(
            "tests",
            `${judge.tests_passed}/${judge.tests_total}`
          );
    } else {
      setText("tests","-");
    }

  if (status === "accepted") {
    setAgentStatus(
      "Accepted. Agent evaluating solution..."
    );
      showToast(
         "Solution accepted."
      );
  
  } else if (status === "wrong_answer") {
    setAgentStatus(
        "Wrong answer. Agent can provide a hint."
    );
    showToast(
        "Wrong answer."
    );
    
  } else {
    setAgentStatus(
      "Judge returned an error."
    );
    
  }
}

function formatStatus(status) {
    switch (status) {
      case "accepted":
          return "Accepted";
      case "wrong_answer":
          return "Wrong Answer";
      case "error":
          return "Error";
      case "queued":
          return "Queued";
      default:
          return status || "Unknown";
    }

}

function saveDraft() {
  const code = document.getElementById("solutionCode").value;
  localStorage.setItem("dsa_solution_draft", code);
  showToast(
        "Draft saved."
  );

}

function restoreDraft() {
  const draft = localStorage.getItem("dsa_solution_draft");
  if (draft) {
    document.getElementById("solutionCode").value = draft;
  }
}
function setText(id,value) {
    const element =
        document.getElementById(id);
    if (element) {
        element.textContent =
            value;
    }
}
function getAttemptText(number) {
    if (!number || number === 1) {
        return "First attempt";
    }
    return `Attempt ${number}`;
}
function setAgentStatus(message) {
    setText(
        "agentStatus",
        message
    );
}

function showToast(message) {
    const toast =
        document.getElementById(
            "appToast"
        );
    toast.querySelector(
        ".toast-body"
    ).textContent = message;
    bootstrap
        .Toast
        .getOrCreateInstance(toast)
        .show();
}

