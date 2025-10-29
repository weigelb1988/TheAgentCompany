#!/bin/bash
#
# Batch evaluation script for LangGraph agent on TheAgentCompany benchmark
#
# This script runs the LangGraph agent on all tasks (or a subset) and aggregates results.

set -e

# Default configuration
OUTPUTS_PATH=${OUTPUTS_PATH:-"./outputs"}
SERVER_HOSTNAME=${SERVER_HOSTNAME:-"localhost"}
VERSION=${VERSION:-"1.0.0"}
MAX_ITERATIONS=${MAX_ITERATIONS:-100}
TASK_LIST_FILE=${TASK_LIST_FILE:-"tasks.txt"}
START_FROM=${START_FROM:-1}
END_AT=${END_AT:-999}

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  TheAgentCompany Evaluation - LangGraph Agent            ${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Check environment variables
if [ -z "$VLLM_BASE_URL" ]; then
    echo -e "${RED}Error: VLLM_BASE_URL not set${NC}"
    echo "Please set environment variables or create a .env file"
    exit 1
fi

if [ -z "$ENV_LLM_API_KEY" ]; then
    echo -e "${RED}Error: ENV_LLM_API_KEY not set${NC}"
    exit 1
fi

# Check if task list exists
if [ ! -f "$TASK_LIST_FILE" ]; then
    echo -e "${RED}Error: Task list file not found: $TASK_LIST_FILE${NC}"
    echo "Creating default task list with example task..."
    echo "ghcr.io/theagentcompany/example-image:${VERSION} example" > "$TASK_LIST_FILE"
fi

# Create output directory
mkdir -p "$OUTPUTS_PATH"

# Count total tasks
TOTAL_TASKS=$(cat "$TASK_LIST_FILE" | grep -v '^#' | grep -v '^$' | wc -l)

echo -e "${GREEN}Configuration:${NC}"
echo "  Output directory: $OUTPUTS_PATH"
echo "  Server hostname: $SERVER_HOSTNAME"
echo "  Max iterations: $MAX_ITERATIONS"
echo "  Task version: $VERSION"
echo "  Total tasks: $TOTAL_TASKS"
echo "  Task range: $START_FROM to $END_AT"
echo ""

# Load environment from .env if exists
if [ -f .env ]; then
    echo -e "${YELLOW}Loading environment from .env${NC}"
    set -a
    source .env
    set +a
fi

# Statistics
COMPLETED=0
FAILED=0
START_TIME=$(date +%s)

# Create log file
LOG_FILE="$OUTPUTS_PATH/evaluation_log.txt"
echo "Evaluation started at $(date)" > "$LOG_FILE"

# Read tasks and run them
TASK_NUMBER=0
while IFS= read -r line; do
    # Skip comments and empty lines
    if [[ "$line" =~ ^#.*$ ]] || [[ -z "$line" ]]; then
        continue
    fi

    TASK_NUMBER=$((TASK_NUMBER + 1))

    # Skip if before START_FROM or after END_AT
    if [ $TASK_NUMBER -lt $START_FROM ] || [ $TASK_NUMBER -gt $END_AT ]; then
        continue
    fi

    # Parse task line (format: "image_url task_name" or just "image_url")
    read -r TASK_IMAGE TASK_NAME <<< "$line"

    # Extract task name from image if not provided
    if [ -z "$TASK_NAME" ]; then
        TASK_NAME=$(echo "$TASK_IMAGE" | sed 's/.*\/\(.*\):.*/\1/')
    fi

    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Task $TASK_NUMBER/$TOTAL_TASKS: $TASK_NAME${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo "Image: $TASK_IMAGE"
    echo "Started: $(date)"
    echo ""

    # Run the task
    if python3 run_single_task.py \
        --task-image "$TASK_IMAGE" \
        --task-name "$TASK_NAME" \
        --output-dir "$OUTPUTS_PATH" \
        --server-hostname "$SERVER_HOSTNAME" \
        --max-iterations "$MAX_ITERATIONS" 2>&1 | tee -a "$LOG_FILE"; then

        COMPLETED=$((COMPLETED + 1))
        echo -e "${GREEN}✓ Task $TASK_NAME completed successfully${NC}"
    else
        FAILED=$((FAILED + 1))
        echo -e "${RED}✗ Task $TASK_NAME failed${NC}"
    fi

    echo "Task $TASK_NUMBER: $TASK_NAME - Completed: $COMPLETED, Failed: $FAILED" >> "$LOG_FILE"

done < "$TASK_LIST_FILE"

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
HOURS=$((DURATION / 3600))
MINUTES=$(((DURATION % 3600) / 60))
SECONDS=$((DURATION % 60))

# Print summary
echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  EVALUATION COMPLETE                                      ${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo "  Total tasks: $TOTAL_TASKS"
echo "  Completed: $COMPLETED"
echo "  Failed: $FAILED"
echo "  Duration: ${HOURS}h ${MINUTES}m ${SECONDS}s"
echo ""
echo "  Results saved to: $OUTPUTS_PATH"
echo "  Log file: $LOG_FILE"
echo ""

# Run aggregation if results exist
if [ $COMPLETED -gt 0 ]; then
    echo -e "${YELLOW}Aggregating results...${NC}"
    if python3 aggregate_results.py "$OUTPUTS_PATH"; then
        echo -e "${GREEN}✓ Results aggregated${NC}"
    else
        echo -e "${YELLOW}⚠ Could not aggregate results (script may not exist yet)${NC}"
    fi
fi

echo ""
echo -e "${BLUE}To view detailed results:${NC}"
echo "  cat $OUTPUTS_PATH/results_summary.csv"
echo ""

# Exit with error if any tasks failed
if [ $FAILED -gt 0 ]; then
    exit 1
else
    exit 0
fi
