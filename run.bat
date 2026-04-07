@echo off
REM Setup script for Email Triage Environment (Windows)
REM This script helps you configure and run the inference script with proper API credentials

setlocal enabledelayedexpansion

echo.
echo ================================================
echo Email Triage Environment - Setup Script
echo ================================================
echo.

REM Check if .env file exists
if exist ".env" (
    echo [*] Found .env file. Loading configuration...
    
    REM Load .env file variables
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if not "%%a"=="" (
            set "%%a=%%b"
        )
    )
) else (
    echo [-] .env file not found!
    echo.
    echo To fix this:
    echo   1. Copy .env.example to .env:
    echo      copy .env.example .env
    echo.
    echo   2. Edit .env with your actual credentials:
    echo      - API_BASE_URL: Your LiteLLM proxy endpoint
    echo      - API_KEY: Your LiteLLM proxy API key
    echo.
    exit /b 1
)

REM Verify required variables are set
echo.
echo Verifying configuration...
echo.

if "!API_BASE_URL!"=="" (
    echo [-] ERROR: API_BASE_URL is not set
    exit /b 1
)
echo [+] API_BASE_URL is set: !API_BASE_URL!

if "!API_KEY!"=="" (
    echo [-] ERROR: API_KEY is not set
    exit /b 1
)
echo [+] API_KEY is set [hidden]

if "!MODEL_NAME!"=="" (
    set MODEL_NAME=meta-llama/Llama-3.3-70B-Instruct
)
echo [+] MODEL_NAME: !MODEL_NAME!

if "!ENV_URL!"=="" (
    set ENV_URL=http://localhost:8000
)
echo [+] ENV_URL: !ENV_URL!

echo.
echo Starting inference.py...
echo.

python inference.py %*

endlocal
