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

BASIC TOOLS:
- bash: Execute shell commands (parameters: command, working_dir)
- file_read: Read file content (parameters: file_path)
- file_write: Write content to file (parameters: file_path, content)

BROWSER TOOLS:
- browser_goto: Navigate to URL (parameters: url, wait_until)
- browser_click: Click element (parameters: selector, timeout)
- browser_type: Type text into element (parameters: selector, text, delay)
- browser_fill: Fill input field, clearing first (parameters: selector, value)
- browser_get_text: Extract text from page/element (parameters: selector)
- browser_get_elements: Get all matching elements (parameters: selector)
- browser_screenshot: Take screenshot (parameters: path, full_page)
- browser_scroll: Scroll page (parameters: direction, amount)
- browser_wait: Wait for milliseconds (parameters: milliseconds)
- browser_back: Navigate back in history
- browser_forward: Navigate forward in history
- browser_refresh: Refresh current page

GITLAB TOOLS (Recommended: use convenience tools):
Convenience (single-call):
- gitlab_get_file_by_name: Get file by project name (parameters: project_name, file_path, ref)
- gitlab_create_issue_by_name: Create issue by project name (parameters: project_name, title, description, labels)

Low-level (for complex workflows):
- gitlab_list_projects: List all projects
- gitlab_get_file: Get file (parameters: project_id, file_path, ref)
- gitlab_create_file: Create file (parameters: project_id, file_path, content, branch, commit_message)
- gitlab_update_file: Update file (parameters: project_id, file_path, content, branch, commit_message)
- gitlab_list_issues: List issues (parameters: project_id, state)
- gitlab_create_issue: Create issue (parameters: project_id, title, description, labels)
- gitlab_update_issue: Update issue (parameters: project_id, issue_iid, title, description, state_event)
- gitlab_list_merge_requests: List MRs (parameters: project_id, state)
- gitlab_create_merge_request: Create MR (parameters: project_id, source_branch, target_branch, title, description)

ROCKETCHAT TOOLS (Recommended: use convenience tools):
Convenience (single-call):
- rocketchat_send_dm_to_user: Send DM by username (parameters: username, text)
- rocketchat_send_to_channel: Send to channel by name (parameters: channel_name, text)
- rocketchat_get_channel_history_by_name: Get history by name (parameters: channel_name, count)

Low-level (for complex workflows):
- rocketchat_list_channels: List all channels
- rocketchat_get_history: Get channel history (parameters: room_id, count)
- rocketchat_send_message: Send message (parameters: room_id, text)
- rocketchat_list_dms: List direct messages
- rocketchat_create_dm: Create DM (parameters: username)

OWNCLOUD TOOLS:
- owncloud_list_folder: List folder contents (parameters: path)
- owncloud_get_file: Download file (parameters: path)
- owncloud_upload_file: Upload file (parameters: local_path, remote_path)
- owncloud_create_folder: Create folder (parameters: path)
- owncloud_delete: Delete file/folder (parameters: path)
- owncloud_create_share: Create share link (parameters: path, password)

PLANE TOOLS (Recommended: use convenience tool):
Convenience (single-call):
- plane_create_issue_by_project_name: Create issue by project name (parameters: project_name, name, description, state_id, priority, assignees, workspace_slug)

Low-level (for complex workflows):
- plane_list_projects: List all projects (parameters: workspace_slug)
- plane_list_issues: List issues (parameters: project_id, workspace_slug, state)
- plane_create_issue: Create issue (parameters: project_id, name, description, workspace_slug, priority)
- plane_update_issue: Update issue (parameters: project_id, issue_id, name, description, state_id, workspace_slug)
- plane_list_states: List issue states (parameters: project_id, workspace_slug)

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
