# DSA AI Tutor

An AI-powered DSA learning platform built with **FastAPI, LangGraph, Groq, PostgreSQL, Codeforces, and Docker**.

## Features

- Student onboarding with name, email, DSA level, and Codeforces handle
- AI-driven skill evaluation
- Personalized roadmap and topic selection
- AI-generated DSA lessons and topic summaries
- Markdown-rendered AI explanations
- Personalized Codeforces problem selection
- Codeforces submission verification through the Codeforces API
- AI evaluation of submitted solutions
- Persistent progress and saved topic notes in PostgreSQL
- Dashboard, problem, progress, and profile pages
- Dockerized application

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | FastAPI |
| Agent orchestration | LangGraph |
| LLM | Groq |
| Database | PostgreSQL |
| DB administration | pgAdmin |
| Online judge | Codeforces API |
| Deployment | Docker / Docker Compose |

---

# 1. Prerequisites

Install:

- Git
- Docker Desktop
- Python 3.11+ if you want to run the backend locally

Check the installations:

```bash
git --version
docker --version
docker compose version
python --version
```
---

# 2. Clone the Project

```bash
git clone https://github.com/Avinash24R/DSA_AI
cd DSA_AI
```

---

# 3. Configure Environment Variables

Create a `.env` file in the project root.

At minimum:

```env
GROQ_API=your_groq_api_key
```

The application uses this key to communicate with Groq.

If your `docker-compose.yml` or database setup requires additional PostgreSQL environment variables, add those as defined by the project.

**Never commit `.env` or API keys to GitHub.**

Recommended `.gitignore` entries:

```gitignore
.env
.venv/
__pycache__/
*.pyc
```

---

# 4. Build the Docker Images

Build the project images once:

```bash
docker compose build
```

This creates the Docker images required by the application.

After the images have been built, you normally do **not** need to build them every time.

---

# 5. Start the Application

Start the containers in detached mode:

```bash
docker compose up -d
```

Check that the containers are running:

```bash
docker compose ps
```

To see the logs:

```bash
docker compose logs -f
```

You can also view the logs of a specific service:

```bash
docker compose logs -f backend
```

Use the service names from your `docker-compose.yml` if they differ.

---

# 6. Seed the Roadmap

The roadmap must be seeded into PostgreSQL before using the learning flow.

After starting Docker Compose, run the project's roadmap seeder:

```bash
docker compose run --rm roadmap-seeder
```

The seeder populates the roadmap topics used by the AI tutor.

After the seeding process completes, verify that the seeder finished successfully. You can also check the Docker logs:

```bash
docker compose logs roadmap-seeder
```

If your Compose configuration names the seeder service differently, use that service name instead.

### Important

The roadmap should be seeded **after the database is available**.

If the database container has just started and the seeder reports a connection error, wait a few seconds and run the seeder again:

```bash
docker compose run --rm roadmap-seeder
```

You only need to seed the roadmap when the database does not already contain the roadmap data. If the data is already present, avoid repeatedly inserting duplicate seed data unless the project's seeder is designed to be idempotent.

---

# 7. Start / Stop the Application

Once the images have been built, the normal workflow is simple.

### Start

```bash
docker compose up -d
```

### Check containers

```bash
docker compose ps
```

### Stop containers

```bash
docker compose down
```

`docker compose down` removes the containers and Docker network, but normally keeps the built images.

Therefore, after stopping the application, you can start it again with:

```bash
docker compose up -d
```

You do **not** need to build the images again unless something that belongs inside the image has changed.

### Rebuild after code/configuration changes

```bash
docker compose build
docker compose up -d
```

Or:

```bash
docker compose up -d --build
```

### Rebuild without cache

Use this only when you need a completely fresh image build:

```bash
docker compose build --no-cache
docker compose up -d
```

---

# 8. Using the Application

Once Docker is running and the roadmap has been seeded, open the application in your browser at the port configured by your `docker-compose.yml`.

The learning flow is:

```text
Create Profile
      ↓
Start Learning Session
      ↓
AI Evaluates Your Skill
      ↓
AI Selects a Roadmap Topic
      ↓
AI Teaches the Topic
      ↓
Topic Summary Is Saved
      ↓
AI Selects a Problem
      ↓
Solve the Problem on Codeforces
      ↓
Check Your Submission
      ↓
AI Evaluates Your Result
      ↓
Progress Is Updated
      ↓
Next Learning Task
```

---

## Step 1 — Create Your Profile

On the onboarding page, enter:

- Name
- Email
- Current DSA level
- Codeforces handle

The application creates or updates your user profile in PostgreSQL.

Your Codeforces handle is important because the application uses it later to find your submissions.

---

## Step 2 — Start a Learning Session

Start the learning session from the application.

The backend creates a LangGraph session/thread for you.

The session keeps track of your current learning state, including information such as:

- User
- Skill level
- Current topic
- Topic summary
- Current problem
- Problem assignment
- Next action

The browser stores the session information so you can continue the current session.

---

## Step 3 — Learn the Recommended Topic

The AI evaluates your current state and selects an appropriate roadmap topic.

The generated lesson can contain:

- Core concepts
- Intuition
- Pattern recognition
- Examples
- Time complexity
- Space complexity
- Common mistakes
- Problem-solving guidance

The lesson is displayed as formatted Markdown instead of raw Markdown text.

---

## Step 4 — Save and Review Topic Knowledge

The application saves topic summaries in PostgreSQL.

Saved summaries can be used later to review what you learned.

You can access your saved knowledge from the progress/profile sections of the application.

---

## Step 5 — Solve the Recommended Problem

After teaching the topic, the AI selects a problem based on your current learning state.

For a Codeforces problem:

1. Open the problem from the application.
2. Go to Codeforces.
3. Solve the problem using your configured Codeforces account.
4. Submit your solution.
5. Wait until Codeforces finishes judging it.
6. Return to the DSA AI Tutor.

---

## Step 6 — Check Your Codeforces Submission

After Codeforces has judged your submission, use **Check Submission** in the application.

The backend checks the Codeforces API using:

- Your Codeforces handle
- Contest ID
- Problem index
- Problem assignment time

The application looks for a submission made **after the problem was assigned**.

The result can be:

```text
accepted
rejected
not_found
```

If the submission is found, the judge result is passed back into the LangGraph workflow.

The AI can then evaluate the result and continue the learning process.

---

## Step 7 — Continue Learning

After the solution is evaluated, your progress is updated.

The agent can then move toward the next learning task based on your current state.

This creates a continuous learning loop:

```text
Learn
 ↓
Practice
 ↓
Submit
 ↓
Evaluate
 ↓
Update Progress
 ↓
Learn Next Topic
```

---

# 9. Codeforces Requirements

For the Codeforces verification workflow:

1. Enter a valid Codeforces handle during onboarding.
2. Solve the assigned problem using that account.
3. Submit the solution after the problem has been assigned to you.
4. Wait for Codeforces to finish judging.
5. Click **Check Submission** in the application.

If the application displays:

```text
No Codeforces submission found yet.
```

check that:

- The Codeforces handle is correct.
- You submitted using the configured account.
- You solved the assigned problem.
- The submission was made after the assignment.
- Codeforces has finished judging the submission.

---

# 10. Main API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/users` | Create/update user |
| POST | `/api/agent/session/start` | Start AI session |
| GET | `/api/agent/session/{thread_id}/current` | Get current session |
| POST | `/api/agent/session/{thread_id}/submit` | Existing local judge flow |
| POST | `/api/agent/session/{thread_id}/check-submission` | Check Codeforces submission |
| GET | `/api/dashboard?user_id=...` | Dashboard data |
| GET | `/api/progress?user_id=...` | Progress data |
| GET | `/api/roadmap` | Roadmap topics |
| POST | `/api/topic-summary` | Save topic summary |
| GET | `/api/topic-summary?user_id=...` | Retrieve saved summaries |

---

# 11. Testing

The project contains a fake LLM mode for testing so external Groq calls can be avoided.

Set:

```env
USE_FAKE_LLM=1
```

Then run:

```bash
pytest
```

After testing, remove or disable fake LLM mode when you want to use the real Groq model.

---

# 12. Common Problems

## Roadmap is empty

Make sure the database is running and seed the roadmap:

```bash
docker compose up -d
docker compose run --rm roadmap-seeder
```

Then refresh the application.

---

## Containers are not running

Check:

```bash
docker compose ps
```

Then inspect logs:

```bash
docker compose logs -f
```

---

## Groq API error

Check your `.env`:

```env
GROQ_API=your_groq_api_key
```

Then restart the application:

```bash
docker compose down
docker compose up -d
```

Also make sure the model configured in the source is currently available through Groq.

---

## Codeforces submission is not found

Verify:

- Codeforces handle
- Contest ID
- Problem index
- Assignment time
- Submission account
- Submission verdict

Also make sure Codeforces has finished judging before checking again.

---

## Old LangGraph session returns 404

The browser may still contain an old `dsa_thread_id`.

Clear it from the browser console:

```javascript
localStorage.removeItem("dsa_thread_id");
location.reload();
```

Then start a new learning session.

If sessions need to survive backend restarts, use persistent LangGraph checkpoint storage instead of an in-memory checkpointer.

---

# 13. Useful Docker Commands

### Start

```bash
docker compose up -d
```

### Stop

```bash
docker compose down
```

### Build images

```bash
docker compose build
```

### Build and start

```bash
docker compose up -d --build
```

### Rebuild without cache

```bash
docker compose build --no-cache
```

### Check containers

```bash
docker compose ps
```

### View all logs

```bash
docker compose logs -f
```

### View a service's logs

```bash
docker compose logs -f backend
```

### Restart services

```bash
docker compose restart
```

### Seed roadmap

```bash
docker compose run --rm roadmap-seeder
```

---

# 14. Complete Setup — Quick Start

For someone setting up the project for the first time:

```bash
git clone https://github.com/Avinash24R/DSA_AI
cd DSA_AI
```

Create `.env`:

```env
GROQ_API=your_groq_api_key
```

Build the Docker images:

```bash
docker compose build
```

Start the containers:

```bash
docker compose up -d
```

Seed the roadmap:

```bash
docker compose run --rm roadmap-seeder
```

Check the containers:

```bash
docker compose ps
```

Then open the application using the port configured in `docker-compose.yml`.

Create your profile, start a learning session, study the AI-generated lesson, solve the recommended Codeforces problem, and return to the application to check your submission.

---

# 15. Daily Usage

After the initial setup, you normally only need:

```bash
docker compose up -d
```

When finished:

```bash
docker compose down
```

If you have changed source files that are copied into Docker images, rebuild:

```bash
docker compose build
docker compose up -d
```

You do not need to rebuild just because you stopped and started the containers.

---

# 16. Desktop Installer (Windows / macOS / Linux)

Instead of running Docker commands by hand, you can use the desktop
launcher: a small GUI that checks Docker and Python are installed,
builds the images, starts/stops the stack, and seeds the Codeforces +
LeetCode problem pools, all from one window with a desktop icon.

See [`desktop/README.md`](desktop/README.md) for the installer for
your OS. Quick version:

```bash
# Windows: double-click desktop/install_windows.bat
# macOS:
./desktop/install_macos.sh
# Linux:
./desktop/install_linux.sh
```

Each installer creates a `.env` from the template if you don't have
one yet (you'll still need to add your `GROQ_API` key) and adds a
desktop icon that opens the launcher. You can also skip the installer
and just run `python3 desktop/dsa_tutor_launcher.py` directly — it
only needs the Python standard library.

---

## License

This project is licensed under the [MIT License](LICENSE) — you're free to use, modify, and distribute it, including commercially, as long as the original copyright and license notice are kept.

Contributions are welcome — open an issue or pull request on the repository below.

## Author

- Repository: https://github.com/Avinash24R/DSA_AI
- Author: Avinash Rout
