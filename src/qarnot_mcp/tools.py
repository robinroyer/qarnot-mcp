"""Tool implementations for Qarnot MCP Server."""

import logging
from typing import Annotated, Any

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from .client import QarnotClient, QarnotAPIError
from .config import LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _mask_token(token: str) -> str:
    """Mask token for logging, showing only first and last 4 chars."""
    if len(token) <= 12:
        return "***"
    return f"{token[:4]}...{token[-4:]}"


def get_api_key_from_context(ctx: Context) -> str:
    """Extract API key from MCP request context.

    The API key can be provided via:
    1. Authorization header as Bearer token
    2. X-Api-Key header directly

    Raises:
        ToolError: If no API key is found
    """
    request_context = getattr(ctx, "request_context", None)
    if request_context:
        headers = getattr(request_context, "headers", {}) or {}

        auth_header = headers.get("authorization") or headers.get("Authorization")
        if auth_header:
            if auth_header.lower().startswith("bearer "):
                token = auth_header[7:].strip()
                logger.info(f"API key extracted from Authorization header: {_mask_token(token)}")
                return token
            return auth_header

        api_key = headers.get("x-api-key") or headers.get("X-Api-Key")
        if api_key:
            logger.info(f"API key extracted from X-Api-Key header: {_mask_token(api_key)}")
            return api_key

    raise ToolError("Authentication required. Please provide an API key via Authorization header.")


async def get_client(ctx: Context) -> QarnotClient:
    """Get a configured Qarnot client from context."""
    api_key = get_api_key_from_context(ctx)
    return QarnotClient(api_key=api_key)


async def list_tasks_impl(
    ctx: Context,
    tags: Annotated[list[str] | None, Field(description="Filter tasks by tags")] = None,
) -> list[dict[str, Any]]:
    """List all compute tasks for the authenticated user.

    Returns a list of tasks with their status, progress, and basic information.
    """
    logger.info(f"Action: list_tasks | Tags: {tags}")

    try:
        client = await get_client(ctx)
        tasks = await client.list_tasks(tags=tags)

        formatted_tasks = []
        for task in tasks:
            formatted_tasks.append({
                "uuid": task.get("uuid"),
                "name": task.get("name"),
                "shortname": task.get("shortname"),
                "state": task.get("state"),
                "progress": task.get("progress"),
                "profile": task.get("profile"),
                "instance_count": task.get("instanceCount"),
                "running_instance_count": task.get("runningInstanceCount"),
                "creation_date": task.get("creationDate"),
                "end_date": task.get("endDate"),
                "tags": task.get("tags"),
            })

        logger.info(f"list_tasks: Found {len(formatted_tasks)} tasks")
        return formatted_tasks

    except QarnotAPIError as e:
        raise ToolError(f"Failed to list tasks: {e.message}")


async def get_task_impl(
    ctx: Context,
    task_uuid: Annotated[str, Field(description="UUID of the task to retrieve")],
) -> dict[str, Any]:
    """Get detailed information about a specific task.

    Returns full task details including status, configuration, and execution information.
    """
    logger.info(f"Action: get_task | Task UUID: {task_uuid}")

    try:
        client = await get_client(ctx)
        task = await client.get_task(task_uuid)

        logger.info(f"get_task: Retrieved task '{task.get('name')}' with state '{task.get('state')}'")
        return task

    except QarnotAPIError as e:
        if e.status_code == 404:
            raise ToolError(f"Task not found: {task_uuid}")
        raise ToolError(f"Failed to get task: {e.message}")


async def submit_task_impl(
    ctx: Context,
    name: Annotated[str, Field(description="Name of the task (required)")],
    profile: Annotated[str | None, Field(description="Computation profile (e.g., 'docker-batch')")] = None,
    instance_count: Annotated[int | None, Field(description="Number of parallel instances", ge=1)] = None,
    shortname: Annotated[str | None, Field(description="Short identifier for the task")] = None,
    resource_buckets: Annotated[list[str] | None, Field(description="Input bucket names")] = None,
    result_bucket: Annotated[str | None, Field(description="Output bucket name")] = None,
    constants: Annotated[list[dict[str, str]] | None, Field(description="List of {key, value} constants")] = None,
    tags: Annotated[list[str] | None, Field(description="Tags for organization")] = None,
) -> dict[str, Any]:
    """Submit a new compute task to Qarnot.

    Creates and starts a new computation task with the specified configuration.
    Returns the created task details including its UUID.
    """
    logger.info(f"Action: submit_task | Name: {name} | Profile: {profile}")

    try:
        client = await get_client(ctx)

        task_config: dict[str, Any] = {"name": name}

        if shortname:
            task_config["shortname"] = shortname
        if profile:
            task_config["profile"] = profile
        if instance_count:
            task_config["instanceCount"] = instance_count
        if resource_buckets:
            task_config["resourceBuckets"] = resource_buckets
        if result_bucket:
            task_config["resultBucket"] = result_bucket
        if constants:
            task_config["constants"] = constants
        if tags:
            task_config["tags"] = tags

        result = await client.create_task(task_config)

        logger.info(f"submit_task: Created task with UUID '{result.get('uuid')}'")
        return result

    except QarnotAPIError as e:
        raise ToolError(f"Failed to submit task: {e.message}")


async def get_task_logs_impl(
    ctx: Context,
    task_uuid: Annotated[str, Field(description="UUID of the task")],
    log_type: Annotated[str, Field(description="Type of log: 'stdout' or 'stderr'")] = "stdout",
    instance_id: Annotated[int | None, Field(description="Specific instance ID (optional)")] = None,
) -> str:
    """Get stdout or stderr logs from a task.

    Retrieves the output logs from a running or completed task.
    Can optionally filter by specific instance ID.
    """
    logger.info(f"Action: get_task_logs | Task: {task_uuid} | Type: {log_type} | Instance: {instance_id}")

    if log_type not in ("stdout", "stderr"):
        raise ToolError("log_type must be 'stdout' or 'stderr'")

    try:
        client = await get_client(ctx)

        if log_type == "stdout":
            logs = await client.get_task_stdout(task_uuid, instance_id)
        else:
            logs = await client.get_task_stderr(task_uuid, instance_id)

        logger.info(f"get_task_logs: Retrieved {len(logs) if logs else 0} chars of {log_type}")
        return logs if logs else f"No {log_type} output available"

    except QarnotAPIError as e:
        if e.status_code == 404:
            raise ToolError(f"Task or instance not found: {task_uuid}")
        raise ToolError(f"Failed to get logs: {e.message}")


async def abort_task_impl(
    ctx: Context,
    task_uuid: Annotated[str, Field(description="UUID of the task to abort")],
) -> dict[str, str]:
    """Abort a running task.

    Stops a task that is currently executing. The task state will change to 'Cancelled'.
    """
    logger.info(f"Action: abort_task | Task UUID: {task_uuid}")

    try:
        client = await get_client(ctx)
        await client.abort_task(task_uuid)

        logger.info(f"abort_task: Successfully aborted task '{task_uuid}'")
        return {"status": "success", "message": f"Task {task_uuid} has been aborted"}

    except QarnotAPIError as e:
        if e.status_code == 404:
            raise ToolError(f"Task not found: {task_uuid}")
        if e.status_code == 403:
            raise ToolError(f"Cannot abort task (may already be completed): {task_uuid}")
        raise ToolError(f"Failed to abort task: {e.message}")


async def delete_task_impl(
    ctx: Context,
    task_uuid: Annotated[str, Field(description="UUID of the task to delete")],
) -> dict[str, str]:
    """Delete a task.

    Removes a task from the system. If the task is running, it will be aborted first.
    """
    logger.info(f"Action: delete_task | Task UUID: {task_uuid}")

    try:
        client = await get_client(ctx)
        await client.delete_task(task_uuid)

        logger.info(f"delete_task: Successfully deleted task '{task_uuid}'")
        return {"status": "success", "message": f"Task {task_uuid} has been deleted"}

    except QarnotAPIError as e:
        if e.status_code == 404:
            raise ToolError(f"Task not found: {task_uuid}")
        raise ToolError(f"Failed to delete task: {e.message}")


async def list_profiles_impl(ctx: Context) -> list[dict[str, Any]]:
    """List available computation profiles.

    Returns the profiles that can be used when creating tasks.
    Each profile defines a specific computation environment.
    """
    logger.info("Action: list_profiles")

    try:
        client = await get_client(ctx)
        profiles = await client.list_profiles()

        logger.info(f"list_profiles: Found {len(profiles)} profiles")
        return profiles

    except QarnotAPIError as e:
        raise ToolError(f"Failed to list profiles: {e.message}")


async def get_profile_impl(
    ctx: Context,
    profile_name: Annotated[str, Field(description="Name of the profile to retrieve")],
) -> dict[str, Any]:
    """Get details of a specific computation profile.

    Returns detailed information about a profile including its constants and configuration.
    """
    logger.info(f"Action: get_profile | Profile: {profile_name}")

    try:
        client = await get_client(ctx)
        profile = await client.get_profile(profile_name)

        logger.info(f"get_profile: Retrieved profile '{profile_name}'")
        return profile

    except QarnotAPIError as e:
        if e.status_code == 404:
            raise ToolError(f"Profile not found: {profile_name}")
        raise ToolError(f"Failed to get profile: {e.message}")
