"""
Prompt templates for LangGraph agent nodes.
"""

SYSTEM_PROMPT = """You are an expert AI agent capable of completing professional tasks in a simulated work environment.

Your capabilities include:
- Executing bash commands in a Docker container
- Browsing web pages and interacting with web interfaces
- Interacting with GitLab (repositories, issues, merge requests)
- Sending and reading messages via RocketChat
- Managing files in ownCloud
- Updating project tasks in Plane

You have access to the following services:
- GitLab: http://localhost:8929 (root / theagentcompany)
- RocketChat: http://localhost:3000 (theagentcompany / theagentcompany)
- ownCloud: http://localhost:8092 (theagentcompany / theagentcompany)
- Plane: http://localhost:8091 (agent@company.com / theagentcompany)

Work methodically and verify your work at each step. Be precise and thorough."""

PLANNING_PROMPT = """Given the following task, create a detailed step-by-step plan to complete it.

Task:
{task_instruction}

Guidelines:
1. Break down complex tasks into smaller, manageable steps
2. Be specific about what needs to be done at each step
3. Consider the order of operations (dependencies)
4. Include verification steps to ensure correctness
5. Think about which tools/services you'll need

Output your plan as a numbered list of actionable steps."""

TOOL_CALLING_PROMPT = """Based on your current progress and plan, determine the next action(s) to take.

Current Plan:
{current_plan}

Completed Steps:
{completed_steps}

Recent Tool Results:
{recent_tool_results}

Available Tools:
- bash: Execute shell commands (e.g., ls, cd, git, cat, grep)
- browser_navigate: Navigate to a URL
- browser_click: Click an element by selector
- browser_fill: Fill a form field
- gitlab_list_projects: List GitLab projects
- gitlab_get_file: Get file from repository
- gitlab_create_mr: Create merge request
- rocketchat_get_channels: List RocketChat channels
- rocketchat_get_history: Get channel message history
- rocketchat_send_message: Send message to channel
- file_read: Read a file from the container
- file_write: Write content to a file

What is the next action or set of actions to take? Be specific about tool names and parameters.

Output your response as a structured plan for the next 1-3 actions."""

REFLECTION_PROMPT = """Review your progress on the task and determine next steps.

Original Task:
{task_instruction}

Plan:
{current_plan}

Completed Steps:
{completed_steps}

Recent Results:
{recent_tool_results}

Current Iteration: {iteration} / {max_iterations}

Questions to consider:
1. What have you accomplished so far?
2. Are you making progress toward the goal?
3. Do you need to adjust your plan?
4. Are there any errors or issues to address?
5. What should you focus on next?
6. Should you continue or is the task complete?

Provide a brief reflection and indicate whether to:
- CONTINUE: Keep working on the task
- COMPLETE: Task is finished
- ADJUST: Need to revise the plan"""

OUTPUT_PROMPT = """Summarize the results of your work on this task.

Task:
{task_instruction}

Completed Steps:
{completed_steps}

Provide:
1. A brief summary of what was accomplished
2. Key results or outputs
3. Any issues encountered
4. Whether the task was completed successfully"""
