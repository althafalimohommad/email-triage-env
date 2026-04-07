# API Configuration Guide

## Overview
The inference script requires two mandatory environment variables:
- **`API_BASE_URL`**: The LiteLLM proxy endpoint (e.g., `https://your-proxy.example.com/v1`)
- **`API_KEY`**: The LiteLLM proxy API key

## Quick Setup (Windows)

### Step 1: Copy the Environment Template
```powershell
copy .env.example .env
```

### Step 2: Edit `.env` File
Open `.env` in your editor and fill in your actual credentials:
```
API_BASE_URL=https://your-litellm-proxy-url/v1
API_KEY=your-actual-api-key-here
```

### Step 3: Run with the Setup Script
```powershell
.\run.bat
```

---

## Quick Setup (Linux/Mac)

### Step 1: Copy the Environment Template
```bash
cp .env.example .env
```

### Step 2: Edit `.env` File
```bash
nano .env  # or your preferred editor
```
Fill in:
```
API_BASE_URL=https://your-litellm-proxy-url/v1
API_KEY=your-actual-api-key-here
```

### Step 3: Run with the Setup Script
```bash
chmod +x run.sh
./run.sh
```

---

## Manual Setup (Without Script)

If you prefer to set environment variables manually:

### Windows (PowerShell)
```powershell
$env:API_BASE_URL="https://your-litellm-proxy-url/v1"
$env:API_KEY="your-actual-api-key-here"
$env:ENV_URL="http://localhost:8000"
python inference.py
```

### Windows (Command Prompt)
```cmd
set API_BASE_URL=https://your-litellm-proxy-url/v1
set API_KEY=your-actual-api-key-here
set ENV_URL=http://localhost:8000
python inference.py
```

### Linux/Mac (Bash)
```bash
export API_BASE_URL="https://your-litellm-proxy-url/v1"
export API_KEY="your-actual-api-key-here"
export ENV_URL="http://localhost:8000"
python inference.py
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_BASE_URL` | ✅ Yes | N/A | LiteLLM proxy endpoint URL |
| `API_KEY` | ✅ Yes | N/A | API key for the proxy |
| `MODEL_NAME` | ❌ No | `meta-llama/Llama-3.3-70B-Instruct` | Model identifier to use |
| `ENV_URL` | ❌ No | `http://localhost:8000` | Email Triage environment server URL |
| `HF_TOKEN` | ❌ No | N/A | Hugging Face API token (if needed) |

---

## Important Notes

### For Local Testing
- Use the `.env` file approach for convenience
- The `run.sh` (Linux/Mac) and `run.bat` (Windows) scripts will automatically load the `.env` file

### For Hackathon Submission
- The validator will automatically inject `API_BASE_URL` and `API_KEY` at runtime
- Do **NOT** hardcode credentials in the code
- The code expects credentials from environment variables only

### Security
- Never commit `.env` to version control
- The `.env.example` file can be committed as a template
- Always keep `API_KEY` secret

---

## Troubleshooting

### Error: "API_KEY environment variable is not set"
1. Verify `.env` file exists in the project root
2. Check that `API_KEY=<value>` is present and not empty in `.env`
3. Make sure you're running `run.bat` (not just `python inference.py`)

### Error: "API_BASE_URL environment variable is not set"
1. Check that `API_BASE_URL=<value>` is in your `.env` file
2. Verify that the URL is correct (should end with `/v1`)
3. Ensure it's not commented out (no `#` at the beginning of the line)

### Script runs but gets "connection refused"
1. Verify the `ENV_URL` points to a running server
2. Local server: `uvicorn server.app:app --host 0.0.0.0 --port 8000 &`
3. Remote server: Use the correct URL in `ENV_URL`

---

## Example `.env` File (Filled In)

```
API_BASE_URL=https://router.huggingface.co/v1
API_KEY=hf_aBcDeFgHiJkLmNoPqRsT
MODEL_NAME=meta-llama/Llama-3.3-70B-Instruct
HF_TOKEN=hf_aBcDeFgHiJkLmNoPqRsT
ENV_URL=http://localhost:8000
```
