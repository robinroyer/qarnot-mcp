"""Pytest fixtures for Qarnot MCP tests."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from src.qarnot_mcp.client import QarnotClient


@pytest.fixture
def mock_api_key():
    """Return a mock API key."""
    return "test-api-key-12345"


@pytest.fixture
def mock_context(mock_api_key):
    """Create a mock FastMCP context with auth headers."""
    ctx = MagicMock()
    ctx.request_context = MagicMock()
    ctx.request_context.headers = {
        "authorization": f"Bearer {mock_api_key}"
    }
    return ctx


@pytest.fixture
def mock_context_no_auth():
    """Create a mock FastMCP context without auth headers."""
    ctx = MagicMock()
    ctx.request_context = MagicMock()
    ctx.request_context.headers = {}
    return ctx


@pytest.fixture
def sample_task():
    """Return a sample task response."""
    return {
        "uuid": "test-uuid-12345",
        "name": "Test Task",
        "shortname": "test-task",
        "state": "Running",
        "progress": 50.0,
        "profile": "docker-batch",
        "instanceCount": 4,
        "runningInstanceCount": 2,
        "creationDate": "2025-01-01T00:00:00Z",
        "endDate": None,
        "tags": ["test", "example"],
        "resourceBuckets": ["input-bucket"],
        "resultBucket": "output-bucket",
    }


@pytest.fixture
def sample_task_list(sample_task):
    """Return a list of sample tasks."""
    return [
        sample_task,
        {
            **sample_task,
            "uuid": "test-uuid-67890",
            "name": "Another Task",
            "state": "Completed",
            "progress": 100.0,
        },
    ]


@pytest.fixture
def sample_profile():
    """Return a sample profile response."""
    return {
        "name": "docker-batch",
        "constants": [
            {"key": "DOCKER_CMD", "value": ""},
            {"key": "DOCKER_REPO", "value": ""},
        ],
    }


@pytest.fixture
def sample_profiles(sample_profile):
    """Return a list of sample profiles."""
    return [
        sample_profile,
        {
            "name": "blender",
            "constants": [
                {"key": "BLEND_FILE", "value": ""},
            ],
        },
    ]
