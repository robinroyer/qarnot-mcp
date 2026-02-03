"""FastMCP server for Qarnot Computing API."""

from fastmcp import FastMCP

from .tools import (
    list_tasks_impl,
    get_task_impl,
    submit_task_impl,
    get_task_logs_impl,
    abort_task_impl,
    delete_task_impl,
    list_profiles_impl,
    get_profile_impl,
)

# Initialize FastMCP server
mcp = FastMCP(
    "Qarnot-Manager",
    instructions="""
    Qarnot MCP Server provides tools to manage compute tasks on Qarnot Computing platform.

    Available operations:
    - List tasks: View all your compute tasks
    - Get task details: Get detailed information about a specific task
    - Submit task: Create and submit a new compute task
    - Get logs: Retrieve stdout/stderr from task instances
    - Abort task: Stop a running task
    - Delete task: Remove a task
    - List profiles: View available computation profiles

    Authentication is handled via the API key provided in the request.
    """,
)

# Register tools with friendly names
mcp.tool(name="list_tasks")(list_tasks_impl)
mcp.tool(name="get_task")(get_task_impl)
mcp.tool(name="submit_task")(submit_task_impl)
mcp.tool(name="get_task_logs")(get_task_logs_impl)
mcp.tool(name="abort_task")(abort_task_impl)
mcp.tool(name="delete_task")(delete_task_impl)
mcp.tool(name="list_profiles")(list_profiles_impl)
mcp.tool(name="get_profile")(get_profile_impl)
