"""
SQL Query Reviewer — Client
============================
Supports three connection modes:
1. from_docker_image()  — used by hackathon validator
2. Async via SQLReviewEnv(base_url=...)
3. Sync via SyncSQLReviewEnv(base_url=...)
"""

from __future__ import annotations

from typing import Any

import httpx

from sql_query_reviewer.models import (
    ResetRequest,
    SQLReviewAction,
    SQLReviewState,
    StepResult,
)


class SQLReviewEnv:
    """Async client for the SQL Query Reviewer environment."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    # --- Docker image support (hackathon validator) -----------------------

    @classmethod
    async def from_docker_image(cls, image_name: str) -> "SQLReviewEnv":
        """
        Connect to the environment via a Docker image.
        Tries openenv-core's provider first, then falls back to localhost.
        """
        try:
            # Try using openenv-core's built-in Docker provider
            from openenv.core.env_client import EnvClient

            class _Wrapper(EnvClient):
                pass

            env = await _Wrapper.from_docker_image(image_name)
            # Wrap the openenv client so our typed models work
            return _DockerEnvWrapper(env)
        except ImportError:
            pass
        except Exception:
            pass

        # Fallback: assume the Docker container is already running on port 8000
        import subprocess
        import time

        container_id = None
        try:
            result = subprocess.run(
                ["docker", "run", "-d", "-p", "8000:8000", image_name],
                capture_output=True,
                text=True,
                timeout=120,
            )
            container_id = result.stdout.strip()
        except Exception:
            pass

        # Wait for container to be ready
        base_url = "http://localhost:8000"
        for _ in range(30):
            try:
                async with httpx.AsyncClient() as c:
                    r = await c.get(f"{base_url}/health", timeout=2.0)
                    if r.status_code == 200:
                        break
            except Exception:
                pass
            time.sleep(1)

        instance = cls(base_url=base_url)
        instance._container_id = container_id  # type: ignore[attr-defined]
        await instance.__aenter__()
        return instance

    # --- Async context manager --------------------------------------------

    async def __aenter__(self) -> "SQLReviewEnv":
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        # Clean up Docker container if we started one
        container_id = getattr(self, "_container_id", None)
        if container_id:
            try:
                import subprocess
                subprocess.run(["docker", "stop", container_id], capture_output=True, timeout=10)
                subprocess.run(["docker", "rm", container_id], capture_output=True, timeout=10)
            except Exception:
                pass

    def sync(self) -> "SyncSQLReviewEnv":
        return SyncSQLReviewEnv(base_url=self.base_url, timeout=self.timeout)

    # --- API methods ------------------------------------------------------

    async def reset(self, task_id: str | None = None) -> StepResult:
        client = self._require_client()
        body = ResetRequest(task_id=task_id).model_dump(exclude_none=True)
        response = await client.post("/reset", json=body)
        response.raise_for_status()
        return StepResult.model_validate(response.json())

    async def step(self, action: SQLReviewAction) -> StepResult:
        client = self._require_client()
        response = await client.post("/step", json=action.model_dump(exclude_none=True))
        response.raise_for_status()
        return StepResult.model_validate(response.json())

    async def state(self) -> SQLReviewState:
        client = self._require_client()
        response = await client.get("/state")
        response.raise_for_status()
        return SQLReviewState.model_validate(response.json())

    def _require_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Use SQLReviewEnv as an async context manager or call from_docker_image().")
        return self._client


class _DockerEnvWrapper(SQLReviewEnv):
    """Wraps an openenv-core EnvClient to present our typed interface."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self._client = None  # not used — we delegate to inner
        self.base_url = ""

    async def reset(self, task_id: str | None = None) -> StepResult:
        result = await self._inner.reset()
        return StepResult.model_validate(result.model_dump() if hasattr(result, "model_dump") else result)

    async def step(self, action: SQLReviewAction) -> StepResult:
        result = await self._inner.step(action)
        return StepResult.model_validate(result.model_dump() if hasattr(result, "model_dump") else result)

    async def state(self) -> SQLReviewState:
        result = await self._inner.state()
        return SQLReviewState.model_validate(result.model_dump() if hasattr(result, "model_dump") else result)

    async def close(self) -> None:
        try:
            await self._inner.close()
        except Exception:
            pass


class SyncSQLReviewEnv:
    """Synchronous client for local dev and testing."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.Client | None = None

    def __enter__(self) -> "SyncSQLReviewEnv":
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def reset(self, task_id: str | None = None) -> StepResult:
        client = self._require_client()
        body = ResetRequest(task_id=task_id).model_dump(exclude_none=True)
        response = client.post("/reset", json=body)
        response.raise_for_status()
        return StepResult.model_validate(response.json())

    def step(self, action: SQLReviewAction) -> StepResult:
        client = self._require_client()
        response = client.post("/step", json=action.model_dump(exclude_none=True))
        response.raise_for_status()
        return StepResult.model_validate(response.json())

    def state(self) -> SQLReviewState:
        client = self._require_client()
        response = client.get("/state")
        response.raise_for_status()
        return SQLReviewState.model_validate(response.json())

    def _require_client(self) -> httpx.Client:
        if self._client is None:
            raise RuntimeError("Use SyncSQLReviewEnv as a context manager.")
        return self._client
