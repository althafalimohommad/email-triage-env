"""Quick live test — verifies all 3 steps work against the running server."""
import requests
import json
import sys

BASE = "http://localhost:8000"

PASS = "✅"
FAIL = "❌"
errors = []

def check(label, resp, expected=200):
    if resp.status_code == expected:
        print(f"  {PASS} {label:30s} -> {resp.status_code} OK")
        return True
    else:
        msg = f"  {FAIL} {label:30s} -> {resp.status_code} | {resp.text[:120]}"
        print(msg)
        errors.append(msg)
        return False

print()
print("=" * 55)
print("  STEP 2: API Smoke Test")
print("=" * 55)

# Health + root
check("GET /health",      requests.get(f"{BASE}/health"))
check("GET /",            requests.get(f"{BASE}/"))
check("GET /tasks",       requests.get(f"{BASE}/tasks"))

# --- EASY task ---
print()
print("  [easy task]")
r = requests.post(f"{BASE}/reset", params={"task_id": "easy"})
if check("POST /reset?task_id=easy", r):
    obs = r.json()
    print(f"    Subject: {obs.get('subject','?')[:55]}")
    print(f"    Inbox remaining: {obs.get('inbox_remaining','?')}")

    action = {"action_type": "classify", "category": "spam", "priority": 1, "reason": "test"}
    r2 = requests.post(f"{BASE}/step", json={"action": action})
    if r2.status_code == 422:
        r2 = requests.post(f"{BASE}/step", json=action)
    if check("POST /step", r2):
        res = r2.json()
        print(f"    Reward: {res.get('reward','?')}  |  Done: {res.get('done','?')}")

r3 = requests.get(f"{BASE}/state")
if check("GET /state", r3):
    st = r3.json()
    print(f"    Step count: {st.get('step_count','?')}  |  Score: {st.get('current_score','?')}")

# --- MEDIUM task reset ---
print()
print("  [medium task reset]")
r = requests.post(f"{BASE}/reset", params={"task_id": "medium"})
if check("POST /reset?task_id=medium", r):
    obs = r.json()
    print(f"    Inbox remaining: {obs.get('inbox_remaining','?')} (expect ~29)")

# --- HARD task reset ---
print()
print("  [hard task reset]")
r = requests.post(f"{BASE}/reset", params={"task_id": "hard"})
if check("POST /reset?task_id=hard", r):
    obs = r.json()
    print(f"    Inbox remaining: {obs.get('inbox_remaining','?')} (expect ~39)")

print()
print("=" * 55)
if errors:
    print(f"  ❌ {len(errors)} FAILURE(S) found!")
    sys.exit(1)
else:
    print("  ✅ All Step 2 checks PASSED — server working correctly!")
print("=" * 55)
print()
