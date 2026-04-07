#!/bin/bash
# Setup script for Email Triage Environment
# This script helps you configure and run the inference script with proper API credentials

set -e  # Exit on error

echo "================================================"
echo "Email Triage Environment - Setup Script"
echo "================================================"
echo ""

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✓ Found .env file. Loading configuration..."
    export $(cat .env | xargs)
else
    echo "✗ .env file not found!"
    echo ""
    echo "To fix this:"
    echo "  1. Copy .env.example to .env:"
    echo "     cp .env.example .env"
    echo ""
    echo "  2. Edit .env with your actual credentials:"
    echo "     - API_BASE_URL: Your LiteLLM proxy endpoint"
    echo "     - API_KEY: Your LiteLLM proxy API key"
    echo ""
    exit 1
fi

# Verify required variables are set
echo ""
echo "Verifying configuration..."

if [ -z "$API_BASE_URL" ]; then
    echo "✗ ERROR: API_BASE_URL is not set"
    exit 1
fi
echo "✓ API_BASE_URL is set: $API_BASE_URL"

if [ -z "$API_KEY" ]; then
    echo "✗ ERROR: API_KEY is not set"
    exit 1
fi
echo "✓ API_KEY is set (***hidden***)"

echo "✓ MODEL_NAME: ${MODEL_NAME:-meta-llama/Llama-3.3-70B-Instruct}"
echo "✓ ENV_URL: ${ENV_URL:-http://localhost:8000}"
echo ""

# Run the inference script
echo "Starting inference.py..."
export API_BASE_URL API_KEY MODEL_NAME ENV_URL HF_TOKEN LOCAL_IMAGE_NAME
python inference.py "$@"
