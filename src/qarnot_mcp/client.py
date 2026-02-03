"""HTTP client wrapper for Qarnot API calls."""

import logging
from typing import Any

import httpx

from .config import QARNOT_BASE_URL, QARNOT_API_VERSION

logger = logging.getLogger(__name__)


class QarnotAPIError(Exception):
    """Exception raised for Qarnot API errors."""

    def __init__(self, status_code: int, message: str, details: Any = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(f"Qarnot API error ({status_code}): {message}")


class QarnotClient:
    """HTTP client for Qarnot API."""

    def __init__(self, api_key: str, base_url: str | None = None, version: str | None = None):
        self.api_key = api_key
        self.base_url = base_url or QARNOT_BASE_URL
        self.version = version or QARNOT_API_VERSION
        self._client: httpx.AsyncClient | None = None

    @property
    def _base_path(self) -> str:
        return f"{self.base_url}/v{self.version}"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "Content-Type": "application/json",
                    "Authorization": self.api_key,
                },
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | list[dict[str, Any]] | None = None,
    ) -> Any:
        client = await self._get_client()
        url = f"{self._base_path}{path}"

        logger.debug(f"Qarnot API request: {method} {url}")

        response = await client.request(method, url, params=params, json=json)

        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("message", response.text)
            except Exception:
                message = response.text
            raise QarnotAPIError(response.status_code, message)

        if response.status_code == 204:
            return None

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(
        self,
        path: str,
        json: dict[str, Any] | list[dict[str, Any]] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return await self._request("POST", path, params=params, json=json)

    async def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        return await self._request("PUT", path, json=json)

    async def delete(self, path: str) -> Any:
        return await self._request("DELETE", path)

    async def list_tasks(self, tags: list[str] | None = None) -> list[dict[str, Any]]:
        """List all tasks for the authenticated user."""
        params = {"tag": tags} if tags else None
        return await self.get("/tasks", params=params)

    async def get_task(self, task_uuid: str) -> dict[str, Any]:
        """Get a specific task by UUID."""
        return await self.get(f"/tasks/{task_uuid}")

    async def create_task(self, task_config: dict[str, Any]) -> dict[str, Any]:
        """Create a new task."""
        return await self.post("/tasks", json=task_config)

    async def abort_task(self, task_uuid: str) -> None:
        """Abort a running task."""
        await self.post(f"/tasks/{task_uuid}/abort")

    async def delete_task(self, task_uuid: str) -> None:
        """Delete a task."""
        await self.delete(f"/tasks/{task_uuid}")

    async def get_task_stdout(
        self, task_uuid: str, instance_id: int | None = None
    ) -> str:
        """Get stdout logs for a task or specific instance."""
        if instance_id is not None:
            path = f"/tasks/{task_uuid}/stdout/{instance_id}"
        else:
            path = f"/tasks/{task_uuid}/stdout"
        return await self.get(path)

    async def get_task_stderr(
        self, task_uuid: str, instance_id: int | None = None
    ) -> str:
        """Get stderr logs for a task or specific instance."""
        if instance_id is not None:
            path = f"/tasks/{task_uuid}/stderr/{instance_id}"
        else:
            path = f"/tasks/{task_uuid}/stderr"
        return await self.get(path)

    async def list_profiles(self) -> list[dict[str, Any]]:
        """List available computation profiles."""
        return await self.get("/profiles")

    async def get_profile(self, name: str) -> dict[str, Any]:
        """Get details of a specific profile."""
        return await self.get(f"/profiles/{name}")
