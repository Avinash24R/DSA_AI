const API_BASE = "/api";

let session = null;

document.addEventListener("DOMContentLoaded", async () => {
  bindEvents();

  const userId = localStorage.getItem("dsa_user_id");
  const threadId = localStorage.getItem("dsa_thread_id");

  /*
   * index.html: onboarding form OR a
   * "welcome back" card if a session
   * already exists in this browser.
   */

  const onboarding = document.getElementById("onboarding");

  if (onboarding) {
    if (userId && threadId) {
      await showExistingSession();
    } else {
      showOnboarding();
    }
    return;
  }

  /*
   * Every other page needs a session.
   * Bounce back to the start form if
   * one hasn't been created yet.
   */

  if (!userId || !threadId) {
    window.location.href = "index.html";
    return;
  }

  /*
   * Route by a unique element on each page rather than
   * matching text that also appears in the shared sidebar.
   */

  await loadSession();

  if (document.getElementById("progressList")) {
    await loadProgressPage();
  }

  if (document.getElementById("profileRoadmapList")) {
    await loadProfilePage();
  }

  if (document.getElementById("solvedProblemsList")) {
    await loadSolvedProblems();
  }
});

function bindEvents() {
  const startForm = document.getElementById("startForm");
  if (startForm) {
    startForm.addEventListener("submit", (event) => {
      event.preventDefault();
      createUserAndSession();
    });
  }

  document.querySelectorAll("[data-reset-session]").forEach((el) => {
    el.addEventListener("click", (event) => {
      event.preventDefault();
      resetSession();
    });
  });

  const checkSubmissionButton = document.getElementById("checkSubmissionBtn");
  if (checkSubmissionButton) {
    checkSubmissionButton.addEventListener("click", checkCodeforcesSubmission);
  }
}

function resetSession() {
  localStorage.removeItem("dsa_user_id");
  localStorage.removeItem("dsa_thread_id");
  window.location.href = "index.html";
}

function showOnboarding() {
  const onboarding = document.getElementById("onboarding");
  const existing = document.getElementById("existingSession");
  if (onboarding) onboarding.style.display = "";
  if (existing) existing.style.display = "none";
}

async function showExistingSession() {
  const onboarding = document.getElementById("onboarding");
  const existing = document.getElementById("existingSession");
  if (onboarding) onboarding.style.display = "none";
  if (existing) existing.style.display = "";

  const threadId = localStorage.getItem("dsa_thread_id");

  try {
    const response = await fetch(
      `${API_BASE}/agent/session/${encodeURIComponent(threadId)}/current`,
    );
    const data = await readResponse(response);

    const userName = data?.user?.name || "there";
    const topicName = getTopicName(data);

    setText(
      "existingSessionText",
      `Welcome back, ${userName}. You're currently learning ${topicName}.`,
    );
  } catch (error) {
    console.error("EXISTING SESSION ERROR:", error);
    setText(
      "existingSessionText",
      "Your learning session is ready.",
    );
  }
}

async function createUserAndSession() {
  const name = document.getElementById("onboardingName")?.value.trim();
  const email = document.getElementById("onboardingEmail")?.value.trim();
  const level = document.getElementById("onboardingLevel")?.value;
  const codeforcesHandle = document
    .getElementById("onboardingCodeforces")
    ?.value.trim();

  if (!name) {
    showToast("Please enter your name.");
    return;
  }

  if (!email) {
    showToast("Please enter your email.");
    return;
  }

  if (!codeforcesHandle) {
    showToast("Please enter your Codeforces handle.");
    return;
  }

  const button = document.getElementById("startLearningBtn");
  const originalContent = button?.innerHTML;
  if (button) {
    button.disabled = true;
    button.innerHTML = `<span class="spinner">↻</span> Starting AI agent…`;
  }

  try {
    const userResponse = await fetch(`${API_BASE}/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        email,
        level,
        codeforces_handle: codeforcesHandle,
      }),
    });

    const user = await readResponse(userResponse);

    if (!user.user_id) {
      throw new Error("Backend did not return user_id");
    }

    localStorage.setItem("dsa_user_id", String(user.user_id));

    const sessionResponse = await fetch(`${API_BASE}/agent/session/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: user.user_id }),
    });
    const sessionData = await readResponse(sessionResponse);

    if (!sessionData.thread_id) {
      throw new Error("Agent did not return thread_id");
    }

    localStorage.setItem("dsa_thread_id", sessionData.thread_id);

    window.location.href = "home.html";
  } catch (error) {
    console.error("START AGENT ERROR:", error);
    showToast(error.message);
  } finally {
    if (button) {
      button.disabled = false;
      button.innerHTML = originalContent;
    }
  }
}

/* =========================================================
   SESSION
========================================================= */

async function loadSession() {
  const threadId = localStorage.getItem("dsa_thread_id");

  if (!threadId) {
    window.location.href = "index.html";
    return;
  }

  setAgentStatus("Loading AI session…");

  try {
    const response = await fetch(
      `${API_BASE}/agent/session/${encodeURIComponent(threadId)}/current`,
    );
    session = await readResponse(response);

    console.log("CURRENT AGENT SESSION:", session);

    renderSession(session);

    const summary = getTopicSummary(session);

    if (summary) {
      renderTopicSummary(summary);
      await saveTopicSummary(session, summary);
    }

    if (isProblemReady(session)) markProblemReady();
    else setAgentStatus("Agent is preparing your lesson…");
  } catch (error) {
    console.error("SESSION ERROR:", error);
    setAgentStatus("Agent session unavailable");
    showToast(error.message);
  }
}

function renderSession(data) {
  const user = data?.user || {};
  const task = data?.task || {};
  const skill = data?.skill || {};

  const userName = user.name || "Student";
  const level = user.level || "Beginner";
  const topicName = getTopicName(data);

  /* Shared topbar (home / problem / progress / user pages) */
  setText("userName", userName);
  setText("userLevel", level);

  const avatar = document.getElementById("avatarLetter");
  if (avatar) avatar.textContent = userName.charAt(0).toUpperCase();

  /* Home page */
  setText("topicName", topicName);
  setText("homeSkill", skill.score ?? 0);
  setText("homeSolved", skill.solved ?? 0);
  setText("homeAccuracy", `${skill.accuracy ?? 0}%`);

  const homeIntro = document.getElementById("homeIntro");
  if (homeIntro) {
    homeIntro.textContent = isProblemReady(data)
      ? `Your next assignment on ${topicName} is ready.`
      : `The AI agent is preparing your ${topicName} lesson.`;
  }

  renderProblem(task);

  /* Profile page header */
  setText("profileName", userName);
  setText("profileEmail", user.email || "—");
  setText("profileLevel", level);
  setText("profileCurrentTopic", topicName);
  setText("profileSkillScore", skill.score ?? 0);
  setText("profileSolved", skill.solved ?? 0);
  setText(
    "profileAccuracyNote",
    `${skill.accuracy ?? 0}% accuracy over ${skill.attempts ?? 0} attempts`,
  );

  const profileAvatar = document.getElementById("profileAvatar");
  if (profileAvatar) profileAvatar.textContent = userName.charAt(0).toUpperCase();

  const cfHandle = user.codeforces_handle;
  const cfElement = document.getElementById("profileCodeforces");
  if (cfElement) {
    if (cfHandle) {
      cfElement.innerHTML = `<a href="https://codeforces.com/profile/${encodeURIComponent(
        cfHandle,
      )}" target="_blank" rel="noopener noreferrer">${escapeHtml(cfHandle)}</a>`;
    } else {
      cfElement.textContent = "—";
    }
  }
}


function getTopicObject(data) {
  const topic = data?.topic;
  return typeof topic === "object" && topic !== null ? topic : {};
}

function getTopicName(data) {
  const topic = getTopicObject(data);
  const task = data?.task || {};

  return (
    topic.name ||
    data?.current_topic ||
    (typeof data?.topic === "string" ? data.topic : null) ||
    task.topic ||
    data?.topic_name ||
    "DSA"
  );
}

function getTopicId(data) {
  const topic = getTopicObject(data);
  return topic.id ?? data?.current_topic_id ?? data?.roadmap_topic_id ?? null;
}

function getTopicSummary(data) {
  const topic = getTopicObject(data);

  return (
    data?.topic_summary ||
    data?.lesson ||
    topic.summary ||
    data?.summary ||
    data?.current_topic_summary ||
    data?.lesson_summary ||
    null
  );
}

function renderTopicSummary(summary) {
  const text = typeof summary === "string" ? summary : JSON.stringify(summary, null, 2);

  renderMarkdown("topicSummary", text, "Waiting for the AI lesson…");

  const step = document.getElementById("agentStepSummary");
  if (step) step.classList.add("active");

  setText("summarySaved", "AI lesson generated");
}

async function saveTopicSummary(data, summary) {
  const userId = localStorage.getItem("dsa_user_id");

  if (!userId || !summary) return;

  try {
    const topicName = getTopicName(data);
    const topicId = getTopicId(data);

    const response = await fetch(`${API_BASE}/topic-summary`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: Number(userId),
        roadmap_topic_id: topicId,
        topic_name: topicName,
        summary: typeof summary === "string" ? summary : JSON.stringify(summary),
      }),
    });

    if (response.status === 404) {
      setText("summarySaved", "Lesson ready (not saved — endpoint missing)");
      return;
    }

    await readResponse(response);
    setText("summarySaved", "Saved to your learning history");
  } catch (error) {
    console.error("SUMMARY SAVE ERROR:", error);
    setText("summarySaved", "Lesson generated");
  }
}


function isProblemReady(data) {
  const task = data?.task || {};
  return Boolean(task.title || task.problem_id || task.id);
}

function renderProblem(task) {
  if (!task) return;

  setText("taskTitle", task.title || "Problem");
  setText("taskTopic", task.subtopic || task.topic || "DSA");
  setText(
    "estimatedTime",
    task.estimated_minutes ? `${task.estimated_minutes} min` : "—",
  );
  setText("attemptText", getAttemptText(task.attempt_number));

  const difficulty = task.difficulty || "Easy";
  const badge = document.getElementById("difficultyBadge");
  if (badge) {
    badge.textContent = difficulty;
    badge.className = `badge ${difficulty.toLowerCase()}`;
  }

  renderMarkdown(
    "problemDescription",
    task.description,
    "Open the problem to see the full statement.",
  );
  renderMarkdown(
    "homeProblemDescription",
    task.description,
    "Problem details will appear here.",
  );

  const url = document.getElementById("problemUrl");
  if (url) {
    url.href = task.url || "#";
    url.classList.toggle("disabled", !task.url);
  }

  const cfLink = document.getElementById("solveOnCodeforcesBtn");
  if (cfLink) {
    cfLink.href = task.url || "#";
    cfLink.classList.toggle("disabled", !task.url);
  }
}

function markProblemReady() {
  setAgentStatus("Topic ready");
  const step = document.getElementById("agentStepProblem");
  if (step) step.classList.add("active");
}

function getAttemptText(number) {
  if (!number || number === 1) return "First attempt";
  return `Attempt ${number}`;
}

async function checkCodeforcesSubmission() {
  const threadId = localStorage.getItem("dsa_thread_id");

  if (!threadId) {
    showToast("No active agent session");
    return;
  }

  const button = document.getElementById("checkSubmissionBtn");
  const originalContent = button?.innerHTML;
  if (button) {
    button.disabled = true;
    button.innerHTML = `<span class="spinner">↻</span> Checking…`;
  }

  try {
    const response = await fetch(
      `${API_BASE}/agent/session/${encodeURIComponent(threadId)}/check-submission`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      },
    );

    const result = await readResponse(response);
    console.log("CODEFORCES CHECK:", result);
    renderCodeforcesResult(result);

    if (result.judge_result?.accepted) {
      showToast("Accepted! The AI is evaluating your progress.");
      setTimeout(loadSession, 1000);
    } else if (result.judge_result?.found) {
      showToast(`Submission found: ${result.judge_result.verdict}`);
    } else {
      showToast("No submission found yet.");
    }
  } catch (error) {
    console.error("CODEFORCES CHECK ERROR:", error);
    showToast(error.message || "Could not check Codeforces submission.");
  } finally {
    if (button) {
      button.disabled = false;
      button.innerHTML = originalContent;
    }
  }
}

function renderCodeforcesResult(result) {
  const judge = result?.judge_result || {};

  const card = document.getElementById("judgeCard");
  if (card) card.style.display = "";

  setText("judgeStatus", judge.found ? judge.verdict || "UNKNOWN" : "NOT SUBMITTED");
  setText("judgeVerdict", judge.verdict || "—");
  setText("submissionId", judge.submission_id ?? "—");
  setText("submissionLanguage", judge.language || "—");

  setText(
    "judgeError",
    judge.found
      ? `Codeforces verdict: ${judge.verdict}`
      : "No submission found for this problem yet.",
  );
}


async function loadProgressPage() {
  const userId = localStorage.getItem("dsa_user_id");
  if (!userId) return;

  try {
    const data = await loadDashboard(userId);
    const agg = computeSkillAggregate(data.skill_profile);

    setText("skillScore", agg.score);
    setText("solved", agg.solved);
    setText("attempts", agg.attempts);
    setText("metricAccuracy", `${agg.accuracy}%`);

    renderTopicProgressList("progressList", data.skill_profile);
  } catch (error) {
    console.error("PROGRESS ERROR:", error);
    showToast(error.message);
  }

  await loadSavedSummaries("progressSummaries");
}

function computeSkillAggregate(skillProfile) {
  const topics = Array.isArray(skillProfile) ? skillProfile : [];

  const solved = topics.reduce((sum, t) => sum + (t.problems_solved || 0), 0);
  const attempts = topics.reduce((sum, t) => sum + (t.problems_attempted || 0), 0);

  const attempted = topics.filter((t) => (t.problems_attempted || 0) > 0);
  const score = attempted.length
    ? Math.round(
        (attempted.reduce((sum, t) => sum + Number(t.skill_score || 0), 0) /
          attempted.length) *
          10,
      ) / 10
    : 0;

  const accuracy = attempts ? Math.round((solved / attempts) * 1000) / 10 : 0;

  return { score, solved, attempts, accuracy };
}

function renderTopicProgressList(containerId, skillProfile) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const topics = Array.isArray(skillProfile) ? skillProfile : [];

  if (!topics.length) {
    container.innerHTML = `<div class="empty-state">Your roadmap will appear here once topics are configured.</div>`;
    return;
  }

  container.innerHTML = topics
    .map((topic) => {
      const name = topic.topic_name || topic.name || "Topic";
      const score = Number(topic.skill_score || 0);
      const solved = topic.problems_solved || 0;
      const attempted = topic.problems_attempted || 0;
      const started = attempted > 0;

      return `
        <div class="topic-row ${started ? "" : "not-started"}">
          <div class="topic-row-info">
            <strong>${escapeHtml(name)}</strong>
            <small>${
              started
                ? `${solved}/${attempted} problems solved`
                : "Not started yet"
            }</small>
          </div>
          <div class="topic-row-bar">
            <div class="track"><div class="fill" style="width:${Math.min(
              score,
              100,
            )}%"></div></div>
            <small>Skill score</small>
          </div>
          <div class="topic-row-score">
            <strong>${started ? score.toFixed(0) : "—"}</strong>
            <small>/ 100</small>
          </div>
        </div>
      `;
    })
    .join("");
}

async function loadProfilePage() {
  const userId = localStorage.getItem("dsa_user_id");
  if (!userId) return;

  try {
    const data = await loadDashboard(userId);
    renderTopicProgressList("profileRoadmapList", data.skill_profile);
  } catch (error) {
    console.error("PROFILE ROADMAP ERROR:", error);
    const container = document.getElementById("profileRoadmapList");
    if (container) {
      container.innerHTML = `<div class="empty-state">Could not load your roadmap.</div>`;
    }
  }

  await loadSavedSummaries("savedSummaries");
}

async function loadDashboard(userId) {
  const response = await fetch(
    `${API_BASE}/dashboard?user_id=${encodeURIComponent(userId)}`,
  );
  return readResponse(response);
}

/* =========================================================
   SOLVED PROBLEMS (problem.html history)
========================================================= */

async function loadSolvedProblems() {
  const userId = localStorage.getItem("dsa_user_id");
  const container = document.getElementById("solvedProblemsList");
  if (!container || !userId) return;

  try {
    const data = await loadDashboard(userId);
    const attempts = Array.isArray(data.recent_attempts) ? data.recent_attempts : [];

    if (!attempts.length) {
      container.innerHTML = `<div class="empty-state">You haven't submitted any problems yet — solve today's assignment to start your history.</div>`;
      return;
    }

    container.innerHTML = attempts
      .map((attempt) => {
        const correct = Boolean(attempt.correct);
        const title = attempt.problem_title || attempt.problem_id || "Problem";
        const topicName = attempt.topic_name || "DSA";
        const difficulty = attempt.difficulty || "—";
        const score =
          attempt.overall_score != null ? Math.round(attempt.overall_score) : null;
        const date = formatDate(attempt.created_at);

        return `
          <div class="attempt-row">
            <div class="attempt-row-icon ${correct ? "correct" : "incorrect"}">
              <i class="bi ${correct ? "bi-check-lg" : "bi-x-lg"}"></i>
            </div>
            <div class="attempt-row-info">
              <strong>${escapeHtml(title)}</strong>
              <small>${escapeHtml(topicName)} · ${escapeHtml(
                difficulty,
              )} · ${escapeHtml(date)}</small>
            </div>
            <div class="attempt-row-score">
              <strong>${score != null ? score : "—"}</strong>
              <small>${score != null ? "/ 100" : correct ? "Solved" : "Attempted"}</small>
            </div>
          </div>
        `;
      })
      .join("");
  } catch (error) {
    console.error("SOLVED PROBLEMS ERROR:", error);
    container.innerHTML = `<div class="empty-state">Could not load your problem history.</div>`;
  }
}


async function loadSavedSummaries(containerId) {
  const userId = localStorage.getItem("dsa_user_id");
  const container = document.getElementById(containerId);

  if (!container || !userId) return;

  try {
    const response = await fetch(
      `${API_BASE}/topic-summary?user_id=${encodeURIComponent(userId)}`,
    );

    if (response.status === 404) {
      container.innerHTML = `<div class="empty-state">Saved topic notes will appear here once the AI generates one.</div>`;
      return;
    }

    const data = await readResponse(response);
    const summaries = Array.isArray(data) ? data : data.summaries || [];

    if (!summaries.length) {
      container.innerHTML = `<div class="empty-state">No saved topic notes yet.</div>`;
      return;
    }

    container.innerHTML = summaries
      .map(
        (item) => `
          <article class="note-card">
            <h4>${escapeHtml(item.topic_name || "Topic")}</h4>
            <div class="markdown-body" data-raw="${escapeHtml(item.summary || "")}"></div>
          </article>
        `,
      )
      .join("");

    /* Render each note's markdown after insertion (safer than building huge HTML strings). */
    container.querySelectorAll(".markdown-body[data-raw]").forEach((el) => {
      const raw = el.getAttribute("data-raw") || "";
      el.innerHTML = renderMarkdownString(raw);
      el.removeAttribute("data-raw");
    });
  } catch (error) {
    console.error("SUMMARY HISTORY ERROR:", error);
    container.innerHTML = `<div class="empty-state">Could not load saved notes.</div>`;
  }
}


function renderMarkdownString(text) {
  if (!text) return "";

  if (window.marked && window.DOMPurify) {
    const html = window.marked.parse(String(text));
    return window.DOMPurify.sanitize(html);
  }

  return escapeHtml(String(text)).replaceAll("\n", "<br>");
}

function renderMarkdown(elementId, text, placeholder) {
  const el = document.getElementById(elementId);
  if (!el) return;

  if (!text) {
    el.innerHTML = `<div class="loading">${escapeHtml(placeholder || "Nothing here yet.")}</div>`;
    return;
  }

  el.innerHTML = renderMarkdownString(text);
}


async function readResponse(response) {
  const text = await response.text();

  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { detail: text };
  }

  if (!response.ok) {
    throw new Error(data.detail || data.message || `HTTP ${response.status}`);
  }

  return data;
}

function setText(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value ?? "";
}

function setAgentStatus(message) {
  setText("agentStatusBadge", message);
}

function formatDate(value) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return "—";
  }
}

let toastTimer = null;
function showToast(message) {
  const toast = document.getElementById("appToast");
  if (!toast) {
    console.log(message);
    return;
  }

  toast.textContent = message;
  toast.classList.add("show");

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 4000);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}