const API_BASE = "/api";

let session = null;

document.addEventListener("DOMContentLoaded", async () => {
  bindEvents();

  const userId = localStorage.getItem("dsa_user_id");
  const threadId = localStorage.getItem("dsa_thread_id");

  const onboarding = document.getElementById("onboarding");
  if (onboarding) {
    if (userId && threadId) {
      hideOnboarding();
      await loadSession();
    } else {
      showOnboarding();
    }
  }

  /*
   * Route by a unique element on each page rather than
   * matching text that also appears in the shared sidebar
   * (e.g. every page's nav contains the word "Problems").
   */

  if (document.getElementById("progressList")) {
    await loadProgress();
  }

  if (document.getElementById("savedSummaries")) {
    await loadProfile();
  }
});

function bindEvents() {
  const startButton = document.getElementById("startLearningBtn");
  if (startButton) startButton.addEventListener("click", createUserAndSession);

  const continueButton = document.getElementById("continueProblemBtn");
  if (continueButton) continueButton.addEventListener("click", showProblem);

  const saveDraftButton = document.getElementById("saveDraftBtn");
  if (saveDraftButton) saveDraftButton.addEventListener("click", saveDraft);

  const checkSubmissionButton =
    document.getElementById(
        "checkSubmissionBtn"
    );

  if (checkSubmissionButton) {
      checkSubmissionButton.addEventListener("click",checkCodeforcesSubmission);
  }
  const code = document.getElementById("solutionCode");
  if (code) {
    restoreDraft();
    code.addEventListener("input", () => {
      localStorage.setItem(getDraftKey(), code.value);
    });
  }
}

function showOnboarding() {
  const onboarding = document.getElementById("onboarding");
  const application = document.getElementById("application");
  if (onboarding) onboarding.classList.remove("d-none");
  if (application) application.classList.add("d-none");
}

function hideOnboarding() {
  const onboarding = document.getElementById("onboarding");
  const application = document.getElementById("application");
  if (onboarding) onboarding.classList.add("d-none");
  if (application) application.classList.remove("d-none");
}

async function createUserAndSession() {
  const name = document.getElementById("onboardingName")?.value.trim();
  const email = document.getElementById("onboardingEmail")?.value.trim();
  const level = document.getElementById("onboardingLevel")?.value;
  const codeforcesHandle = document.getElementById("onboardingCodeforces")?.value.trim();
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
  button.disabled = true;
  button.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Starting AI Agent...`;

  try {

    const userResponse = await fetch(`${API_BASE}/users`, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        name: name,
        email: email,
        level: level,
        codeforces_handle: codeforcesHandle,
      }),
    });

    const user = await readResponse(userResponse);

    if (!user.user_id) {
      throw new Error("Backend did not return user_id");
    }

    localStorage.setItem("dsa_user_id", String(user.user_id));

    /*
     * 2. Start agent
     */

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
    hideOnboarding();

    /*
     * 3. Load actual agent state
     */

    await loadSession();
  } catch (error) {
    console.error("START AGENT ERROR:", error);

    showToast(error.message);
  } finally {
    button.disabled = false;

    button.innerHTML = `<i class="bi bi-play-fill"></i>
             Start Learning`;
  }
}

async function loadSession() {
  const threadId = localStorage.getItem("dsa_thread_id");

  if (!threadId) {
    showOnboarding();
    return;
  }
  setAgentStatus("Loading AI session...");

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
    else setAgentStatus("Agent is preparing your lesson...");
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
  setText("userName", userName);
  setText("welcomeName", userName);
  setText("userLevel", level);
  setText("topicName", topicName);
  setText("subtopicName", task.subtopic || "Learning");
  setText("xp", user.xp ?? 0);
  setText("accuracy", `${user.accuracy ?? skill.accuracy ?? 0}%`);
  setText("profileCodeforces",user.codeforces_handle || "-");
  const avatar = document.getElementById("avatarLetter");

  if (avatar) {
    avatar.textContent = userName.charAt(0).toUpperCase();
  }

  const cfHandle =
    user.codeforces_handle;

  const cfElement =
      document.getElementById(
          "profileCodeforces"
      );
  if (cfElement && cfHandle) {
      cfElement.innerHTML = `
          <a
              href="https://codeforces.com/profile/${encodeURIComponent(cfHandle)}"
              target="_blank"
              rel="noopener noreferrer"
          >
              ${escapeHtml(cfHandle)}
          </a>
      `;
  }

  renderProblem(task);

  /*
   * Profile page
   */

  setText("profileName", userName);

  setText("profileEmail", user.email || "student@example.com");

  setText("profileLevel", level);

  setText("profileXp", user.xp ?? 0);

  setText("profileAccuracy", `${user.accuracy ?? skill.accuracy ?? 0}%`);

  setText("profileStreak", user.streak ?? 0);

  const profileAvatar = document.getElementById("profileAvatar");

  if (profileAvatar) {
    profileAvatar.textContent = userName.charAt(0).toUpperCase();
  }
}


/*
 * The LangGraph agent state has used a few different
 * field names over time (old vs. new graph versions).
 * These helpers read from every known shape so the
 * frontend keeps working no matter which backend
 * version is running.
 */

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

  return (
    topic.id ??
    data?.current_topic_id ??
    data?.roadmap_topic_id ??
    null
  );
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
  const card = document.getElementById("summaryCard");

  const summaryElement = document.getElementById("topicSummary");

  if (!summaryElement) {
    return;
  }

  if (typeof summary === "object") {
    summaryElement.textContent = JSON.stringify(summary, null, 2);
  } else {
    summaryElement.textContent = summary;
  }

  if (card) {
    card.classList.remove("d-none");
  }

  const step = document.getElementById("agentStepSummary");

  if (step) {
    step.classList.add("active");
  }

  setText("summarySaved", "AI summary generated");
}

async function saveTopicSummary(data, summary) {
  const userId = localStorage.getItem("dsa_user_id");

  if (!userId || !summary) {
    return;
  }

  /*
   * This endpoint must be added
   * to the backend:
   *
   * POST /api/topic-summary
   */

  try {
    const topicName = getTopicName(data);

    const topicId = getTopicId(data);

    const response = await fetch(`${API_BASE}/topic-summary`, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        user_id: Number(userId),

        roadmap_topic_id: topicId,

        topic_name: topicName,

        summary:
          typeof summary === "string" ? summary : JSON.stringify(summary),
      }),
    });

    /*
     * If endpoint hasn't been added yet,
     * don't break the learning UI.
     */

    if (response.status === 404) {
      setText("summarySaved", "Summary ready");

      return;
    }

    await readResponse(response);

    setText("summarySaved", "Saved to your learning history");
  } catch (error) {
    console.error("SUMMARY SAVE ERROR:", error);

    setText("summarySaved", "Summary generated");
  }
}
async function checkCodeforcesSubmission(){
  const thread_id= localStorage.getItem("dsa_thread_id")
  if (!thread_id){
    showToast("No active agent session")
    return
  }
  const button = document.getElementById("checkSubmissionBtn");
  if (button){
    button.disabled = true;
    button.innerHTML = `
      <span class="spinner-border spinner-border-sm">
      </span>
      Checking...
    `;
  }
  try {
    const response = await fetch(
      `${API_BASE}/agent/session/`+
      `${encodeURIComponent(thread_id)}`+
      `/check-submission`,
      {
        method: "POST",
        headers: {
            "Content-Type":
                "application/json"
        }
      }
    )

    const result = await readResponse(response);
    console.log("CODEFORCES CHECK:", result);
    renderCodeforcesResult(result);
    if(result.judge_result?.accepted){
      showToast("Accepted AI is evaluating your solution")
      setTimeout(loadSession, 1000);
    }else if (result.judge_result?.found){
      showToast(`Submission found : ${result.judge_result.verdict}`);
    }else{
      showToast("No submission found yet");
    }

  }catch(error){
    console.error(
        "CODEFORCES CHECK ERROR:",
        error
    );
    showToast(
        error.message ||
        "Could not check Codeforces submission."
    );
  }finally{
    if (button) {
      button.disabled = false;
      button.innerHTML = `
          <i class="bi bi-arrow-repeat"></i>
          Check Submission
      `;
    }
  }
}
function renderCodeforcesResult(result) {
    const judge =
        result?.judge_result || {};
    const card =
        document.getElementById(
            "judgeCard"
        );
    if (card) {
        card.classList.remove(
            "d-none"
        );
    }
    setText(
        "judgeStatus",
        judge.found
            ? (
                judge.verdict ||
                "UNKNOWN"
              )
            : "NOT SUBMITTED"
    );
    setText(
        "runtime",
        "-"
    );
    setText(
        "memory",
        "-"
    );
    setText(
        "tests",
        "-"
    );
    const errorElement =
        document.getElementById(
            "judgeError"
        );
    if (errorElement) {
        if (!judge.found) {
            errorElement.textContent =
                "No submission found for this problem yet.";
            errorElement.classList.remove(
                "d-none"
            );
        } else {
            errorElement.textContent =
                `Codeforces verdict: ${
                    judge.verdict
                }`;

            errorElement.classList.remove(
                "d-none"
            );
        }
    }
}
function isProblemReady(data) {
  const task = data?.task || {};

  return Boolean(task.title || task.problem_id || task.current_problem_id);
}

function renderProblem(task) {
  if (!task) {
    return;
  }

  setText("taskTitle", task.title || "Problem");

  setText("taskTopic", task.subtopic || task.topic || "DSA");

  setText(
    "estimatedTime",
    task.estimated_minutes ? `${task.estimated_minutes} min` : "-",
  );

  setText("attemptText", getAttemptText(task.attempt_number));

  const difficulty = task.difficulty || "Easy";

  const badge = document.getElementById("difficultyBadge");

  if (badge) {
    badge.textContent = difficulty;

    badge.className = `difficulty ${difficulty.toLowerCase()}`;
  }

  const description = document.getElementById("problemDescription");

  if (description) {
    description.textContent =
      task.description || "Open the problem to see the full statement.";
  }

  const url = document.getElementById("problemUrl");

  if (url) {
    if (task.url) {
      url.href = task.url;

      url.classList.remove("disabled");
    } else {
      url.href = "#";

      url.classList.add("disabled");
    }
  }

  /*
   * Codeforces page has its own
   * "Solve on Codeforces" link -
   * point it at the real problem URL.
   */

  const cfLink = document.getElementById("solveOnCodeforcesBtn");

  if (cfLink) {
    if (task.url) {
      cfLink.href = task.url;

      cfLink.classList.remove("disabled");
    } else {
      cfLink.href = "#";

      cfLink.classList.add("disabled");
    }
  }
}

function showProblem() {
  const problemCard = document.getElementById("problemCard");

  const editorCard = document.getElementById("editorCard");

  if (problemCard) {
    problemCard.classList.remove("d-none");
  }

  if (editorCard) {
    editorCard.classList.remove("d-none");
  }

  const step = document.getElementById("agentStepProblem");

  if (step) {
    step.classList.add("active");
  }

  setAgentStatus("Ready to solve");

  document.getElementById("problemCard")?.scrollIntoView({
    behavior: "smooth",
  });
}

function markProblemReady() {
  setAgentStatus("Topic ready");

  const button = document.getElementById("continueProblemBtn");

  if (button) {
    button.disabled = false;
  }
}

/* =========================================================
   SUBMISSION
========================================================= */

async function submitSolution() {
  const threadId = localStorage.getItem("dsa_thread_id");

  if (!threadId) {
    showToast("No active agent session.");

    return;
  }

  const code = document.getElementById("solutionCode")?.value.trim();

  const language = document.getElementById("language")?.value || "cpp";

  if (!code) {
    showToast("Write your solution first.");

    return;
  }

  const button = document.getElementById("submitBtn");

  button.disabled = true;

  button.innerHTML = `<span class="spinner-border spinner-border-sm"></span>
         Judging...`;

  try {
    /*
     * IMPORTANT:
     *
     * This matches the real backend:
     *
     * POST
     * /api/agent/session/{thread_id}/submit
     */

    const response = await fetch(
      `${API_BASE}/agent/session/` + `${encodeURIComponent(threadId)}/submit`,
      {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          language,
          code,
        }),
      },
    );

    const result = await readResponse(response);

    console.log("SUBMISSION:", result);

    renderJudgeResult(result);

    /*
     * Refresh agent state after
     * accepted submission.
     */

    if (result.status === "accepted") {
      showToast("Accepted. Agent is evaluating your progress.");

      setTimeout(loadSession, 1000);
    }
  } catch (error) {
    console.error("SUBMISSION ERROR:", error);

    showToast(error.message);
  } finally {
    button.disabled = false;

    button.innerHTML = `<i class="bi bi-send"></i>
             Submit Solution`;
  }
}

/* =========================================================
   JUDGE RESULT
========================================================= */

function renderJudgeResult(result) {
  const judge = result?.judge_result || result?.judge || {};

  const card = document.getElementById("judgeCard");

  if (card) {
    card.classList.remove("d-none");
  }

  setText("judgeStatus", formatStatus(result.status || judge.status));

  setText("runtime", judge.runtime_ms != null ? `${judge.runtime_ms} ms` : "-");

  setText("memory", judge.memory_kb != null ? `${judge.memory_kb} KB` : "-");

  setText(
    "tests",
    judge.tests_passed != null
      ? `${judge.tests_passed}/${judge.tests_total}`
      : "-",
  );

  const error = judge.error || "";

  const errorElement = document.getElementById("judgeError");

  if (errorElement) {
    if (error) {
      errorElement.textContent = error;

      errorElement.classList.remove("d-none");
    } else {
      errorElement.classList.add("d-none");
    }
  }
}

/* =========================================================
   PROGRESS
========================================================= */

async function loadProgress() {
  const userId = localStorage.getItem("dsa_user_id");

  if (!userId) {
    return;
  }

  try {
    const response = await fetch(
      `${API_BASE}/progress?user_id=${encodeURIComponent(userId)}`,
    );

    const data = await readResponse(response);

    const skill = data.skill_profile || {};

    setText("skillScore", skill.score ?? skill.average_skill_score ?? 0);

    setText("solved", skill.solved ?? 0);

    setText("attempts", skill.attempts ?? 0);

    setText("metricAccuracy", `${skill.accuracy ?? 0}%`);

    renderProgressList(data.progress);
  } catch (error) {
    console.error("PROGRESS ERROR:", error);

    showToast(error.message);
  }
}

function renderProgressList(progress) {
  const container = document.getElementById("progressList");

  if (!container) {
    return;
  }

  if (!progress) {
    container.textContent = "No progress data yet.";

    return;
  }

  /*
   * Backend Tool may return either
   * an array or an object.
   */

  if (Array.isArray(progress)) {
    if (!progress.length) {
      container.textContent = "No topic progress yet.";

      return;
    }

    container.innerHTML = progress
      .map((item) => {
        const name = item.topic_name || item.name || "Topic";

        const score = item.skill_score ?? item.score ?? 0;

        return `
                        <div class="progress-row">

                            <div>
                                <strong>
                                    ${escapeHtml(name)}
                                </strong>

                                <small>
                                    Skill Score
                                </small>
                            </div>

                            <strong>
                                ${score}/100
                            </strong>

                        </div>
                    `;
      })
      .join("");

    return;
  }

  container.innerHTML = `<pre class="data-box">${escapeHtml(
    JSON.stringify(progress, null, 2),
  )}</pre>`;
}

/* =========================================================
   PROFILE
========================================================= */

async function loadProfile() {
  /*
   * Current agent session already
   * contains user information.
   */

  await loadSession();

  /*
   * Saved summaries require:
   *
   * GET /api/topic-summary?user_id=X
   *
   */

  await loadSavedSummaries();
}

async function loadSavedSummaries() {
  const userId = localStorage.getItem("dsa_user_id");

  const container = document.getElementById("savedSummaries");

  if (!container || !userId) {
    return;
  }

  try {
    const response = await fetch(
      `${API_BASE}/topic-summary?user_id=${encodeURIComponent(userId)}`,
    );

    if (response.status === 404) {
      container.innerHTML = `<p class="text-secondary">
                    Saved topic history will appear here.
                </p>`;

      return;
    }

    const data = await readResponse(response);

    const summaries = Array.isArray(data) ? data : data.summaries || [];

    if (!summaries.length) {
      container.innerHTML = `<p class="text-secondary">
                    No saved topic summaries yet.
                </p>`;

      return;
    }

    container.innerHTML = summaries
      .map((item) => {
        return `
                        <article class="saved-summary">

                            <h4>
                                ${escapeHtml(item.topic_name || "Topic")}
                            </h4>

                            <p>
                                ${escapeHtml(item.summary || "")}
                            </p>

                        </article>
                    `;
      })
      .join("");
  } catch (error) {
    console.error("SUMMARY HISTORY ERROR:", error);

    container.innerHTML = `<p class="text-secondary">
                Could not load saved summaries.
            </p>`;
  }
}

/* =========================================================
   DRAFT
========================================================= */

function getDraftKey() {
  const problemId =
    session?.task?.problem_id || session?.task?.current_problem_id || "current";

  return `dsa_draft_${problemId}`;
}

function saveDraft() {
  const code = document.getElementById("solutionCode")?.value || "";

  localStorage.setItem(getDraftKey(), code);

  showToast("Draft saved.");
}

function restoreDraft() {
  const code = document.getElementById("solutionCode");

  if (!code) {
    return;
  }

  const draft = localStorage.getItem(getDraftKey());

  if (draft) {
    code.value = draft;
  }
}

/* =========================================================
   HELPERS
========================================================= */

async function readResponse(response) {
  const text = await response.text();

  let data;

  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = {
      detail: text,
    };
  }

  if (!response.ok) {
    throw new Error(data.detail || data.message || `HTTP ${response.status}`);
  }

  return data;
}

function setText(id, value) {
  const element = document.getElementById(id);

  if (element) {
    element.textContent = value ?? "";
  }
}

function setAgentStatus(message) {
  setText("agentStatusBadge", message);
}

function formatStatus(status) {
  switch (String(status || "").toLowerCase()) {
    case "accepted":
      return "Accepted";

    case "wrong_answer":
      return "Wrong Answer";

    case "compilation_error":
      return "Compilation Error";

    case "runtime_error":
      return "Runtime Error";

    case "time_limit_exceeded":
      return "Time Limit Exceeded";

    default:
      return status || "Unknown";
  }
}

function getAttemptText(number) {
  if (!number || number === 1) {
    return "First attempt";
  }

  return `Attempt ${number}`;
}

function showToast(message) {
  const toast = document.getElementById("appToast");

  if (!toast) {
    console.log(message);

    return;
  }

  const body = toast.querySelector(".toast-body");

  if (body) {
    body.textContent = message;
  }

  if (window.bootstrap) {
    bootstrap.Toast.getOrCreateInstance(toast).show();
  }
}
function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}