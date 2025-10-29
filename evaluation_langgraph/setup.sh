#!/bin/bash
#
# Setup script for LangGraph agent evaluation
#
# This script installs dependencies and prepares the environment.

set -e

echo "============================================================"
echo "  LangGraph Agent Evaluation - Setup"
echo "============================================================"
echo ""

# Check if Python 3.10+ is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo ""
    echo "Poetry is not installed. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    echo "✓ Poetry installed"
else
    echo "✓ Poetry found: $(poetry --version)"
fi

# Navigate to langgraph_agent directory
cd ../langgraph_agent

echo ""
echo "Installing LangGraph agent dependencies..."
poetry install

echo ""
echo "✓ Dependencies installed"

# Navigate back to evaluation directory
cd ../evaluation_langgraph

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env created - Please edit it with your configuration"
    echo ""
    echo "Important: Edit .env with your:"
    echo "  - VLLM_BASE_URL and VLLM_API_KEY"
    echo "  - ENV_LLM_API_KEY and ENV_LLM_BASE_URL"
else
    echo ""
    echo "✓ .env file already exists"
fi

# Create outputs directory
mkdir -p outputs
echo "✓ Outputs directory created"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo ""
    echo "⚠ Warning: Docker is not installed"
    echo "  Docker is required to run tasks"
    echo "  Install from: https://docs.docker.com/get-docker/"
else
    echo ""
    echo "✓ Docker found: $(docker --version)"

    # Check if Docker daemon is running
    if docker ps &> /dev/null; then
        echo "✓ Docker daemon is running"
    else
        echo "⚠ Warning: Docker daemon is not running"
        echo "  Start Docker before running evaluation"
    fi
fi

echo ""
echo "============================================================"
echo "  Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your configuration:"
echo "   vi .env"
echo ""
echo "2. Make sure TheAgentCompany services are running:"
echo "   - GitLab (port 8929)"
echo "   - RocketChat (port 3000)"
echo "   - ownCloud (port 8092)"
echo "   - Plane (port 8091)"
echo ""
echo "3. Make sure vLLM server is running:"
echo "   vllm serve <model> --host 0.0.0.0 --port 8000 --api-key <key>"
echo ""
echo "4. Test on example task:"
echo "   python3 run_single_task.py \\"
echo "     --task-image ghcr.io/theagentcompany/example-image:1.0.0 \\"
echo "     --task-name example \\"
echo "     --output-dir ./outputs"
echo ""
echo "5. Run full evaluation:"
echo "   bash run_eval.sh"
echo ""
