from __future__ import annotations

from typing import Any

import httpx

from sql_query_reviewer.models import ResetRequest, SQLReviewAction, SQLReviewState, StepResult


class SQLReviewEnv:
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "SQLReviewEnv":
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def sync(self) -> "SyncSQLReviewEnv":
        return SyncSQLReviewEnv(base_url=self.base_url, timeout=self.timeout)

    async def reset(self, task_id: str | None = None) -> StepResult:
        client = self._require_client()
        response = await client.post("/reset", json=ResetRequest(task_id=task_id).model_dump(exclude_none=True))
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
            raise RuntimeError("Use SQLReviewEnv as an async context manager before calling it.")
        return self._client


class SyncSQLReviewEnv:
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
        response = client.post("/reset", json=ResetRequest(task_id=task_id).model_dump(exclude_none=True))
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
            raise RuntimeError("Use SyncSQLReviewEnv as a context manager before calling it.")
        return self._client

