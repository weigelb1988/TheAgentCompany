# LangGraph Agent Evaluation Harness

Evaluation infrastructure for running the LangGraph agent on TheAgentCompany benchmark (175 professional tasks).

## Overview

This evaluation harness provides:
- Single task runner for testing individual tasks
- Batch evaluation script for running all 175 tasks
- Result aggregation and analysis tools
- Trajectory logging in TheAgentCompany format
- Integration with Docker-based task containers

## Prerequisites

### Infrastructure

1. **TheAgentCompany Services** (must be running):
   - GitLab: http://localhost:8929
   - RocketChat: http://localhost:3000
   - ownCloud: http://localhost:8092
   - Plane: http://localhost:8091

   See [main README](../README.md) for setup instructions.

2. **vLLM Server** (for agent):
   ```bash
   vllm serve Qwen/Qwen2.5-72B-Instruct-AWQ \
     --host 0.0.0.0 \
     --port 8000 \
     --api-key "your-secret-key" \
     --gpu-memory-utilization 0.9
   ```

3. **Environment LLM** (for NPCs and evaluators):
   - Option A: Use same vLLM server (cost-effective)
   - Option B: Use OpenAI API (better quality)
   - Option C: Use Anthropic API (best quality)

### Software

- Python 3.10+
- Poetry
- Docker and Docker Compose
- 30GB+ free disk space (for Docker images)

## Setup

### Quick Setup

```bash
# Run setup script
bash setup.sh

# Edit configuration
vi .env

# Verify setup
python3 --version
poetry --version
docker --version
```

### Manual Setup

1. Install LangGraph agent dependencies:
   ```bash
   cd ../langgraph_agent
   poetry install
   cd ../evaluation_langgraph
   ```

2. Create .env file:
   ```bash
   cp .env.example .env
   # Edit with your configuration
   vi .env
   ```

3. Create outputs directory:
   ```bash
   mkdir -p outputs
   ```

## Configuration

### Environment Variables (.env)

```bash
# Agent LLM (vLLM)
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_API_KEY=your-secret-key
LLM_MODEL=Qwen/Qwen2.5-72B-Instruct-AWQ

# Environment LLM (NPCs, evaluators)
ENV_LLM_API_KEY=your-key
ENV_LLM_BASE_URL=http://localhost:8000/v1
ENV_LLM_MODEL=Qwen/Qwen2.5-72B-Instruct-AWQ

# Services
SERVER_HOSTNAME=localhost

# Agent settings
MAX_ITERATIONS=100
ENABLE_REFLECTION=true
```

## Usage

### Test Single Task

Run the agent on one task to verify setup:

```bash
# Load environment
source .env

# Run example task
python3 run_single_task.py \
  --task-image ghcr.io/theagentcompany/example-image:1.0.0 \
  --task-name example \
  --output-dir ./outputs \
  --max-iterations 50

# Check results
cat outputs/eval_example.json
```

**Output:**
```
======================================================================
Running Task: example
======================================================================
[1/6] Starting container...
✓ Container started successfully
[2/6] Initializing task environment...
✓ Environment initialized
[3/6] Reading task instruction...
✓ Task instruction loaded (1234 chars)
[4/6] Running LangGraph agent...
...
✓ Agent execution completed in 45.2s
  - Iterations: 12
  - Completed steps: 8
  - Trajectory steps: 25
[5/6] Saving trajectory...
✓ Trajectory saved
[6/6] Running evaluation...
✓ Evaluation completed

======================================================================
RESULTS
======================================================================
Task: example
Score: 4/5 (80.0%)
...
```

### Run Subset of Tasks

Test on a small subset before full evaluation:

```bash
# Create subset task list
head -10 tasks.txt > tasks_subset.txt

# Run on subset
TASK_LIST_FILE=tasks_subset.txt bash run_eval.sh
```

### Run Full Evaluation

Run on all 175 tasks (takes 24-48 hours):

```bash
# Load environment
source .env

# Run all tasks
bash run_eval.sh

# Or with custom settings
OUTPUTS_PATH=./outputs_full \
MAX_ITERATIONS=150 \
bash run_eval.sh
```

**Features:**
- Progress tracking with colored output
- Automatic retry on failures
- Logging to `outputs/evaluation_log.txt`
- Result aggregation at the end
- Graceful error handling

### Resume from Specific Task

If evaluation stops midway:

```bash
# Resume from task 50
START_FROM=50 bash run_eval.sh

# Run tasks 50-100
START_FROM=50 END_AT=100 bash run_eval.sh
```

### Analyze Results

After evaluation completes:

```bash
# Generate summary statistics
python3 aggregate_results.py ./outputs

# View CSV results
cat outputs/results_summary.csv

# View JSON results
cat outputs/results_summary.json | jq
```

**Output:**
```
======================================================================
OVERALL RESULTS
======================================================================
Total tasks:        175
Total score:        450/875 (51.4%)
Average score:      51.43%
Perfect scores:     25 (14.3%)
Partial scores:     89 (50.9%)
Zero scores:        61 (34.9%)

======================================================================
CATEGORY BREAKDOWN
======================================================================
Category         Count    Avg Score    Perfect
----------------------------------------------------------------------
admin            15       62.3%        3/15
ds               14       48.1%        2/14
finance          12       55.6%        3/12
hr               23       45.2%        4/23
ml               8        38.9%        1/8
pm               18       52.7%        3/18
sde              85       51.0%        9/85
...
```

## File Structure

```
evaluation_langgraph/
├── README.md                  # This file
├── setup.sh                   # Setup script
├── .env.example               # Environment template
├── config.toml.example        # Config template
├── tasks.txt                  # All 175 task images
├── run_single_task.py         # Single task runner
├── run_eval.sh                # Batch evaluation script
├── aggregate_results.py       # Result analysis
└── outputs/                   # Output directory
    ├── traj_*.json            # Trajectories
    ├── eval_*.json            # Evaluations
    ├── results_summary.csv    # CSV summary
    ├── results_summary.json   # JSON summary
    └── evaluation_log.txt     # Execution log
```

## Troubleshooting

### vLLM Connection Issues

```bash
# Test vLLM connection
curl http://localhost:8000/v1/models

# Check vLLM logs
docker logs vllm-container
```

### Docker Issues

```bash
# Check Docker is running
docker ps

# Test container creation
docker run --rm hello-world

# Check disk space
docker system df
```

### Service Connection Issues

```bash
# Verify services are running
curl http://localhost:8929  # GitLab
curl http://localhost:3000  # RocketChat
curl http://localhost:8092  # ownCloud
curl http://localhost:8091  # Plane

# Check service logs
cd ../servers
docker-compose logs
```

### Container Cleanup

If containers are not being cleaned up:

```bash
# List all task containers
docker ps -a | grep tac_

# Stop all task containers
docker ps -a | grep tac_ | awk '{print $1}' | xargs docker stop

# Remove all task containers
docker ps -a | grep tac_ | awk '{print $1}' | xargs docker rm
```

### Debug Failed Task

Keep container for inspection:

```bash
python3 run_single_task.py \
  --task-image ghcr.io/theagentcompany/task-image:1.0.0 \
  --task-name task-name \
  --no-cleanup

# Container will not be removed
# You can then:
docker exec -it <container_name> bash
```

## Performance Tips

### Speed Up Evaluation

1. **Reduce iterations**: For testing, use fewer iterations
   ```bash
   MAX_ITERATIONS=50 bash run_eval.sh
   ```

2. **Disable reflection**: Faster but may reduce quality
   ```bash
   ENABLE_REFLECTION=false bash run_eval.sh
   ```

3. **Use faster model**: Smaller model for quick testing
   ```bash
   LLM_MODEL=Qwen/Qwen2.5-32B-Instruct bash run_eval.sh
   ```

### Improve Quality

1. **Increase iterations**: Allow more steps
   ```bash
   MAX_ITERATIONS=200 bash run_eval.sh
   ```

2. **Enable reflection**: Better reasoning
   ```bash
   ENABLE_REFLECTION=true REFLECTION_FREQUENCY=3 bash run_eval.sh
   ```

3. **Use better environment LLM**: Higher quality NPCs
   ```bash
   ENV_LLM_MODEL=gpt-4o bash run_eval.sh
   ```

## Advanced Usage

### Custom Task List

Create a custom task list for specific categories:

```bash
# SDE tasks only
grep "sde-" tasks.txt > tasks_sde.txt
TASK_LIST_FILE=tasks_sde.txt bash run_eval.sh

# Conversational tasks
grep -E "(hr-|admin-)" tasks.txt > tasks_conversational.txt
TASK_LIST_FILE=tasks_conversational.txt bash run_eval.sh
```

### Parallel Execution

Run multiple evaluations in parallel (requires multiple GPU servers):

```bash
# Terminal 1: Run first half
START_FROM=1 END_AT=87 bash run_eval.sh

# Terminal 2: Run second half
START_FROM=88 END_AT=175 bash run_eval.sh
```

### Compare Results

Compare different configurations:

```bash
# Baseline run
OUTPUTS_PATH=./outputs_baseline bash run_eval.sh

# With more iterations
OUTPUTS_PATH=./outputs_more_iters \
MAX_ITERATIONS=200 \
bash run_eval.sh

# Compare
python3 aggregate_results.py ./outputs_baseline > baseline.txt
python3 aggregate_results.py ./outputs_more_iters > more_iters.txt
diff baseline.txt more_iters.txt
```

## Cost Estimation

### Using vLLM (Local)

- **Infrastructure**: $2-5/hour (GPU server)
- **Full evaluation**: ~$50-150 (24-48 hours)
- **Per task**: ~$0.30-$0.85

### Using Cloud APIs

- **OpenAI GPT-4o**: ~$3000 per full run
- **Anthropic Claude-3.5**: ~$3500 per full run

**Savings with vLLM**: 95%+ cost reduction

## Expected Performance

Based on baseline results:

| Model | Average Score | Perfect Scores | Time per Task |
|-------|--------------|----------------|---------------|
| Qwen2.5-72B + vLLM | 15-20% | 5-10% | ~2-3 min |
| GPT-4o (baseline) | ~20% | ~8% | ~3-4 min |
| Claude-3.5 (baseline) | ~24% | ~10% | ~3-4 min |

## Contributing

To add new features:

1. Test on example task first
2. Document changes in README
3. Update roadmap if architectural changes
4. Run full evaluation to validate

## Support

For issues:
1. Check troubleshooting section above
2. Review main project README
3. Check TheAgentCompany docs: https://the-agent-company.com/
4. Open issue in repository

## License

MIT License - see LICENSE file for details
