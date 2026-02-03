"""Tests for the MCP server tools."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastmcp.exceptions import ToolError

from src.qarnot_mcp.tools import (
    get_api_key_from_context,
    list_tasks_impl as list_tasks,
    get_task_impl as get_task,
    submit_task_impl as submit_task,
    get_task_logs_impl as get_task_logs,
    abort_task_impl as abort_task,
    delete_task_impl as delete_task,
    list_profiles_impl as list_profiles,
    get_profile_impl as get_profile,
)
from src.qarnot_mcp.client import QarnotAPIError


class TestAuthExtraction:
    """Tests for authentication extraction from context."""

    def test_extract_bearer_token(self, mock_context, mock_api_key):
        """Test extracting Bearer token from Authorization header."""
        api_key = get_api_key_from_context(mock_context)
        assert api_key == mock_api_key

    def test_extract_x_api_key_header(self, mock_api_key):
        """Test extracting API key from X-Api-Key header."""
        ctx = MagicMock()
        ctx.request_context = MagicMock()
        ctx.request_context.headers = {"x-api-key": mock_api_key}

        api_key = get_api_key_from_context(ctx)
        assert api_key == mock_api_key

    def test_missing_auth_raises_error(self, mock_context_no_auth):
        """Test that missing authentication raises ToolError."""
        with pytest.raises(ToolError) as exc_info:
            get_api_key_from_context(mock_context_no_auth)
        assert "Authentication required" in str(exc_info.value)


class TestListTasks:
    """Tests for list_tasks tool."""

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_list_tasks_success(self, mock_get_client, mock_context, sample_task_list):
        """Test successful task listing."""
        mock_client = AsyncMock()
        mock_client.list_tasks.return_value = sample_task_list
        mock_get_client.return_value = mock_client

        result = await list_tasks(mock_context)
        assert len(result) == 2
        assert result[0]["uuid"] == "test-uuid-12345"
        assert result[0]["state"] == "Running"

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_list_tasks_with_tags(self, mock_get_client, mock_context, sample_task_list):
        """Test task listing with tag filter."""
        mock_client = AsyncMock()
        mock_client.list_tasks.return_value = [sample_task_list[0]]
        mock_get_client.return_value = mock_client

        result = await list_tasks(mock_context, tags=["test"])
        mock_client.list_tasks.assert_called_once_with(tags=["test"])

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_list_tasks_api_error(self, mock_get_client, mock_context):
        """Test task listing with API error."""
        mock_client = AsyncMock()
        mock_client.list_tasks.side_effect = QarnotAPIError(500, "Internal error")
        mock_get_client.return_value = mock_client

        with pytest.raises(ToolError) as exc_info:
            await list_tasks(mock_context)
        assert "Failed to list tasks" in str(exc_info.value)


class TestGetTask:
    """Tests for get_task tool."""

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_get_task_success(self, mock_get_client, mock_context, sample_task):
        """Test successful task retrieval."""
        mock_client = AsyncMock()
        mock_client.get_task.return_value = sample_task
        mock_get_client.return_value = mock_client

        result = await get_task(mock_context, "test-uuid-12345")
        assert result["uuid"] == "test-uuid-12345"
        mock_client.get_task.assert_called_once_with("test-uuid-12345")

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_get_task_not_found(self, mock_get_client, mock_context):
        """Test task not found error."""
        mock_client = AsyncMock()
        mock_client.get_task.side_effect = QarnotAPIError(404, "Task not found")
        mock_get_client.return_value = mock_client

        with pytest.raises(ToolError) as exc_info:
            await get_task(mock_context, "nonexistent")
        assert "Task not found" in str(exc_info.value)


class TestSubmitTask:
    """Tests for submit_task tool."""

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_submit_task_success(self, mock_get_client, mock_context, sample_task):
        """Test successful task submission."""
        mock_client = AsyncMock()
        mock_client.create_task.return_value = sample_task
        mock_get_client.return_value = mock_client

        result = await submit_task(
            mock_context,
            name="Test Task",
            profile="docker-batch",
            instance_count=4,
        )
        assert result["uuid"] == "test-uuid-12345"
        mock_client.create_task.assert_called_once()

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_submit_task_with_all_options(self, mock_get_client, mock_context, sample_task):
        """Test task submission with all options."""
        mock_client = AsyncMock()
        mock_client.create_task.return_value = sample_task
        mock_get_client.return_value = mock_client

        await submit_task(
            mock_context,
            name="Test Task",
            profile="docker-batch",
            instance_count=4,
            shortname="test",
            resource_buckets=["input"],
            result_bucket="output",
            constants=[{"key": "CMD", "value": "echo hello"}],
            tags=["test"],
        )

        call_args = mock_client.create_task.call_args[0][0]
        assert call_args["name"] == "Test Task"
        assert call_args["profile"] == "docker-batch"
        assert call_args["instanceCount"] == 4
        assert call_args["shortname"] == "test"
        assert call_args["resourceBuckets"] == ["input"]
        assert call_args["resultBucket"] == "output"
        assert call_args["tags"] == ["test"]

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_submit_task_api_error(self, mock_get_client, mock_context):
        """Test task submission with API error."""
        mock_client = AsyncMock()
        mock_client.create_task.side_effect = QarnotAPIError(400, "Invalid configuration")
        mock_get_client.return_value = mock_client

        with pytest.raises(ToolError) as exc_info:
            await submit_task(mock_context, name="Test Task")
        assert "Failed to submit task" in str(exc_info.value)


class TestGetTaskLogs:
    """Tests for get_task_logs tool."""

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_get_stdout(self, mock_get_client, mock_context):
        """Test getting stdout logs."""
        mock_client = AsyncMock()
        mock_client.get_task_stdout.return_value = "Hello from task!"
        mock_get_client.return_value = mock_client

        result = await get_task_logs(mock_context, "test-uuid", "stdout")
        assert result == "Hello from task!"
        mock_client.get_task_stdout.assert_called_once_with("test-uuid", None)

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_get_stderr(self, mock_get_client, mock_context):
        """Test getting stderr logs."""
        mock_client = AsyncMock()
        mock_client.get_task_stderr.return_value = "Error message"
        mock_get_client.return_value = mock_client

        result = await get_task_logs(mock_context, "test-uuid", "stderr")
        assert result == "Error message"

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_get_logs_by_instance(self, mock_get_client, mock_context):
        """Test getting logs for specific instance."""
        mock_client = AsyncMock()
        mock_client.get_task_stdout.return_value = "Instance 0 output"
        mock_get_client.return_value = mock_client

        await get_task_logs(mock_context, "test-uuid", "stdout", instance_id=0)
        mock_client.get_task_stdout.assert_called_once_with("test-uuid", 0)

    async def test_invalid_log_type(self, mock_context):
        """Test invalid log type."""
        with pytest.raises(ToolError) as exc_info:
            await get_task_logs(mock_context, "test-uuid", "invalid")
        assert "must be 'stdout' or 'stderr'" in str(exc_info.value)


class TestAbortTask:
    """Tests for abort_task tool."""

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_abort_task_success(self, mock_get_client, mock_context):
        """Test successful task abort."""
        mock_client = AsyncMock()
        mock_client.abort_task.return_value = None
        mock_get_client.return_value = mock_client

        result = await abort_task(mock_context, "test-uuid")
        assert result["status"] == "success"
        mock_client.abort_task.assert_called_once_with("test-uuid")

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_abort_task_not_found(self, mock_get_client, mock_context):
        """Test aborting non-existent task."""
        mock_client = AsyncMock()
        mock_client.abort_task.side_effect = QarnotAPIError(404, "Task not found")
        mock_get_client.return_value = mock_client

        with pytest.raises(ToolError) as exc_info:
            await abort_task(mock_context, "nonexistent")
        assert "Task not found" in str(exc_info.value)


class TestDeleteTask:
    """Tests for delete_task tool."""

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_delete_task_success(self, mock_get_client, mock_context):
        """Test successful task deletion."""
        mock_client = AsyncMock()
        mock_client.delete_task.return_value = None
        mock_get_client.return_value = mock_client

        result = await delete_task(mock_context, "test-uuid")
        assert result["status"] == "success"


class TestListProfiles:
    """Tests for list_profiles tool."""

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_list_profiles_success(self, mock_get_client, mock_context, sample_profiles):
        """Test successful profile listing."""
        mock_client = AsyncMock()
        mock_client.list_profiles.return_value = sample_profiles
        mock_get_client.return_value = mock_client

        result = await list_profiles(mock_context)
        assert len(result) == 2


class TestGetProfile:
    """Tests for get_profile tool."""

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_get_profile_success(self, mock_get_client, mock_context, sample_profile):
        """Test successful profile retrieval."""
        mock_client = AsyncMock()
        mock_client.get_profile.return_value = sample_profile
        mock_get_client.return_value = mock_client

        result = await get_profile(mock_context, "docker-batch")
        assert result["name"] == "docker-batch"

    @patch("src.qarnot_mcp.tools.get_client")
    async def test_get_profile_not_found(self, mock_get_client, mock_context):
        """Test profile not found error."""
        mock_client = AsyncMock()
        mock_client.get_profile.side_effect = QarnotAPIError(404, "Profile not found")
        mock_get_client.return_value = mock_client

        with pytest.raises(ToolError) as exc_info:
            await get_profile(mock_context, "nonexistent")
        assert "Profile not found" in str(exc_info.value)
