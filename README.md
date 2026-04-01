# 📧 Email Triage Environment

> An OpenEnv environment simulating real-world email triage — where an AI agent processes an inbox, classifying emails by urgency, setting priorities, archiving spam, and drafting professional replies.

[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-blue)](https://github.com/meta-pytorch/OpenEnv)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![License: BSD](https://img.shields.io/badge/License-BSD-yellow.svg)](LICENSE)

---

## 🎯 Motivation

Email overload is one of the most common productivity challenges in professional settings. The average knowledge worker receives **120+ emails per day** and spends **~2.5 hours** reading and responding. An AI agent that can intelligently triage emails — sorting by urgency, filtering spam, and even drafting responses — could save hours of human effort daily.

This environment provides a **standardized testbed** for evaluating how well AI agents handle this complex, multi-faceted task.

---

## 🏗️ Environment Description

The Email Triage Environment presents an AI agent with a simulated inbox of emails. The agent processes emails **one at a time** through the standard OpenEnv `step()` / `reset()` / `state()` API.

### How It Works

1. **`reset()`** — Initializes a new episode, loads the email dataset, returns the first email
2. **`step(action)`** — Agent takes an action on the current email; receives the next email + reward
3. **`state()`** — Returns episode metadata (progress, score, missed urgents, etc.)

Each email comes with ground-truth labels. The environment scores the agent's actions using a **partial-credit reward function** that rewards close guesses and penalizes critical mistakes (like missing an urgent email).

---

## 📋 Action Space

| Field | Type | Description |
|---|---|---|
| `action_type` | `classify` \| `reply` \| `archive` \| `flag` \| `escalate` \| `skip` | What to do with the email |
| `category` | `urgent` \| `follow_up` \| `fyi` \| `spam` \| `meeting` \| `approval` | Email classification |
| `priority` | `1` – `5` (1=lowest, 5=critical) | Priority level |
| `reply_content` | `string` (optional) | Draft reply (required for `reply` action) |
| `reason` | `string` (optional) | Brief explanation of the decision |

---

## 👁️ Observation Space

| Field | Type | Description |
|---|---|---|
| `email_id` | `string` | Unique email identifier |
| `sender` | `string` | Sender email address |
| `sender_domain` | `string` | Sender's domain |
| `subject` | `string` | Email subject line |
| `body` | `string` | Full email body |
| `timestamp` | `string` | ISO timestamp |
| `has_attachments` | `bool` | Whether email has attachments |
| `reply_to` | `string?` | Parent email if threaded |
| `inbox_remaining` | `int` | Emails left to process |
| `emails_processed` | `int` | Emails already handled |
| `time_remaining` | `float` | Seconds left in episode |
| `task_description` | `string` | Instructions for the agent |
| `available_actions` | `list[str]` | Valid actions for this task |

---

## 📝 Tasks

### Task 1: Spam Detection (Easy)
- **Emails**: 20
- **Time Limit**: 2 minutes
- **Actions**: `classify` only
- **Goal**: Correctly identify spam vs. legitimate emails
- **Scoring**: Binary accuracy (spam / not-spam)

### Task 2: Multi-Label Categorization (Medium)
- **Emails**: 30
- **Time Limit**: 3 minutes
- **Actions**: `classify`, `flag`, `archive`
- **Goal**: Classify emails into 6 categories AND assign correct priority
- **Scoring**: 60% category accuracy + 40% priority accuracy (with partial credit)

### Task 3: Full Triage + Response Drafting (Hard)
- **Emails**: 40
- **Time Limit**: 5 minutes
- **Actions**: `classify`, `reply`, `flag`, `archive`, `escalate`
- **Goal**: Full professional email triage — classify, prioritize, draft replies, handle urgents
- **Scoring**: 40% category + 20% priority + 30% response quality + 10% urgency handling

---

## 🏆 Reward Function

Rewards provide **partial credit** throughout the episode (not just binary end scores):

| Component | Points | Description |
|---|---|---|
| Category correct | +0.50 | Exact category match |
| Category close | +0.20 | Similar category neighborhood |
| Priority correct | +0.30 | Exact priority match |
| Priority close (±1) | +0.15 | Off by one |
| Action type correct | +0.20 | Appropriate action chosen |
| Reply quality bonus | +0.10 | Relevant keywords in drafted reply |
| **Missing urgent** | **-0.30** | **Penalty for failing to identify urgent emails** |

---

## 🚀 Setup & Usage

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/email_triage_env.git
cd email_triage_env

# Install dependencies
pip install -e .
```

### Running the Server

```bash
# Start the environment server
uvicorn server.app:app --host 0.0.0.0 --port 8000

# Or run directly
python -m server.app
```

### Running the Baseline

```bash
# Set your API key
export OPENAI_API_KEY="your-key-here"   # Linux/Mac
$env:OPENAI_API_KEY = "your-key-here"   # Windows PowerShell

# Run baseline inference
python baseline/inference.py

# Specify model
python baseline/inference.py --model gpt-4
```

### Using the Client

```python
from email_triage_env import EmailTriageEnv, EmailTriageAction

with EmailTriageEnv(base_url="http://localhost:8000") as client:
    result = client.reset()
    print(f"First email: {result.observation.subject}")

    action = EmailTriageAction(
        action_type="classify",
        category="spam",
        priority=1,
        reason="Phishing attempt"
    )
    result = client.step(action)
    print(f"Reward: {result.reward}")
```

### Docker

```bash
# Build
docker build -f server/Dockerfile -t email-triage-env .

# Run
docker run -p 8000:8000 email-triage-env
```

---

## 📊 Baseline Scores

| Task | Model | Score |
|---|---|---|
| Easy (Spam Detection) | GPT-4 | ~0.85 |
| Medium (Multi-Label) | GPT-4 | ~0.72 |
| Hard (Full Triage) | GPT-4 | ~0.58 |

*Scores are approximate and may vary slightly between runs.*

---

## 📁 Project Structure

```
email_triage_env/
├── openenv.yaml              # Environment manifest
├── pyproject.toml             # Python dependencies
├── models.py                  # Pydantic models (Action, Observation, State)
├── client.py                  # WebSocket client
├── __init__.py                # Package exports
├── data/
│   ├── emails_easy.json       # 20 emails for spam detection
│   ├── emails_medium.json     # 30 emails for categorization
│   └── emails_hard.json       # 40 emails for full triage
├── server/
│   ├── app.py                 # FastAPI application
│   ├── email_triage_env_environment.py  # Core environment logic
│   ├── email_generator.py     # Synthetic data generator
│   └── Dockerfile             # Container config
├── tasks/
│   ├── task_easy.py           # Easy task grader
│   ├── task_medium.py         # Medium task grader
│   └── task_hard.py           # Hard task grader
├── baseline/
│   └── inference.py           # Baseline LLM agent
└── README.md                  # This file
```

---

## 🔒 License

BSD License — see [LICENSE](LICENSE) for details.
