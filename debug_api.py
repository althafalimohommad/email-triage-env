import requests

env_url = "http://localhost:8000"
resp = requests.post(f"{env_url}/reset", json={})
print("RESET CODE:", resp.status_code)
data = resp.json()
print("RESET JSON:", data)
print("KEYS in RESET:", list(data.keys()))

env_id = data.get("env_id", None)
print("ENV ID:", env_id)

payload = {
    "action": {"action_type": "classify", "category": "spam", "priority": 1}
}
if env_id:
    payload["env_id"] = env_id

step_resp = requests.post(
    f"{env_url}/step",
    json=payload
)
print("STEP CODE:", step_resp.status_code)
print("STEP RESP:", step_resp.text)
