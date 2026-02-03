"""Tests for the Qarnot API client."""

import pytest
from pytest_httpx import HTTPXMock

from src.qarnot_mcp.client import QarnotClient, QarnotAPIError


class TestQarnotClient:
    """Tests for QarnotClient."""

    @pytest.fixture
    def client(self, mock_api_key):
        """Create a QarnotClient instance."""
        return QarnotClient(api_key=mock_api_key)

    async def test_list_tasks(self, client, httpx_mock: HTTPXMock, sample_task_list):
        """Test listing tasks."""
        httpx_mock.add_response(
            method="GET",
            url="https://api.qarnot.com/v1/tasks",
            json=sample_task_list,
        )

        tasks = await client.list_tasks()
        assert len(tasks) == 2
        assert tasks[0]["uuid"] == "test-uuid-12345"
        assert tasks[1]["state"] == "Completed"

    async def test_list_tasks_with_tags(self, client, httpx_mock: HTTPXMock, sample_task_list):
        """Test listing tasks with tag filter."""
        httpx_mock.add_response(
            method="GET",
            url="https://api.qarnot.com/v1/tasks?tag=test",
            json=[sample_task_list[0]],
        )

        tasks = await client.list_tasks(tags=["test"])
        assert len(tasks) == 1

    async def test_get_task(self, client, httpx_mock: HTTPXMock, sample_task):
        """Test getting a specific task."""
        httpx_mock.add_response(
            method="GET",
            url="https://api.qarnot.com/v1/tasks/test-uuid-12345",
            json=sample_task,
        )

        task = await client.get_task("test-uuid-12345")
        assert task["uuid"] == "test-uuid-12345"
        assert task["name"] == "Test Task"

    async def test_get_task_not_found(self, client, httpx_mock: HTTPXMock):
        """Test getting a non-existent task."""
        httpx_mock.add_response(
            method="GET",
            url="https://api.qarnot.com/v1/tasks/nonexistent",
            status_code=404,
            json={"message": "Task not found"},
        )

        with pytest.raises(QarnotAPIError) as exc_info:
            await client.get_task("nonexistent")
        assert exc_info.value.status_code == 404

    async def test_create_task(self, client, httpx_mock: HTTPXMock, sample_task):
        """Test creating a new task."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.qarnot.com/v1/tasks",
            json=sample_task,
        )

        task_config = {
            "name": "Test Task",
            "profile": "docker-batch",
            "instanceCount": 4,
        }
        result = await client.create_task(task_config)
        assert result["uuid"] == "test-uuid-12345"

    async def test_abort_task(self, client, httpx_mock: HTTPXMock):
        """Test aborting a task."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.qarnot.com/v1/tasks/test-uuid-12345/abort",
            status_code=200,
            text="",
        )

        await client.abort_task("test-uuid-12345")

    async def test_delete_task(self, client, httpx_mock: HTTPXMock):
        """Test deleting a task."""
        httpx_mock.add_response(
            method="DELETE",
            url="https://api.qarnot.com/v1/tasks/test-uuid-12345",
            status_code=204,
        )

        await client.delete_task("test-uuid-12345")

    async def test_get_task_stdout(self, client, httpx_mock: HTTPXMock):
        """Test getting task stdout."""
        httpx_mock.add_response(
            method="GET",
            url="https://api.qarnot.com/v1/tasks/test-uuid-12345/stdout",
            text="Hello from task!",
            headers={"content-type": "text/plain"},
        )

        logs = await client.get_task_stdout("test-uuid-12345")
        assert logs == "Hello from task!"

    async def test_get_task_stdout_by_instance(self, client, httpx_mock: HTTPXMock):
        """Test getting task stdout for specific instance."""
        httpx_mock.add_response(
            method="GET",
            url="https://api.qarnot.com/v1/tasks/test-uuid-12345/stdout/0",
            text="Instance 0 output",
            headers={"content-type": "text/plain"},
        )

        logs = await client.get_task_stdout("test-uuid-12345", instance_id=0)
        assert logs == "Instance 0 output"

    async def test_get_task_stderr(self, client, httpx_mock: HTTPXMock):
        """Test getting task stderr."""
        httpx_mock.add_response(
            method="GET",
            url="https://api.qarnot.com/v1/tasks/test-uuid-12345/stderr",
            text="Error message",
            headers={"content-type": "text/plain"},
        )

        logs = await client.get_task_stderr("test-uuid-12345")
        assert logs == "Error message"

    async def test_list_profiles(self, client, httpx_mock: HTTPXMock, sample_profiles):
        """Test listing profiles."""
        httpx_mock.add_response(
            method="GET",
            url="https://api.qarnot.com/v1/profiles",
            json=sample_profiles,
        )

        profiles = await client.list_profiles()
        assert len(profiles) == 2
        assert profiles[0]["name"] == "docker-batch"

    async def test_get_profile(self, client, httpx_mock: HTTPXMock, sample_profile):
        """Test getting a specific profile."""
        httpx_mock.add_response(
            method="GET",
            url="https://api.qarnot.com/v1/profiles/docker-batch",
            json=sample_profile,
        )

        profile = await client.get_profile("docker-batch")
        assert profile["name"] == "docker-batch"

    async def test_unauthorized(self, client, httpx_mock: HTTPXMock):
        """Test unauthorized request."""
        httpx_mock.add_response(
            method="GET",
            url="https://api.qarnot.com/v1/tasks",
            status_code=401,
            json={"message": "Unauthorized"},
        )

        with pytest.raises(QarnotAPIError) as exc_info:
            await client.list_tasks()
        assert exc_info.value.status_code == 401
